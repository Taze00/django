import { useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { useStatsStore } from '../../store/statsStore';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

export default function ExerciseProgressChart({ exerciseId }) {
  const { exerciseProgress, fetchExerciseProgress, isLoading } = useStatsStore();

  useEffect(() => {
    if (exerciseId) {
      fetchExerciseProgress(exerciseId, 30);
    }
  }, [exerciseId, fetchExerciseProgress]);

  if (isLoading) {
    return (
      <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-4 border border-slate-700">
        <p className="text-slate-400 text-center">Loading...</p>
      </div>
    );
  }

  if (!exerciseProgress || !exerciseProgress.data_points || exerciseProgress.data_points.length === 0) {
    return (
      <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-4 border border-slate-700">
        <p className="text-slate-400 text-center">No data yet for this exercise</p>
      </div>
    );
  }

  const data = {
    labels: exerciseProgress.data_points.map((d) => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }),
    datasets: [
      {
        label: 'Set 1 + Set 2 Reps',
        data: exerciseProgress.data_points.map((d) => d.total_reps),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { display: false },
      title: { display: false },
      tooltip: {
        backgroundColor: 'rgb(30, 41, 59)',
        titleColor: 'rgb(241, 245, 249)',
        bodyColor: 'rgb(148, 163, 184)',
        borderColor: 'rgb(71, 85, 105)',
        borderWidth: 1,
        padding: 12,
        displayColors: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(71, 85, 105, 0.3)',
          drawBorder: false,
        },
        ticks: {
          color: 'rgb(148, 163, 184)',
          font: {
            size: 12,
          },
        },
      },
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          color: 'rgb(148, 163, 184)',
          font: {
            size: 12,
          },
        },
      },
    },
  };

  return (
    <div className="bg-slate-800 rounded-2xl p-4 mx-4 mb-4 border border-slate-700">
      <div className="mb-4">
        <h3 className="text-white font-bold">
          📈 {exerciseProgress.exercise_name}
        </h3>
        <p className="text-slate-400 text-sm mt-1">
          Current: {exerciseProgress.current_progression}
        </p>
      </div>
      <div style={{ height: '250px', position: 'relative' }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
