export default function ExerciseSelector({ exercises, selected, onSelect }) {
  if (!exercises || exercises.length === 0) {
    return null;
  }

  return (
    <div className="px-4 py-4 border-b border-slate-700">
      <label className="text-slate-400 text-sm font-semibold block mb-2">
        Select Exercise
      </label>
      <select
        value={selected?.id || ''}
        onChange={(e) => {
          const exercise = exercises.find((ex) => ex.id === parseInt(e.target.value));
          onSelect(exercise);
        }}
        className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-blue-500 focus:outline-none"
      >
        <option value="">Choose an exercise...</option>
        {exercises.map((exercise) => (
          <option key={exercise.id} value={exercise.id}>
            {exercise.name}
          </option>
        ))}
      </select>
    </div>
  );
}
