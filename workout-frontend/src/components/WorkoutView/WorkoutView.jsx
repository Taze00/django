import { useState, useEffect } from 'react'
import { workoutStore } from '../../store/workoutStore'
import ExerciseCard from './ExerciseCard'
import RestTimer from './RestTimer'
import ProgressionModal from './ProgressionModal'

export default function WorkoutView({ onBack }) {
  const activeWorkout = workoutStore((state) => state.activeWorkout)
  const exercises = workoutStore((state) => state.exercises)
  const userProgressions = workoutStore((state) => state.userProgressions)
  const lastPerformances = workoutStore((state) => state.lastPerformances)
  const currentStep = workoutStore((state) => state.currentStep)
  const addSet = workoutStore((state) => state.addSet)
  const completeWorkout = workoutStore((state) => state.completeWorkout)
  const setStep = workoutStore((state) => state.setStep)
  const setWorkoutActive = workoutStore((state) => state.setWorkoutActive)

  const [showRestTimer, setShowRestTimer] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [modalData, setModalData] = useState(null)

  if (!activeWorkout || exercises.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 mb-4">Loading...</p>
        </div>
      </div>
    )
  }

  // Define 6-step workout flow
  const workoutFlow = [
    { exerciseId: 1, exerciseName: 'Push-ups', setNumber: 1 },
    { exerciseId: 2, exerciseName: 'Pull-ups', setNumber: 1 },
    { exerciseId: 1, exerciseName: 'Push-ups', setNumber: 2 },
    { exerciseId: 2, exerciseName: 'Pull-ups', setNumber: 2 },
    { exerciseId: 1, exerciseName: 'Push-ups', setNumber: 3 },
    { exerciseId: 2, exerciseName: 'Pull-ups', setNumber: 3 },
  ]

  const currentFlowItem = workoutFlow[currentStep]
  const currentExercise = exercises.find((e) => e.id === currentFlowItem.exerciseId)

  const handleSetCompleted = async (data = {}) => {
    // Get progression ID for current exercise
    const exerciseProgression = userProgressions[String(currentFlowItem.exerciseId)]
    const progressionId = exerciseProgression?.current_progression_id

    // Add set to backend
    await addSet(
      currentFlowItem.exerciseId,
      currentFlowItem.setNumber,
      progressionId,
      data
    )

    // Check if this is the last step
    if (currentStep === 5) {
      // Complete the workout
      const result = await completeWorkout()
      setModalData(result)
      setShowModal(true)
      // Don't set setWorkoutActive(false) here - let the modal close handler do it
    } else {
      // Show rest timer or move to next step
      const restTime = currentStep >= 3 ? 300 : 180
      setShowRestTimer(true)
      setTimeout(() => {
        setShowRestTimer(false)
        setStep(currentStep + 1)
      }, restTime * 1000)
    }
  }

  const handleRestTimerComplete = () => {
    setShowRestTimer(false)
    setStep(currentStep + 1)
  }

  const handleModalClose = () => {
    setShowModal(false)
    setWorkoutActive(false)
    onBack()
  }

  if (showRestTimer) {
    const restTime = currentStep >= 3 ? 300 : 180
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <RestTimer seconds={restTime} onComplete={handleRestTimerComplete} />
        </div>
      </div>
    )
  }

  if (!currentExercise) {
    return <div className="p-4 text-red-600">Error: Exercise not found</div>
  }

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow sticky top-0 z-40">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Step {currentStep + 1}/6
              </h1>
              <button
                onClick={() => {
                  setWorkoutActive(false)
                  onBack()
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                ← Back
              </button>
            </div>
            {/* Progress bar */}
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / 6) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {currentExercise && (
            <ExerciseCard
              exercise={currentExercise}
              setNumber={currentFlowItem.setNumber}
              currentProgression={userProgressions[String(currentExercise.id)]?.current_progression}
              lastPerformance={lastPerformances[String(currentExercise.id)]}
              onSetCompleted={handleSetCompleted}
            />
          )}
        </div>
      </div>

      {/* Progression Modal */}
      {showModal && (
        <ProgressionModal
          upgrades={modalData?.upgrades}
          downgrades={modalData?.downgrades}
          onClose={handleModalClose}
        />
      )}
    </>
  )
}
