import { useEffect, useState, useCallback } from 'react';
import { syncOfflineQueue, OfflineQueue } from '../utils/sync';
import { useAuthStore } from '../store/authStore';

/**
 * Hook to handle offline sync
 * - Detects online/offline status
 * - Auto-syncs queue when coming online
 * - Provides offline indicator state
 */
export function useOfflineSync(apiClient) {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [queueSize, setQueueSize] = useState(OfflineQueue.getQueueSize());
  const { isAuthenticated } = useAuthStore();

  // Update queue size
  const updateQueueSize = useCallback(() => {
    setQueueSize(OfflineQueue.getQueueSize());
  }, []);

  // Handle sync
  const handleSync = useCallback(async () => {
    if (!apiClient || !isAuthenticated) {
      console.log('[useOfflineSync] Skipping sync: no apiClient or not authenticated');
      return;
    }

    setIsSyncing(true);
    try {
      const result = await syncOfflineQueue(apiClient);
      updateQueueSize();

      // Show notification if there were items synced
      if (result.success > 0) {
        console.log(`[useOfflineSync] ✓ Synced ${result.success} items`);
      }
      if (result.failed > 0) {
        console.warn(`[useOfflineSync] ✗ Failed to sync ${result.failed} items`);
      }
    } catch (error) {
      console.error('[useOfflineSync] Sync error:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [apiClient, isAuthenticated, updateQueueSize]);

  // Detect online/offline changes
  useEffect(() => {
    const handleOnline = () => {
      console.log('[useOfflineSync] ✓ Back online');
      setIsOnline(true);
      // Auto-sync when coming online
      setTimeout(() => handleSync(), 500);
    };

    const handleOffline = () => {
      console.log('[useOfflineSync] ✗ Going offline');
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleSync]);

  // Update queue size when items are added
  useEffect(() => {
    const handleStorageChange = () => {
      updateQueueSize();
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [updateQueueSize]);

  return {
    isOnline,
    isSyncing,
    queueSize,
    handleSync // Allow manual sync trigger
  };
}
