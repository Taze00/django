import { useOfflineSync } from '../../hooks/useOfflineSync';
import client from '../../api/client';

export default function OfflineIndicator() {
  const { isOnline, isSyncing, queueSize, handleSync } = useOfflineSync(client);

  // Don't show anything if online and no queue
  if (isOnline && queueSize === 0) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 px-4 py-3 text-center font-semibold text-sm transition-all z-40 ${
        isOnline
          ? 'bg-green-900/80 text-green-200 border-b border-green-700'
          : 'bg-red-900/80 text-red-200 border-b border-red-700'
      }`}
    >
      <div className="flex items-center justify-between gap-3 max-w-4xl mx-auto">
        <div className="flex items-center gap-2">
          {isOnline ? (
            <>
              <span>✓ Online</span>
              {queueSize > 0 && (
                <span className="text-xs opacity-75">
                  ({queueSize} pending)
                </span>
              )}
            </>
          ) : (
            <>
              <span>⚠ Offline Mode</span>
              <span className="text-xs opacity-75">
                (Changes will sync when online)
              </span>
            </>
          )}
        </div>

        {isOnline && queueSize > 0 && (
          <button
            onClick={handleSync}
            disabled={isSyncing}
            className="px-3 py-1 bg-green-700 hover:bg-green-600 disabled:opacity-50 rounded text-xs font-semibold transition-colors"
          >
            {isSyncing ? 'Syncing...' : 'Sync Now'}
          </button>
        )}
      </div>
    </div>
  );
}
