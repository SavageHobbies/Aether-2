/**
 * Aether Mobile App Root Component
 */

import React, {useEffect, useState} from 'react';
import {
  StatusBar,
  StyleSheet,
  View,
  Alert,
  AppState,
  AppStateStatus,
} from 'react-native';

import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {SafeAreaProvider} from 'react-native-safe-area-context';

import AppNavigator from './navigation/AppNavigator';
import {AuthProvider} from './contexts/AuthContext';
import {ThemeProvider} from './contexts/ThemeContext';
import {DataProvider} from './contexts/DataContext';
import LoadingScreen from './screens/LoadingScreen';
import ErrorBoundary from './components/ErrorBoundary';
import NotificationService from './services/NotificationService';
import BackgroundService from './services/BackgroundService';
import StorageService from './services/StorageService';
import {initializeApp} from './utils/initialization';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const [appState, setAppState] = useState(AppState.currentState);

  useEffect(() => {
    initializeApplication();
    setupAppStateListener();
    
    return () => {
      BackgroundService.cleanup();
    };
  }, []);

  const initializeApplication = async () => {
    try {
      setIsLoading(true);
      
      // Initialize core services
      await StorageService.initialize();
      await NotificationService.initialize();
      await BackgroundService.initialize();
      
      // Initialize app-specific services
      await initializeApp();
      
      setIsInitialized(true);
    } catch (error) {
      console.error('App initialization failed:', error);
      Alert.alert(
        'Initialization Error',
        'Failed to initialize the application. Please restart the app.',
        [{text: 'OK'}]
      );
    } finally {
      setIsLoading(false);
    }
  };

  const setupAppStateListener = () => {
    const handleAppStateChange = (nextAppState: AppStateStatus) => {
      if (appState.match(/inactive|background/) && nextAppState === 'active') {
        // App has come to the foreground
        BackgroundService.handleForeground();
      } else if (nextAppState.match(/inactive|background/)) {
        // App has gone to the background
        BackgroundService.handleBackground();
      }
      
      setAppState(nextAppState);
    };

    const subscription = AppState.addEventListener('change', handleAppStateChange);
    return () => subscription?.remove();
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isInitialized) {
    return (
      <View style={styles.errorContainer}>
        <LoadingScreen error="Failed to initialize application" />
      </View>
    );
  }

  return (
    <ErrorBoundary>
      <GestureHandlerRootView style={styles.container}>
        <SafeAreaProvider>
          <ThemeProvider>
            <AuthProvider>
              <DataProvider>
                <StatusBar
                  barStyle="dark-content"
                  backgroundColor="transparent"
                  translucent
                />
                <AppNavigator />
              </DataProvider>
            </AuthProvider>
          </ThemeProvider>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    </ErrorBoundary>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default App;