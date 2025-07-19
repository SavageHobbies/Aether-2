/**
 * Push Notification Service
 */

import PushNotification, {Importance} from 'react-native-push-notification';
import PushNotificationIOS from '@react-native-community/push-notification-ios';
import {Platform, Alert} from 'react-native';
import {check, request, PERMISSIONS, RESULTS} from 'react-native-permissions';

interface NotificationData {
  id: string;
  title: string;
  message: string;
  data?: any;
  scheduledDate?: Date;
  repeatType?: 'day' | 'week' | 'month';
}

class NotificationService {
  private static isInitialized = false;

  static async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      await this.requestPermissions();
      this.configurePushNotifications();
      this.isInitialized = true;
      console.log('Notification service initialized');
    } catch (error) {
      console.error('Notification service initialization error:', error);
      throw error;
    }
  }

  private static async requestPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const result = await request(PERMISSIONS.IOS.NOTIFICATION);
        return result === RESULTS.GRANTED;
      } else {
        const result = await request(PERMISSIONS.ANDROID.POST_NOTIFICATIONS);
        return result === RESULTS.GRANTED;
      }
    } catch (error) {
      console.error('Permission request error:', error);
      return false;
    }
  }

  private static configurePushNotifications(): void {
    PushNotification.configure({
      onRegister: (token) => {
        console.log('Push notification token:', token);
        // TODO: Send token to server
      },

      onNotification: (notification) => {
        console.log('Notification received:', notification);
        
        if (notification.userInteraction) {
          // User tapped on notification
          this.handleNotificationTap(notification);
        }

        // Required on iOS only
        if (Platform.OS === 'ios') {
          notification.finish(PushNotificationIOS.FetchResult.NoData);
        }
      },

      onAction: (notification) => {
        console.log('Notification action:', notification);
      },

      onRegistrationError: (err) => {
        console.error('Push notification registration error:', err);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    // Create notification channels for Android
    if (Platform.OS === 'android') {
      this.createNotificationChannels();
    }
  }

  private static createNotificationChannels(): void {
    PushNotification.createChannel(
      {
        channelId: 'default',
        channelName: 'Default',
        channelDescription: 'Default notifications',
        playSound: true,
        soundName: 'default',
        importance: Importance.HIGH,
        vibrate: true,
      },
      (created) => console.log('Default channel created:', created)
    );

    PushNotification.createChannel(
      {
        channelId: 'reminders',
        channelName: 'Reminders',
        channelDescription: 'Task and deadline reminders',
        playSound: true,
        soundName: 'default',
        importance: Importance.HIGH,
        vibrate: true,
      },
      (created) => console.log('Reminders channel created:', created)
    );

    PushNotification.createChannel(
      {
        channelId: 'ideas',
        channelName: 'Ideas',
        channelDescription: 'Idea capture notifications',
        playSound: false,
        importance: Importance.LOW,
        vibrate: false,
      },
      (created) => console.log('Ideas channel created:', created)
    );
  }

  private static handleNotificationTap(notification: any): void {
    try {
      const {data} = notification;
      
      if (data?.type === 'task_reminder') {
        // Navigate to tasks screen
        // TODO: Implement navigation
      } else if (data?.type === 'idea_suggestion') {
        // Navigate to idea capture
        // TODO: Implement navigation
      } else if (data?.type === 'conversation') {
        // Navigate to conversation
        // TODO: Implement navigation
      }
    } catch (error) {
      console.error('Handle notification tap error:', error);
    }
  }

  // Show immediate notification
  static showNotification(data: NotificationData): void {
    try {
      PushNotification.localNotification({
        id: data.id,
        title: data.title,
        message: data.message,
        userInfo: data.data,
        channelId: this.getChannelId(data.data?.type),
        playSound: true,
        soundName: 'default',
        vibrate: true,
      });
    } catch (error) {
      console.error('Show notification error:', error);
    }
  }

  // Schedule notification for later
  static scheduleNotification(data: NotificationData): void {
    if (!data.scheduledDate) {
      throw new Error('Scheduled date is required for scheduled notifications');
    }

    try {
      PushNotification.localNotificationSchedule({
        id: data.id,
        title: data.title,
        message: data.message,
        date: data.scheduledDate,
        userInfo: data.data,
        channelId: this.getChannelId(data.data?.type),
        playSound: true,
        soundName: 'default',
        vibrate: true,
        repeatType: data.repeatType,
      });
    } catch (error) {
      console.error('Schedule notification error:', error);
    }
  }

  // Cancel notification
  static cancelNotification(id: string): void {
    try {
      PushNotification.cancelLocalNotification(id);
    } catch (error) {
      console.error('Cancel notification error:', error);
    }
  }

  // Cancel all notifications
  static cancelAllNotifications(): void {
    try {
      PushNotification.cancelAllLocalNotifications();
    } catch (error) {
      console.error('Cancel all notifications error:', error);
    }
  }

  // Get scheduled notifications
  static getScheduledNotifications(): Promise<any[]> {
    return new Promise((resolve) => {
      PushNotification.getScheduledLocalNotifications((notifications) => {
        resolve(notifications);
      });
    });
  }

  // Set badge number (iOS only)
  static setBadgeNumber(number: number): void {
    if (Platform.OS === 'ios') {
      PushNotificationIOS.setApplicationIconBadgeNumber(number);
    }
  }

  // Clear badge (iOS only)
  static clearBadge(): void {
    if (Platform.OS === 'ios') {
      PushNotificationIOS.setApplicationIconBadgeNumber(0);
    }
  }

  private static getChannelId(type?: string): string {
    switch (type) {
      case 'task_reminder':
      case 'deadline':
        return 'reminders';
      case 'idea_suggestion':
      case 'idea_capture':
        return 'ideas';
      default:
        return 'default';
    }
  }

  // Convenience methods for common notification types
  static showTaskReminder(taskTitle: string, taskId: string): void {
    this.showNotification({
      id: `task_${taskId}`,
      title: 'Task Reminder',
      message: `Don't forget: ${taskTitle}`,
      data: {
        type: 'task_reminder',
        taskId,
      },
    });
  }

  static scheduleTaskDeadline(taskTitle: string, taskId: string, deadline: Date): void {
    // Schedule 1 hour before deadline
    const reminderTime = new Date(deadline.getTime() - 60 * 60 * 1000);
    
    if (reminderTime > new Date()) {
      this.scheduleNotification({
        id: `deadline_${taskId}`,
        title: 'Deadline Approaching',
        message: `${taskTitle} is due in 1 hour`,
        scheduledDate: reminderTime,
        data: {
          type: 'deadline',
          taskId,
        },
      });
    }
  }

  static showIdeaCaptureReminder(): void {
    this.showNotification({
      id: 'idea_capture_reminder',
      title: 'Capture Your Ideas',
      message: 'Have any new ideas to capture?',
      data: {
        type: 'idea_suggestion',
      },
    });
  }

  static showSyncComplete(itemCount: number): void {
    this.showNotification({
      id: 'sync_complete',
      title: 'Sync Complete',
      message: `${itemCount} items synchronized`,
      data: {
        type: 'sync',
      },
    });
  }

  // Check if notifications are enabled
  static async areNotificationsEnabled(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const result = await check(PERMISSIONS.IOS.NOTIFICATION);
        return result === RESULTS.GRANTED;
      } else {
        const result = await check(PERMISSIONS.ANDROID.POST_NOTIFICATIONS);
        return result === RESULTS.GRANTED;
      }
    } catch (error) {
      console.error('Check notification permissions error:', error);
      return false;
    }
  }

  // Request permissions if not granted
  static async requestNotificationPermissions(): Promise<boolean> {
    try {
      const isEnabled = await this.areNotificationsEnabled();
      if (isEnabled) return true;

      return await this.requestPermissions();
    } catch (error) {
      console.error('Request notification permissions error:', error);
      return false;
    }
  }
}

export default NotificationService;