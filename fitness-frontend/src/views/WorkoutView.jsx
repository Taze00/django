import { useState, useEffect } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';
import { useNavigate } from 'react-router-dom';
import SetInput from '../components/SetInput';
import TimerInput from '../components/TimerInput';
import RestTimer from '../components/RestTimer';
import DropSetInstructions from '../components/DropSetInstructions';
import WarmupChecklist from '../components/WarmupChecklist';
import ProgressionModal from '../components/ProgressionModal';

const WORKOUT_STEPS = [
  { exercise: 'Push-ups', setNumber: 1, type: 'set' },
  { exercise: 'Planks', setNumber: 1, type: 'set' },
  { exercise: 'Pull-ups', setNumber: 1, type: 'set' },
  { exercise: 'Push-ups', setNumber: 2, type: 'set' },
  { exercise: 'Planks', setNumber: 2, type: 'set' },
  { exercise: 'Pull-ups', setNumber: 2, type: 'set' },
  { exercise: 'Push-ups', setNumber: 3, type: 'drop' },
  { exercise: 'Planks', setNumber: 3, type: 'drop' },
  { exercise: 'Pull-ups', setNumber: 3, type: 'drop' },
];

const REST_TIMES = {
  normal: 120,
  afterDrop: 300,
};

export default function WorkoutView() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isResting, setIsResting] = useState(false);
  const [currentWorkout, setCurrentWorkout] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [progressionData, setProgressionData] = useState(null);
  const [isWarmupComplete, setIsWarmupComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const isInitialized = useWorkoutStore(state => state.isInitialized);
  const lastPerformance = useWorkoutStore(state => state.lastPerformance);
  const getCurrentWorkout = useWorkoutStore(state => state.getCurrentWorkout);
  const addSet = useWorkoutStore(state => state.addSet);
  const completeWorkout = useWorkoutStore(state => state.completeWorkout);
  const getLastPerformance = useWorkoutStore(state => state.getLastPerformance);

  useEffect(() => {
    if (isInitialized && exercises.length > 0) {
      initializeWorkout();
    }
  }, [isInitialized, exercises.length]);

  const initializeWorkout = async () => {
    try {
      const workout = await getCurrentWorkout();
      setCurrentWorkout(workout);
      try {
        await getLastPerformance();
      } catch (e) {
        console.warn('Could not fetch last performance:', e);
      }
      setIsLoading(false);
    } catch (error) {
      console.error('Error starting workout:', error);
      setIsLoading(false);
    }
  };

  const getLastTime = (exerciseName, setNumber) => {
    const perf = lastPerformance?.[exerciseName];
    if (!perf) return null;
    return perf[`set${setNumber}`] ?? null;
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
      console.warn(`User progression not found for exercise: ${exerciseName}`);
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

  const getNextExerciseLabel = (nextStep) => {
    if (nextStep.type === 'drop') {
      const shortName = nextStep.exercise.replace('-ups', '');
      return `DROP-SET ${shortName}`;
    }
    const progInfo = getProgressionInfo(nextStep.exercise, nextStep.setNumber, false);
    return progInfo?.currentProgression?.name || nextStep.exercise;
  };

  const handleSetComplete = async (valueOrDropSetCompleted = null) => {
    setIsLoading(true);
    try {
      const step = WORKOUT_STEPS[currentStep];
      const isDropSet = step.type === 'drop';
      const dropSetCompleted = isDropSet && valueOrDropSetCompleted !== false;
      const value = !isDropSet ? valueOrDropSetCompleted : null;
      
      const progInfo = getProgressionInfo(step.exercise, step.setNumber, isDropSet);
      
      if (!progInfo) {
        console.error('Cannot save set: progInfo is null');
        return;
      }

      const reps = progInfo.currentProgression.target_type === 'reps' || step.exercise === 'Planks' ? value : null;
      const seconds = progInfo.currentProgression.target_type === 'time' ? value : null;
      const restTime = isDropSet ? REST_TIMES.afterDrop : REST_TIMES.normal;

      await addSet(
        currentWorkout.id,
        progInfo.exercise.id,
        progInfo.currentProgression.id,
        step.setNumber,
        reps,
        seconds,
        restTime,
        isDropSet,
        dropSetCompleted
      );

      if (currentStep === WORKOUT_STEPS.length - 1) {
        const result = await completeWorkout(currentWorkout.id);
        setProgressionData(result);
        setShowModal(true);
      } else {
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
    navigate('/');
  };

  const handleExitWorkout = () => {
    if (window.confirm('Exit workout? Your progress will not be saved.')) {
      navigate('/');
    }
  };

  const handleWarmupComplete = async (warmupData) => {
    setIsWarmupComplete(true);
    // Optional: save warmup to backend
    // await updateWarmup(currentWorkout.id, warmupData);
  };

  if (isLoading || !isInitialized || exercises.length === 0 || !currentWorkout) {
    return (
      <div className="workout-loading">
        <p>Loading workout...</p>
      </div>
    );
  }

  if (!isWarmupComplete) {
    return (
      <WarmupChecklist onComplete={handleWarmupComplete} />
    );
  }

  if (showModal && progressionData) {
    const hasChanges = progressionData.upgrades?.length > 0 || progressionData.downgrades?.length > 0;
    
    if (!hasChanges) {
      return (
        <div className="workout-complete">
          <div className="workout-complete-card">
            <div className="workout-complete-emoji">🎉</div>
            <h1 className="workout-complete-title">Workout Complete!</h1>
            <p className="workout-complete-subtitle">Great effort! You're building strength every day.</p>
            <button className="workout-complete-btn" onClick={handleModalClose}>Back to Home</button>
          </div>
        </div>
      );
    }
    
    return (
      <ProgressionModal
        upgrades={progressionData.upgrades || []}
        downgrades={progressionData.downgrades || []}
        onClose={handleModalClose}
      />
    );
  }

  if (isResting && currentStep < WORKOUT_STEPS.length - 1) {
    const currentStepInfo = WORKOUT_STEPS[currentStep];
    const nextStepInfo = WORKOUT_STEPS[currentStep + 1];
    const restTime = currentStepInfo.type === 'drop' ? REST_TIMES.afterDrop : REST_TIMES.normal;
    
    return (
      <RestTimer
        seconds={restTime}
        nextExercise={getNextExerciseLabel(nextStepInfo)}
        setNumber={nextStepInfo.setNumber}
        onComplete={handleRestComplete}
      />
    );
  }

  const step = WORKOUT_STEPS[currentStep];
  const progInfo = getProgressionInfo(step.exercise, step.setNumber, step.type === "drop" && dropSetCompleted);

  if (!progInfo) {
    return (
      <div className="workout-error">
        <div className="error-content">
          <p className="error-title">Error loading exercise data</p>
          <p className="error-detail">Exercise: {step.exercise}</p>
          <p className="error-detail">Check console for details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="workout-main">
      <header className="workout-header">
        <button 
          className="btn-exit-workout"
          onClick={handleExitWorkout}
          title="Exit workout"
        >
          ✕
        </button>
        <div className="workout-header-content">
          <div className="workout-header-info">
            <p className="workout-step">Step {currentStep + 1} of {WORKOUT_STEPS.length}</p>
            <p className="workout-current">
              {step.type === "drop" && dropSetCompleted ? '🔥 ' : ''}{step.exercise} Set {step.setNumber}
            </p>
          </div>
          <div className="workout-progress-bar">
            <div
              className="workout-progress-fill"
              style={{ width: `${((currentStep + 1) / WORKOUT_STEPS.length) * 100}%` }}
            />
          </div>
        </div>
      </header>

      <main className="workout-content">
        {step.type === "drop" && dropSetCompleted ? (
          <DropSetInstructions
            exercise={progInfo.exercise}
            progressions={[progInfo.currentProgression].concat(progInfo.nextProgressions.reverse())}
            onComplete={(completed) => handleSetComplete(completed)}
          />
        ) : progInfo.currentProgression.target_type === 'reps' || step.exercise === 'Planks' ? (
          <SetInput
            setNumber={step.setNumber}
            exerciseName={step.exercise}
            progressionName={progInfo.currentProgression.name}
            lastTime={getLastTime(step.exercise, step.setNumber)}
            onComplete={handleSetComplete}
          />
        ) : (
          <TimerInput
            setNumber={step.setNumber}
            exerciseName={step.exercise}
            progressionName={progInfo.currentProgression.name}
            targetSeconds={progInfo.currentProgression.target_value}
            lastTime={getLastTime(step.exercise, step.setNumber)}
            onComplete={handleSetComplete}
          />
        )}
      </main>
    </div>
  );
}
