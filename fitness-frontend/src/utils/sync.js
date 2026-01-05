/**
 * Offline Sync System
 * Queues API requests when offline and syncs them when online
 */

const QUEUE_STORAGE_KEY = 'fitness_offline_queue';
const LAST_SYNC_KEY = 'fitness_last_sync';

export class OfflineQueue {
  /**
   * Add a request to the offline queue
   * @param {Object} item - {method, url, data, type}
   */
  static addToQueue(item) {
    const queue = this.getQueue();
    queue.push({
      ...item,
      timestamp: new Date().toISOString(),
      id: Date.now() // Unique ID for tracking
    });
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(queue));
    console.log('[OfflineQueue] Added item:', item.type, 'Queue size:', queue.length);
  }

  /**
   * Get the current offline queue
   * @returns {Array}
   */
  static getQueue() {
    const queue = localStorage.getItem(QUEUE_STORAGE_KEY);
    return queue ? JSON.parse(queue) : [];
  }

  /**
   * Remove item from queue by ID
   * @param {number} itemId
   */
  static removeFromQueue(itemId) {
    const queue = this.getQueue();
    const filtered = queue.filter(item => item.id !== itemId);
    localStorage.setItem(QUEUE_STORAGE_KEY, JSON.stringify(filtered));
    console.log('[OfflineQueue] Removed item:', itemId, 'Queue size:', filtered.length);
  }

  /**
   * Clear the entire queue
   */
  static clearQueue() {
    localStorage.removeItem(QUEUE_STORAGE_KEY);
    console.log('[OfflineQueue] Queue cleared');
  }

  /**
   * Get queue size
   * @returns {number}
   */
  static getQueueSize() {
    return this.getQueue().length;
  }

  /**
   * Set last sync timestamp
   */
  static setLastSync() {
    localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
  }

  /**
   * Get last sync timestamp
   * @returns {string}
   */
  static getLastSync() {
    return localStorage.getItem(LAST_SYNC_KEY);
  }
}

/**
 * Sync the offline queue with the API
 * @param {Function} apiClient - Axios instance for API calls
 * @returns {Promise<{success: number, failed: number}>}
 */
export async function syncOfflineQueue(apiClient) {
  const queue = OfflineQueue.getQueue();

  if (queue.length === 0) {
    console.log('[OfflineSync] Queue is empty, nothing to sync');
    return { success: 0, failed: 0 };
  }

  console.log('[OfflineSync] Starting sync, queue size:', queue.length);

  let success = 0;
  let failed = 0;

  for (const item of queue) {
    try {
      console.log(`[OfflineSync] Syncing ${item.type}:`, item.url);

      // Make the API request
      const response = await apiClient({
        method: item.method,
        url: item.url,
        data: item.data,
        timeout: 10000
      });

      // Success - remove from queue
      OfflineQueue.removeFromQueue(item.id);
      success++;
      console.log(`[OfflineSync] ✓ ${item.type} synced successfully`);
    } catch (error) {
      // Failed - keep in queue for next sync
      failed++;
      console.error(`[OfflineSync] ✗ Failed to sync ${item.type}:`, error.message);
    }
  }

  if (success > 0) {
    OfflineQueue.setLastSync();
  }

  console.log(`[OfflineSync] Sync complete: ${success} success, ${failed} failed`);
  return { success, failed };
}
