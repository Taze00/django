import { useEffect, useState } from 'react';

/**
 * Compact offline status indicator
 * Shows online/offline status in the header area
 */
export default function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className="fixed top-0 right-0 left-0 px-4 py-4 z-40 flex items-center justify-end h-auto pointer-events-none">
      <div
        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 pointer-events-auto ${
          isOnline
            ? 'bg-green-900/80 text-green-200 border border-green-700'
            : 'bg-red-900/80 text-red-200 border border-red-700'
        }`}
      >
        <span className={`w-2 h-2 rounded-full animate-pulse ${isOnline ? 'bg-green-400' : 'bg-red-400'}`}></span>
        <span>{isOnline ? 'Online' : 'Offline'}</span>
      </div>
    </div>
  );
}
