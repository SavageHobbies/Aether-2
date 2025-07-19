/**
 * App Initialization Utilities
 */

import {Platform} from 'react-native';
import DeviceInfo from 'react-native-device-info';

import ApiService from '../services/ApiService';
import StorageService from '../services/StorageService';
import NotificationService from '../services/NotificationService';

export const initializeApp = async (): Promise<void> => {
  try {
    console.log('Initializing Aether mobile app...');

    // Initialize core services
    await Promise.all([
      initializeApiService(),
      initializeDeviceInfo(),
      requestPermissions(),
    ]);

    console.log('App initialization completed successfully');
  } catch (error) {
    console.error('App initialization failed:', error);
    throw error;
  }
};

const initializeApiService = async (): Promise<void> => {
  try {
    await ApiService.initialize();
    
    // Test connection to backend
    const isHealthy = await ApiService.healthCheck();
    if (isHealthy) {
      console.log('Backend connection established');
    } else {
      console.warn('Backend connection failed - running in offline mode');
    }
  } catch (error) {
    console.warn('API service initialization failed:', error);
    // Continue in offline mode
  }
};

const initializeDeviceInfo = async (): Promise<void> => {
  try {
    const deviceInfo = {
      deviceId: await DeviceInfo.getUniqueId(),
      deviceName: await DeviceInfo.getDeviceName(),
      systemName: DeviceInfo.getSystemName(),
      systemVersion: DeviceInfo.getSystemVersion(),
      appVersion: DeviceInfo.getVersion(),
      buildNumber: DeviceInfo.getBuildNumber(),
      bundleId: DeviceInfo.getBundleId(),
      isEmulator: await DeviceInfo.isEmulator(),
    };

    console.log('Device info:', deviceInfo);

    // Store device info for analytics/debugging
    await StorageService.setSecureItem('deviceInfo', JSON.stringify(deviceInfo));
  } catch (error) {
    console.error('Device info initialization error:', error);
    // Non-critical, continue
  }
};

const requestPermissions = async (): Promise<void> => {
  try {
    // Request notification permissions
    const notificationPermission = await NotificationService.requestNotificationPermissions();
    console.log('Notification permission granted:', notificationPermission);

    // TODO: Request other permissions as needed
    // - Camera (for future features)
    // - Microphone (for voice input)
    // - Location (for context-aware features)
  } catch (error) {
    console.error('Permission request error:', error);
    // Non-critical, continue
  }
};

export const getAppInfo = async (): Promise<{
  version: string;
  buildNumber: string;
  platform: string;
  deviceInfo: any;
}> => {
  try {
    const deviceInfoStr = await StorageService.getSecureItem('deviceInfo');
    const deviceInfo = deviceInfoStr ? JSON.parse(deviceInfoStr) : {};

    return {
      version: DeviceInfo.getVersion(),
      buildNumber: DeviceInfo.getBuildNumber(),
      platform: Platform.OS,
      deviceInfo,
    };
  } catch (error) {
    console.error('Get app info error:', error);
    return {
      version: 'unknown',
      buildNumber: 'unknown',
      platform: Platform.OS,
      deviceInfo: {},
    };
  }
};

export const checkAppHealth = async (): Promise<{
  storage: boolean;
  api: boolean;
  notifications: boolean;
  overall: boolean;
}> => {
  try {
    const [storageHealth, apiHealth, notificationHealth] = await Promise.all([
      checkStorageHealth(),
      checkApiHealth(),
      checkNotificationHealth(),
    ]);

    const overall = storageHealth && apiHealth && notificationHealth;

    return {
      storage: storageHealth,
      api: apiHealth,
      notifications: notificationHealth,
      overall,
    };
  } catch (error) {
    console.error('App health check error:', error);
    return {
      storage: false,
      api: false,
      notifications: false,
      overall: false,
    };
  }
};

const checkStorageHealth = async (): Promise<boolean> => {
  try {
    // Test storage read/write
    const testKey = 'health_check_test';
    const testValue = Date.now().toString();
    
    await StorageService.setSecureItem(testKey, testValue);
    const retrievedValue = await StorageService.getSecureItem(testKey);
    await StorageService.removeSecureItem(testKey);
    
    return retrievedValue === testValue;
  } catch (error) {
    console.error('Storage health check error:', error);
    return false;
  }
};

const checkApiHealth = async (): Promise<boolean> => {
  try {
    return await ApiService.healthCheck();
  } catch (error) {
    console.error('API health check error:', error);
    return false;
  }
};

const checkNotificationHealth = async (): Promise<boolean> => {
  try {
    return await NotificationService.areNotificationsEnabled();
  } catch (error) {
    console.error('Notification health check error:', error);
    return false;
  }
};

export const resetApp = async (): Promise<void> => {
  try {
    console.log('Resetting app data...');
    
    // Clear all local data
    await StorageService.clearAllData();
    
    // Cancel all notifications
    NotificationService.cancelAllNotifications();
    
    console.log('App reset completed');
  } catch (error) {
    console.error('App reset error:', error);
    throw error;
  }
};