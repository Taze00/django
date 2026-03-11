import { useState, useMemo } from 'react';
import { useWorkoutStore } from '../stores/workoutStore';

export default function StatisticsView() {
  const workouts = useWorkoutStore(state => state.workouts);
  const [expandedDate, setExpandedDate] = useState(null);

  // Helper: format date YYYY-MM-DD to comparable format
  const formatDate = (date) => {
    return date.toISOString().split('T')[0];
  };

  // Get all trained dates (workouts with sets)
  const trainedDates = new Set(
    workouts.filter(w => w.sets && w.sets.length > 0).map(w => w.date)
  );

  // Calculate current streak
  const calculateCurrentStreak = () => {
    let streak = 0;
    const today = new Date();

    for (let i = 0; i < 365; i++) {
      const checkDate = new Date(today);
      checkDate.setDate(checkDate.getDate() - i);
      const dateStr = formatDate(checkDate);

      if (trainedDates.has(dateStr)) {
        streak++;
      } else {
        break;
      }
    }
    return streak;
  };

  // Calculate longest streak
  const calculateLongestStreak = () => {
    let maxStreak = 0;
    let currentStreak = 0;
    const sortedDates = Array.from(trainedDates).sort();

    if (sortedDates.length === 0) return 0;

    let lastDate = null;
    for (const dateStr of sortedDates) {
      const currentDate = new Date(dateStr);
      if (lastDate === null) {
        currentStreak = 1;
      } else {
        const lastDateObj = new Date(lastDate);
        const dayDiff = Math.floor((currentDate - lastDateObj) / (1000 * 60 * 60 * 24));
        if (dayDiff === 1) {
          currentStreak++;
        } else {
          maxStreak = Math.max(maxStreak, currentStreak);
          currentStreak = 1;
        }
      }
      lastDate = dateStr;
    }
    maxStreak = Math.max(maxStreak, currentStreak);
    return maxStreak;
  };

  // Generate heatmap data for last 12 weeks (84 days)
  const generateHeatmapData = () => {
    const data = [];
    const today = new Date();

    for (let i = 83; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = formatDate(date);
      const dayOfWeek = date.getDay(); // 0=Sunday, 1=Monday, etc.

      data.push({
        date: dateStr,
        dayOfWeek: dayOfWeek === 0 ? 6 : dayOfWeek - 1, // Mon=0, Sun=6
        trained: trainedDates.has(dateStr),
        displayDate: date
      });
    }

    return data;
  };

  // Get month labels for heatmap
  const getMonthLabels = () => {
    const today = new Date();
    const labels = [];
    const seen = new Set();

    for (let i = 83; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const monthYear = `${date.getMonth() + 1}/${date.getFullYear()}`;

      if (!seen.has(monthYear)) {
        seen.add(monthYear);
        labels.push({
          monthYear,
          label: date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
        });
      }
    }

    return labels;
  };

  const currentStreak = calculateCurrentStreak();
  const longestStreak = calculateLongestStreak();
  const heatmapData = generateHeatmapData();

  // Get completed workouts sorted by date (newest first)
  // Show all workouts that have sets (whether fully completed or not)
  const completedWorkouts = workouts
    .filter(w => w.sets && w.sets.length > 0)
    .sort((a, b) => new Date(b.date) - new Date(a.date));

  // Helper to format date like "Thursday, March 6"
  const formatWorkoutDate = (dateStr) => {
    const date = new Date(dateStr);
    const day = date.toLocaleDateString('en-US', { weekday: 'long' });
    const month = date.toLocaleDateString('en-US', { month: 'long' });
    const dayNum = date.getDate();
    return `${day}, ${month} ${dayNum}`;
  };

  // Helper to group sets by exercise
  const getSetsGrouped = (workout) => {
    const grouped = {};
    (workout.sets || []).forEach(set => {
      if (!grouped[set.exercise_name]) {
        grouped[set.exercise_name] = [];
      }
      grouped[set.exercise_name].push(set);
    });
    return grouped;
  };

  // Calculate total reps and time
  const stats = useMemo(() => {
    const result = {
      pushReps: 0,
      pullReps: 0,
      plankSeconds: 0,
    };

    workouts.forEach(workout => {
      workout.sets?.forEach(set => {
        if (set.exercise_name === 'Push-ups' && set.reps) {
          result.pushReps += set.reps;
        } else if (set.exercise_name === 'Pull-ups' && set.reps) {
          result.pullReps += set.reps;
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
        {/* Total Stats */}
        <div className="stats-summary">
          <div className="stat-item">
            <p className="stat-label">Push-ups</p>
            <p className="stat-value">{stats.pushReps}</p>
          </div>
          <div className="stat-item">
            <p className="stat-label">Pull-ups</p>
            <p className="stat-value">{stats.pullReps}</p>
          </div>
          <div className="stat-item">
            <p className="stat-label">Core Time</p>
            <p className="stat-value">{Math.floor(stats.plankSeconds / 60)}m</p>
          </div>
        </div>

        {/* Streak Cards */}
        <div className="stats-streak-grid">
          <div className="stats-streak-card">
            <div className="stats-streak-number">{currentStreak}</div>
            <div className="stats-streak-label">Current Streak</div>
          </div>
          <div className="stats-streak-card">
            <div className="stats-streak-number">{longestStreak}</div>
            <div className="stats-streak-label">Longest Streak</div>
          </div>
        </div>

        {/* Workout History Section */}
        {completedWorkouts.length > 0 && (
          <div className="history-section">
            <h2 className="stats-heatmap-title">Workout History</h2>
            {completedWorkouts.map(workout => (
              <div key={workout.id} className="history-card">
                <button
                  className="history-card-header"
                  onClick={() => setExpandedDate(expandedDate === workout.date ? null : workout.date)}
                >
                  <div className="history-card-date-wrapper">
                    <span className="history-card-date">{formatWorkoutDate(workout.date)}</span>
                  </div>
                  <span className="history-card-toggle">
                    {expandedDate === workout.date ? '−' : '+'}
                  </span>
                </button>

                {expandedDate === workout.date && (
                  <div className="history-card-content">
                    {Object.entries(getSetsGrouped(workout)).map(([exerciseName, sets]) => (
                      <div key={exerciseName} className="history-exercise-group">
                        <div className="history-exercise-header">
                          <span className="history-exercise-icon">
                            {exerciseName === 'Push-ups' ? '🚀' : exerciseName === 'Pull-ups' ? '🔥' : '🔳'}
                          </span>
                          <span className="history-exercise-title">{exerciseName}</span>
                        </div>
                        <div className="history-sets-container">
                          {sets.map((set, idx) => (
                            <div key={idx} className={`history-set-item ${set.set_number === 3 && set.is_drop_set ? 'drop-set' : ''}`}>
                              <span className="set-label">
                                {set.set_number === 3 && set.is_drop_set ? 'Drop' : `Set ${set.set_number}`}
                              </span>
                              <span className={`set-value ${set.set_number === 3 && set.is_drop_set ? 'drop-value' : ''}`}>
                                {set.set_number === 3 && set.is_drop_set ? '✓' : (set.reps ? `${set.reps}` : `${set.seconds}s`)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
