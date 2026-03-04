import { useEffect, useState } from 'react'

export default function RestTimer({ seconds, onComplete }) {
  const [remaining, setRemaining] = useState(seconds)

  useEffect(() => {
    if (remaining <= 0) {
      onComplete()
      return
    }

    const timer = setInterval(() => {
      setRemaining((prev) => prev - 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [remaining, onComplete])

  const minutes = Math.floor(remaining / 60)
  const secs = remaining % 60

  return (
    <div className="text-center space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Rest Timer</h2>
      <div className="bg-blue-600 text-white rounded-lg p-12">
        <div className="text-6xl font-bold font-mono">
          {String(minutes).padStart(2, '0')}:{String(secs).padStart(2, '0')}
        </div>
      </div>
      <button
        onClick={onComplete}
        className="w-full py-3 px-4 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
      >
        Continue Now
      </button>
    </div>
  )
}
