export default function StatsCard({ label, value, icon }) {
  return (
    <div className="bg-slate-800 rounded-2xl p-4 border border-slate-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm font-semibold">{label}</p>
          <p className="text-white text-2xl font-bold mt-2">{value}</p>
        </div>
        {icon && <span className="text-4xl">{icon}</span>}
      </div>
    </div>
  );
}
