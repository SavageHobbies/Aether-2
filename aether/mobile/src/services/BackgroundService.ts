/**
 * Background Service for handling background tasks
 */

import BackgroundJob from 'react-native-background-job';
import BackgroundTask from 'react-native-background-task';
import {Platform, AppState} from 'react-native';

import StorageService from './StorageService';
import SyncService from './SyncService';
import NotificationService from './NotificationService';

class BackgroundService {
  private static isInitialized = false;
  private static backgroundTaskId: number | null = null;
  private static syncInterval: NodeJS.Timeout | null = null;

  static async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.setupBackgroundTasks();
      this.setupPeriodicSync();
      this.isInitialized = true;
      console.log('Background service initialized');
    } catch (error) {
      console.error('Background service initialization error:', error);
      throw error;
    }
  }

  private static setupBackgroundTasks(): void {
    if (Platform.OS === 'ios') {
      this.setupIOSBackgroundTasks();
    } else {
      this.setupAndroidBackgroundTasks();
    }
  }

  private static setupIOSBackgroundTasks(): void {
    BackgroundTask.define(() => {
      console.log('iOS background task started');
      
      // Perform background sync
      this.performBackgroundSync()
        .then(() => {
          console.log('Background sync completed');
        })
        .catch((error) => {
          console.error('Background sync error:', error);
        })
        .finally(() => {
          BackgroundTask.finish();
        });
    });
  }

  private static setupAndroidBackgroundTasks(): void {
    BackgroundJob.register({
      jobKey: 'aetherSync',
      period: 15000, // 15 seconds minimum for Android
    });

    BackgroundJob.on('aetherSync', () => {
      console.log('Android background job started');
      
      this.performBackgroundSync()
        .then(() => {
          console.log('Background sync completed');
        })
        .catch((error) => {
          console.error('Background sync error:', error);
        });
    });
  }

  private static setupPeriodicSync(): void {
    // Set up periodic sync every 5 minutes when app is active
    this.syncInterval = setInterval(async () => {
      if (AppState.currentState === 'active') {
        try {
          await this.performBackgroundSync();
        } catch (error) {
          console.error('Periodic sync error:', error);
        }
      }
    }, 5 * 60 * 1000); // 5 minutes
  }

  private static async performBackgroundSync(): Promise<void> {
    try {
      // Check if we have pending sync operations
      const syncQueue = await StorageService.getSyncQueue();
      
      if (syncQueue.length > 0) {
        console.log(`Syncing ${syncQueue.length} pending operations`);
        await SyncService.syncPendingChanges();
      }

      // Update last background sync time
      await StorageService.setSecureItem('lastBackgroundSync', new Date().toISOString());
    } catch (error) {
      console.error('Background sync error:', error);
      // Don't throw error to prevent background task from failing
    }
  }

  static handleForeground(): void {
    console.log('App came to foreground');
    
    // Stop background tasks
    this.stopBackgroundTasks();
    
    // Trigger immediate sync
    this.performBackgroundSync().catch(error => {
      console.error('Foreground sync error:', error);
    });
  }

  static handleBackground(): void {
    console.log('App went to background');
    
    // Start background tasks
    this.startBackgroundTasks();
    
    // Save current state
    this.saveAppState().catch(error => {
      console.error('Save app state error:', error);
    });
  }

  private static startBackgroundTasks(): void {
    if (Platform.OS === 'ios') {
      BackgroundTask.start({
        taskName: 'AetherSync',
        taskDelay: 30000, // 30 seconds
      });
    } else {
      BackgroundJob.start({
        jobKey: 'aetherSync',
      });
    }
  }

  private static stopBackgroundTasks(): void {
    if (Platform.OS === 'ios') {
      BackgroundTask.stop();
    } else {
      BackgroundJob.stop({
        jobKey: 'aetherSync',
      });
    }
  }

  private static async saveAppState(): Promise<void> {
    try {
      const appState = {
        timestamp: new Date().toISOString(),
        lastActiveTime: new Date().toISOString(),
      };
      
      await StorageService.setSecureItem('appState', JSON.stringify(appState));
    } catch (error) {
      console.error('Save app state error:', error);
    }
  }

  // Schedule idea capture reminders
  static scheduleIdeaCaptureReminders(): void {
    try {
      // Schedule daily reminder at 9 AM
      const reminderTime = new Date();
      reminderTime.setHours(9, 0, 0, 0);
      
      // If it's already past 9 AM today, schedule for tomorrow
      if (reminderTime <= new Date()) {
        reminderTime.setDate(reminderTime.getDate() + 1);
      }

      NotificationService.scheduleNotification({
        id: 'daily_idea_reminder',
        title: 'Daily Idea Check',
        message: 'Any new ideas to capture today?',
        scheduledDate: reminderTime,
        repeatType: 'day',
        data: {
          type: 'idea_suggestion',
        },
      });
    } catch (error) {
      console.error('Schedule idea reminders error:', error);
    }
  }

  // Process pending voice recordings
  static async processPendingVoiceRecordings(): Promise<void> {
    try {
      // TODO: Implement voice recording processing
      // This would handle any voice recordings that were captured
      // but not yet processed due to network issues
      console.log('Processing pending voice recordings');
    } catch (error) {
      console.error('Process voice recordings error:', error);
    }
  }

  // Clean up old data
  static async cleanupOldData(): Promise<void> {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - 30); // 30 days ago

      // TODO: Implement cleanup logic
      // Remove old completed tasks, processed ideas, etc.
      console.log('Cleaning up old data');
    } catch (error) {
      console.error('Cleanup old data error:', error);
    }
  }

  // Get background sync status
  static async getBackgroundSyncStatus(): Promise<{
    lastSync?: Date;
    pendingOperations: number;
    isEnabled: boolean;
  }> {
    try {
      const lastSyncStr = await StorageService.getSecureItem('lastBackgroundSync');
      const syncQueue = await StorageService.getSyncQueue();
      
      return {
        lastSync: lastSyncStr ? new Date(lastSyncStr) : undefined,
        pendingOperations: syncQueue.length,
        isEnabled: this.isInitialized,
      };
    } catch (error) {
      console.error('Get background sync status error:', error);
      return {
        pendingOperations: 0,
        isEnabled: false,
      };
    }
  }

  // Manual background sync trigger
  static async triggerManualSync(): Promise<void> {
    try {
      await this.performBackgroundSync();
      NotificationService.showNotification({
        id: 'manual_sync_complete',
        title: 'Sync Complete',
        message: 'Manual synchronization completed',
        data: {
          type: 'sync',
        },
      });
    } catch (error) {
      console.error('Manual sync error:', error);
      NotificationService.showNotification({
        id: 'manual_sync_error',
        title: 'Sync Failed',
        message: 'Manual synchronization failed',
        data: {
          type: 'error',
        },
      });
      throw error;
    }
  }

  static cleanup(): void {
    try {
      if (this.syncInterval) {
        clearInterval(this.syncInterval);
        this.syncInterval = null;
      }
      
      this.stopBackgroundTasks();
      this.isInitialized = false;
      console.log('Background service cleaned up');
    } catch (error) {
      console.error('Background service cleanup error:', error);
    }
  }
}

export default BackgroundService;