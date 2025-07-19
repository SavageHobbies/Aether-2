/**
 * Sync Service for offline/online data synchronization
 */

import StorageService from './StorageService';
import ApiService from './ApiService';

interface SyncOperation {
  id: string;
  type: 'idea' | 'task' | 'conversation';
  operation: 'create' | 'update' | 'delete';
  itemId: string;
  data?: any;
  timestamp: Date;
}

class SyncService {
  private static isSyncing = false;

  static async markForSync(
    type: 'idea' | 'task' | 'conversation',
    itemId: string,
    operation: 'create' | 'update' | 'delete',
    data?: any
  ): Promise<void> {
    try {
      const syncOperation: SyncOperation = {
        id: `${type}_${itemId}_${operation}_${Date.now()}`,
        type,
        operation,
        itemId,
        data,
        timestamp: new Date(),
      };

      await StorageService.addToSyncQueue(syncOperation);
    } catch (error) {
      console.error('Mark for sync error:', error);
      throw error;
    }
  }

  static async syncPendingChanges(): Promise<void> {
    if (this.isSyncing) {
      console.log('Sync already in progress');
      return;
    }

    try {
      this.isSyncing = true;
      console.log('Starting sync of pending changes');

      const syncQueue = await StorageService.getSyncQueue();
      if (syncQueue.length === 0) {
        console.log('No pending changes to sync');
        return;
      }

      console.log(`Syncing ${syncQueue.length} pending operations`);

      // Group operations by type and item
      const groupedOperations = this.groupOperations(syncQueue);

      // Process each group
      for (const [key, operations] of Object.entries(groupedOperations)) {
        try {
          await this.processOperationGroup(operations);
          console.log(`Successfully synced operations for ${key}`);
        } catch (error) {
          console.error(`Failed to sync operations for ${key}:`, error);
          // Continue with other operations
        }
      }

      // Clear sync queue after successful sync
      await StorageService.clearSyncQueue();
      console.log('Sync completed successfully');
    } catch (error) {
      console.error('Sync pending changes error:', error);
      throw error;
    } finally {
      this.isSyncing = false;
    }
  }

  private static groupOperations(operations: SyncOperation[]): Record<string, SyncOperation[]> {
    const grouped: Record<string, SyncOperation[]> = {};

    for (const operation of operations) {
      const key = `${operation.type}_${operation.itemId}`;
      if (!grouped[key]) {
        grouped[key] = [];
      }
      grouped[key].push(operation);
    }

    // Sort operations by timestamp within each group
    for (const key of Object.keys(grouped)) {
      grouped[key].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
    }

    return grouped;
  }

  private static async processOperationGroup(operations: SyncOperation[]): Promise<void> {
    if (operations.length === 0) return;

    const {type, itemId} = operations[0];
    const lastOperation = operations[operations.length - 1];

    try {
      switch (type) {
        case 'idea':
          await this.syncIdea(itemId, lastOperation);
          break;
        case 'task':
          await this.syncTask(itemId, lastOperation);
          break;
        case 'conversation':
          await this.syncConversation(itemId, lastOperation);
          break;
        default:
          console.warn(`Unknown sync type: ${type}`);
      }
    } catch (error) {
      console.error(`Process operation group error for ${type} ${itemId}:`, error);
      throw error;
    }
  }

  private static async syncIdea(itemId: string, operation: SyncOperation): Promise<void> {
    try {
      switch (operation.operation) {
        case 'create':
          const ideas = await StorageService.getIdeas();
          const idea = ideas.find(i => i.id === itemId);
          if (idea) {
            await ApiService.createIdea(idea);
          }
          break;
        case 'update':
          if (operation.data) {
            await ApiService.updateIdea(itemId, operation.data);
          }
          break;
        case 'delete':
          await ApiService.deleteIdea(itemId);
          break;
      }
    } catch (error) {
      console.error(`Sync idea error for ${itemId}:`, error);
      throw error;
    }
  }

  private static async syncTask(itemId: string, operation: SyncOperation): Promise<void> {
    try {
      switch (operation.operation) {
        case 'create':
          const tasks = await StorageService.getTasks();
          const task = tasks.find(t => t.id === itemId);
          if (task) {
            await ApiService.createTask(task);
          }
          break;
        case 'update':
          if (operation.data) {
            await ApiService.updateTask(itemId, operation.data);
          }
          break;
        case 'delete':
          await ApiService.deleteTask(itemId);
          break;
      }
    } catch (error) {
      console.error(`Sync task error for ${itemId}:`, error);
      throw error;
    }
  }

  private static async syncConversation(itemId: string, operation: SyncOperation): Promise<void> {
    try {
      // TODO: Implement conversation sync logic
      console.log(`Syncing conversation ${itemId} with operation ${operation.operation}`);
    } catch (error) {
      console.error(`Sync conversation error for ${itemId}:`, error);
      throw error;
    }
  }

  static async performFullSync(): Promise<void> {
    try {
      console.log('Starting full sync');

      // First sync pending changes
      await this.syncPendingChanges();

      // Then fetch latest data from server
      const [ideas, tasks, conversations] = await Promise.all([
        ApiService.getIdeas(),
        ApiService.getTasks(),
        ApiService.getConversations(),
      ]);

      // Update local storage with server data
      await Promise.all([
        StorageService.saveIdeas(ideas),
        StorageService.saveTasks(tasks),
        StorageService.saveConversations(conversations),
      ]);

      // Update last sync time
      await StorageService.setLastSyncTime(new Date());

      console.log('Full sync completed successfully');
    } catch (error) {
      console.error('Full sync error:', error);
      throw error;
    }
  }

  static async getSyncStatus(): Promise<{
    pendingOperations: number;
    lastSyncTime?: Date;
    isSyncing: boolean;
  }> {
    try {
      const syncQueue = await StorageService.getSyncQueue();
      const lastSyncTime = await StorageService.getLastSyncTime();

      return {
        pendingOperations: syncQueue.length,
        lastSyncTime,
        isSyncing: this.isSyncing,
      };
    } catch (error) {
      console.error('Get sync status error:', error);
      return {
        pendingOperations: 0,
        isSyncing: false,
      };
    }
  }

  static async clearSyncQueue(): Promise<void> {
    try {
      await StorageService.clearSyncQueue();
      console.log('Sync queue cleared');
    } catch (error) {
      console.error('Clear sync queue error:', error);
      throw error;
    }
  }

  static async retryFailedSync(): Promise<void> {
    try {
      console.log('Retrying failed sync operations');
      await this.syncPendingChanges();
    } catch (error) {
      console.error('Retry failed sync error:', error);
      throw error;
    }
  }

  // Conflict resolution for concurrent edits
  static async resolveConflict(
    localItem: any,
    serverItem: any,
    type: 'idea' | 'task'
  ): Promise<any> {
    try {
      // Simple conflict resolution: use the most recently modified item
      const localTimestamp = new Date(localItem.timestamp || localItem.updatedAt);
      const serverTimestamp = new Date(serverItem.timestamp || serverItem.updatedAt);

      if (localTimestamp > serverTimestamp) {
        console.log(`Using local version for ${type} ${localItem.id}`);
        return localItem;
      } else {
        console.log(`Using server version for ${type} ${serverItem.id}`);
        return serverItem;
      }
    } catch (error) {
      console.error('Resolve conflict error:', error);
      // Default to server version in case of error
      return serverItem;
    }
  }
}

export default SyncService;