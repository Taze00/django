import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useWorkoutStore } from '../stores/workoutStore';

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function HomeView() {
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const exercises = useWorkoutStore(state => state.exercises);
  const userProgressions = useWorkoutStore(state => state.userProgressions);
  const workouts = useWorkoutStore(state => state.workouts);
  const trainingDays = useWorkoutStore(state => state.trainingDays);
  const isLoading = useWorkoutStore(state => state.isLoading);

  const handleStartWorkout = () => navigate('/workout');

  const getPushProgress = () => {
    const pushExercise = exercises.find(e => e.name === 'Push-ups');
    if (!pushExercise) return null;
    const prog = userProgressions[String(pushExercise.id)];
    return prog ? prog.current_progression : null;
  };

  const getPullProgress = () => {
    const pullExercise = exercises.find(e => e.name === 'Pull-ups');
    if (!pullExercise) return null;
    const prog = userProgressions[String(pullExercise.id)];
    return prog ? prog.current_progression : null;
  };

  const getPlankProgress = () => {
    const plankExercise = exercises.find(e => e.name === 'Planks');
    if (!plankExercise) return null;
    const prog = userProgressions[String(plankExercise.id)];
    return prog ? prog.current_progression : null;
  };

  const pushProg = getPushProgress();
  const pullProg = getPullProgress();
  const plankProg = getPlankProgress();

  // Calculate week status based on actual workouts
  const getWeekStatus = () => {
    const now = new Date();
    const dayIndex = now.getDay(); // 0 = Sunday, 1 = Monday, etc.

    // Get Monday of current week
    const monday = new Date(now);
    monday.setDate(now.getDate() - (dayIndex === 0 ? 6 : dayIndex - 1));
    monday.setHours(0, 0, 0, 0);

    const status = {};
    ALL_DAYS.forEach((day, idx) => {
      status[day] = false;
    });

    workouts.forEach(workout => {
      const workoutDate = new Date(workout.date);
      workoutDate.setHours(0, 0, 0, 0);

      // Check if workout is in current week
      if (workoutDate >= monday) {
        const dayOfWeek = workoutDate.getDay();
        const dayNum = dayOfWeek === 0 ? 7 : dayOfWeek;
        if (dayNum <= 7) {
          const dayName = ALL_DAYS[dayNum - 1];
          status[dayName] = true;
        }
      }
    });

    return status;
  };

  const weekStatus = useMemo(() => getWeekStatus(), [trainingDays, workouts]);

  // Get today's day name for highlighting
  const getTodayDayName = () => {
    const today = new Date();
    const dayIndex = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
    const dayNum = dayIndex === 0 ? 7 : dayIndex;
    return ALL_DAYS[dayNum - 1];
  };

  const todayDayName = useMemo(() => getTodayDayName(), []);

  // Calculate total reps and workout count
  const stats = useMemo(() => {
    const result = {
      pushReps: 0,
      pullReps: 0,
      pullSeconds: 0,
      plankSeconds: 0,
      totalWorkouts: workouts.length
    };

    workouts.forEach(workout => {
      workout.sets?.forEach(set => {
        if (set.exercise_name === 'Push-ups' && set.reps) {
          result.pushReps += set.reps;
        } else if (set.exercise_name === 'Pull-ups') {
          if (set.reps) {
            result.pullReps += set.reps;
          }
          if (set.seconds) {
            result.pullSeconds += set.seconds;
          }
        } else if (set.exercise_name === 'Planks' && set.seconds) {
          result.plankSeconds += set.seconds;
        }
      });
    });

    return result;
  }, [workouts]);

  return (
    <div className="home-container">
      <div className="header">
        <div className="header-content">
          <h1 className="header-title">Calisthenics</h1>
        </div>
      </div>

      <div className="main-content">
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
            <p style={{ color: '#94a3b8' }}>Loading your workouts...</p>
          </div>
        ) : (
          <>
            <div className="week-plan">
              <div className="week-grid-inline">
                {ALL_DAYS.map((day, idx) => {
                  const dayNum = idx + 1;
                  const isTrainingDay = trainingDays.includes(dayNum);
                  const isCompleted = weekStatus[day];
                  const isToday = day === todayDayName;

                  if (isTrainingDay) {
                    return (
                      <div key={day} className={`week-day ${isCompleted ? 'completed' : 'pending'} ${isToday ? 'today' : ''}`}>
                        <p className="week-day-name">{day}</p>
                        <p className="week-day-status">{isCompleted ? '✓' : '○'}</p>
                      </div>
                    );
                  } else {
                    return (
                      <div key={day} className={`week-day rest-day ${isCompleted ? 'trained-on-rest' : ''}`}>
                        <p className="week-day-name">{day}</p>
                        <p className="week-day-status">😴</p>
                      </div>
                    );
                  }
                })}
              </div>
            </div>

            <div className="progression-section">
              <div className="progression-grid-compact">
                <div className="progression-card-compact progression-push">
                  <div className="progression-icon-compact">🚀</div>
                  <p className="progression-title-compact">Push</p>
                  {pushProg ? (
                    <>
                      <p className="progression-name-compact">{pushProg.name}</p>
                      <p className="progression-level-number">Level {pushProg.level}</p>
                    </>
                  ) : (
                    <p className="progression-name-compact">Loading...</p>
                  )}
                </div>

                <div className="progression-card-compact progression-pull">
                  <div className="progression-icon-compact">🔥</div>
                  <p className="progression-title-compact">Pull</p>
                  {pullProg ? (
                    <>
                      <p className="progression-name-compact">{pullProg.name}</p>
                      <p className="progression-level-number">Level {pullProg.level}</p>
                    </>
                  ) : (
                    <p className="progression-name-compact">Loading...</p>
                  )}
                </div>

                <div className="progression-card-compact progression-core">
                  <div className="progression-icon-compact">💪</div>
                  <p className="progression-title-compact">Core</p>
                  {plankProg ? (
                    <>
                      <p className="progression-name-compact">{plankProg.name}</p>
                      <p className="progression-level-number">Level {plankProg.level}</p>
                    </>
                  ) : (
                    <p className="progression-name-compact">Loading...</p>
                  )}
                </div>

                <div className="progression-card-compact progression-cardio">
                  <div className="progression-icon-compact">🏃</div>
                  <p className="progression-title-compact">Cardio</p>
                  <p className="progression-name-compact">Coming Soon</p>
                </div>
              </div>
            </div>

<button className="btn-start-inline" onClick={handleStartWorkout}>
              Start Workout
            </button>
          </>
        )}
      </div>
    </div>
  );
}
