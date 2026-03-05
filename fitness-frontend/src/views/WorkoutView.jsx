import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import SetInput from '../components/SetInput';
import TimerInput from '../components/TimerInput';
import RestTimer from '../components/RestTimer';
import DropSetInstructions from '../components/DropSetInstructions';
import ProgressionModal from '../components/ProgressionModal';

const WORKOUT_STEPS = [
  { exercise: 'Push-ups', setNumber: 1, type: 'set' },
  { exercise: 'Pull-ups', setNumber: 1, type: 'set' },
  { exercise: 'Push-ups', setNumber: 2, type: 'set' },
  { exercise: 'Pull-ups', setNumber: 2, type: 'set' },
  { exercise: 'Push-ups', setNumber: 3, type: 'drop' },
  { exercise: 'Pull-ups', setNumber: 3, type: 'drop' },
];

const REST_TIMES = {
  normal: 180, // 3 min
  afterDrop: 300, // 5 min
};

export default function WorkoutView() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isResting, setIsResting] = useState(false);
  const [currentWorkout, setCurrentWorkout] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [progressionData, setProgressionData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isInitialized = useWorkoutStore(state => state.isInitialized);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const addSet = useWorkoutStore(state => state.addSet);
  const completeWorkout = useWorkoutStore(state => state.completeWorkout);

  useEffect(() => {
    // Wait for exercises to be loaded before initializing workout
    if (isInitialized && exercises.length > 0) {
      initializeWorkout();
    }
  }, [isInitialized, exercises.length]);

  const initializeWorkout = async () => {
    try {
      const workout = await getCurrentWorkout();
      setCurrentWorkout(workout);
      setIsLoading(false);
    } catch (error) {
      console.error('Error starting workout:', error);
      setIsLoading(false);
    }
  };

  const getExerciseById = (name) => {
    return exercises.find(e => e.name === name);
  };

  const getProgressionInfo = (exerciseName, setNumber, isDropSet) => {
    const exercise = getExerciseById(exerciseName);
    if (!exercise) {
      console.warn(`Exercise not found: ${exerciseName}`);
      return null;
    }

    const userProg = userProgressions[String(exercise.id)];
    if (!userProg) {
      console.warn(`User progression not found for exercise: ${exerciseName} (id=${exercise.id})`);
      return null;
    }

    if (!userProg.current_progression) {
      console.warn(`Current progression is null for exercise: ${exerciseName}`);
      return null;
    }

    return {
      exercise,
      userProg,
      currentProgression: userProg.current_progression,
      nextProgressions: exercise.progressions.filter(p => p.level < userProg.current_progression.level),
    };
  };

  const handleSetComplete = async (value) => {
    if (!currentWorkout) return;

    setIsLoading(true);
    try {
      const step = WORKOUT_STEPS[currentStep];
      const progInfo = getProgressionInfo(step.exercise, step.setNumber, step.type === 'drop');

      if (!progInfo) {
        console.error('Could not get progression info for step', step);
        setIsLoading(false);
        return;
      }

      const reps = progInfo.currentProgression.target_type === 'reps' ? value : null;
      const seconds = progInfo.currentProgression.target_type === 'time' ? value : null;

      const restTime = step.type === 'drop' ? REST_TIMES.afterDrop : REST_TIMES.normal;

      await addSet(
        currentWorkout.id,
        progInfo.exercise.id,
        progInfo.currentProgression.id,
        step.setNumber,
        reps,
        seconds,
        restTime,
        step.type === 'drop'
      );

      if (currentStep === WORKOUT_STEPS.length - 1) {
        // Last step - complete workout
        const result = await completeWorkout(currentWorkout.id);
        setProgressionData(result);
        setShowModal(true);
      } else {
        // Show rest timer
        setIsResting(true);
      }
    } catch (error) {
      console.error('Error saving set:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestComplete = () => {
    setIsResting(false);
    setCurrentStep(currentStep + 1);
  };

  const handleModalClose = () => {
    setShowModal(false);
    // Navigate back to home
    window.location.href = '/fitness/';
  };

  if (isLoading || !isInitialized || exercises.length === 0 || !currentWorkout) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <p className="text-slate-300">Loading workout...</p>
      </div>
    );
  }

  if (showModal && progressionData) {
    return (
      <ProgressionModal
        upgrades={progressionData.upgrades || []}
        downgrades={progressionData.downgrades || []}
        onClose={handleModalClose}
      />
    );
  }

  if (isResting && currentStep < WORKOUT_STEPS.length) {
    const currentStepInfo = WORKOUT_STEPS[currentStep];
    const nextStepInfo = WORKOUT_STEPS[currentStep + 1];
    const restTime = currentStepInfo.type === 'drop' ? REST_TIMES.afterDrop : REST_TIMES.normal;
    
    return (
      <RestTimer
        seconds={restTime}
        nextExercise={nextStepInfo.exercise}
        setNumber={nextStepInfo.setNumber}
        onComplete={handleRestComplete}
      />
    );
  }

  const step = WORKOUT_STEPS[currentStep];
  const progInfo = getProgressionInfo(step.exercise, step.setNumber, step.type === 'drop');

  if (!progInfo) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-center">
          <p className="text-red-400 mb-4">Error loading exercise data</p>
          <p className="text-slate-400 text-sm">Exercise: {step.exercise}</p>
          <p className="text-slate-400 text-sm">Exercises loaded: {exercises.length}</p>
          <p className="text-slate-400 text-sm">User progressions: {Object.keys(userProgressions).length}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 pb-40">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-40 p-4">
        <div className="max-w-2xl mx-auto flex justify-between items-center">
          <div>
            <p className="text-slate-400 text-sm">Step {currentStep + 1} of {WORKOUT_STEPS.length}</p>
            <p className="text-slate-100 font-semibold">
              {step.type === 'drop' ? '🔥 ' : ''}{step.exercise} Set {step.setNumber}
            </p>
          </div>
          <div className="w-32 h-1 bg-slate-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all"
              style={{ width: `${((currentStep + 1) / WORKOUT_STEPS.length) * 100}%` }}
            />
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto p-4 mt-6">
        {step.type === 'drop' ? (
          <DropSetInstructions
            exercise={progInfo.exercise}
            progressions={[progInfo.currentProgression].concat(progInfo.nextProgressions.reverse())}
            onComplete={() => handleSetComplete(0)}
          />
        ) : progInfo.currentProgression.target_type === 'reps' ? (
          <SetInput
            setNumber={step.setNumber}
            exerciseName={step.exercise}
            progressionName={progInfo.currentProgression.name}
            onComplete={handleSetComplete}
          />
        ) : (
          <TimerInput
            setNumber={step.setNumber}
            exerciseName={step.exercise}
            progressionName={progInfo.currentProgression.name}
            targetSeconds={progInfo.currentProgression.target_value}
            onComplete={handleSetComplete}
          />
        )}
      </main>
    </div>
  );
}
