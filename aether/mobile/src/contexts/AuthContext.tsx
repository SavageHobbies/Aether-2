/**
 * Authentication Context
 */

import React, {createContext, useContext, useEffect, useState, ReactNode} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import EncryptedStorage from 'react-native-encrypted-storage';
import {Alert} from 'react-native';

interface User {
  id: string;
  email: string;
  name: string;
  preferences: {
    voiceEnabled: boolean;
    notificationsEnabled: boolean;
    biometricEnabled: boolean;
  };
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isFirstLaunch: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<boolean>;
  updateUser: (updates: Partial<User>) => Promise<void>;
  completeOnboarding: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({children}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isFirstLaunch, setIsFirstLaunch] = useState(false);

  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      setIsLoading(true);
      
      // Check if this is the first launch
      const hasLaunchedBefore = await AsyncStorage.getItem('hasLaunchedBefore');
      if (!hasLaunchedBefore) {
        setIsFirstLaunch(true);
        setIsLoading(false);
        return;
      }

      // Try to restore user session
      const storedUser = await EncryptedStorage.getItem('user');
      const authToken = await EncryptedStorage.getItem('authToken');
      
      if (storedUser && authToken) {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      // TODO: Replace with actual API call
      // For now, simulate login with mock data
      if (email && password) {
        const mockUser: User = {
          id: '1',
          email,
          name: email.split('@')[0],
          preferences: {
            voiceEnabled: true,
            notificationsEnabled: true,
            biometricEnabled: false,
          },
        };
        
        const mockToken = 'mock-jwt-token';
        
        await EncryptedStorage.setItem('user', JSON.stringify(mockUser));
        await EncryptedStorage.setItem('authToken', mockToken);
        
        setUser(mockUser);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Login error:', error);
      Alert.alert('Login Error', 'Failed to login. Please try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      
      // TODO: Replace with actual API call
      // For now, simulate registration
      if (email && password && name) {
        const newUser: User = {
          id: Date.now().toString(),
          email,
          name,
          preferences: {
            voiceEnabled: true,
            notificationsEnabled: true,
            biometricEnabled: false,
          },
        };
        
        const mockToken = 'mock-jwt-token';
        
        await EncryptedStorage.setItem('user', JSON.stringify(newUser));
        await EncryptedStorage.setItem('authToken', mockToken);
        
        setUser(newUser);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Registration error:', error);
      Alert.alert('Registration Error', 'Failed to create account. Please try again.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await EncryptedStorage.removeItem('user');
      await EncryptedStorage.removeItem('authToken');
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const updateUser = async (updates: Partial<User>): Promise<void> => {
    try {
      if (!user) return;
      
      const updatedUser = {...user, ...updates};
      await EncryptedStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
    } catch (error) {
      console.error('Update user error:', error);
      Alert.alert('Update Error', 'Failed to update user preferences.');
    }
  };

  const completeOnboarding = async (): Promise<void> => {
    try {
      await AsyncStorage.setItem('hasLaunchedBefore', 'true');
      setIsFirstLaunch(false);
    } catch (error) {
      console.error('Complete onboarding error:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isFirstLaunch,
    isLoading,
    login,
    logout,
    register,
    updateUser,
    completeOnboarding,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};