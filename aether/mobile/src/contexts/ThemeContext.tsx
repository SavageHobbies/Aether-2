/**
 * Theme Context
 */

import React, {createContext, useContext, useEffect, useState, ReactNode} from 'react';
import {Appearance, ColorSchemeName} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Colors {
  primary: string;
  primaryDark: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  error: string;
  warning: string;
  success: string;
  info: string;
}

interface Theme {
  colors: Colors;
  isDark: boolean;
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
  };
  typography: {
    h1: {fontSize: number; fontWeight: string};
    h2: {fontSize: number; fontWeight: string};
    h3: {fontSize: number; fontWeight: string};
    body: {fontSize: number; fontWeight: string};
    caption: {fontSize: number; fontWeight: string};
  };
}

const lightColors: Colors = {
  primary: '#6366f1',
  primaryDark: '#5855eb',
  secondary: '#22c55e',
  background: '#f8fafc',
  surface: '#ffffff',
  text: '#1e293b',
  textSecondary: '#64748b',
  border: '#e2e8f0',
  error: '#ef4444',
  warning: '#f59e0b',
  success: '#22c55e',
  info: '#3b82f6',
};

const darkColors: Colors = {
  primary: '#6366f1',
  primaryDark: '#5855eb',
  secondary: '#22c55e',
  background: '#0f172a',
  surface: '#1e293b',
  text: '#f1f5f9',
  textSecondary: '#94a3b8',
  border: '#334155',
  error: '#ef4444',
  warning: '#f59e0b',
  success: '#22c55e',
  info: '#3b82f6',
};

const createTheme = (isDark: boolean): Theme => ({
  colors: isDark ? darkColors : lightColors,
  isDark,
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
  },
  typography: {
    h1: {fontSize: 32, fontWeight: '700'},
    h2: {fontSize: 24, fontWeight: '600'},
    h3: {fontSize: 20, fontWeight: '600'},
    body: {fontSize: 16, fontWeight: '400'},
    caption: {fontSize: 14, fontWeight: '400'},
  },
});

interface ThemeContextType {
  theme: Theme;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (isDark: boolean) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({children}) => {
  const [isDark, setIsDark] = useState(false);
  const [theme, setTheme] = useState(createTheme(false));

  useEffect(() => {
    initializeTheme();
    
    const subscription = Appearance.addChangeListener(({colorScheme}) => {
      handleSystemThemeChange(colorScheme);
    });

    return () => subscription?.remove();
  }, []);

  useEffect(() => {
    setTheme(createTheme(isDark));
  }, [isDark]);

  const initializeTheme = async () => {
    try {
      const storedTheme = await AsyncStorage.getItem('theme');
      if (storedTheme) {
        const isDarkStored = storedTheme === 'dark';
        setIsDark(isDarkStored);
      } else {
        // Use system theme as default
        const systemColorScheme = Appearance.getColorScheme();
        setIsDark(systemColorScheme === 'dark');
      }
    } catch (error) {
      console.error('Theme initialization error:', error);
      // Fallback to system theme
      const systemColorScheme = Appearance.getColorScheme();
      setIsDark(systemColorScheme === 'dark');
    }
  };

  const handleSystemThemeChange = async (colorScheme: ColorSchemeName) => {
    try {
      const storedTheme = await AsyncStorage.getItem('theme');
      // Only follow system theme if user hasn't manually set a preference
      if (!storedTheme) {
        setIsDark(colorScheme === 'dark');
      }
    } catch (error) {
      console.error('System theme change error:', error);
    }
  };

  const toggleTheme = async () => {
    try {
      const newIsDark = !isDark;
      setIsDark(newIsDark);
      await AsyncStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    } catch (error) {
      console.error('Toggle theme error:', error);
    }
  };

  const setThemeMode = async (newIsDark: boolean) => {
    try {
      setIsDark(newIsDark);
      await AsyncStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    } catch (error) {
      console.error('Set theme error:', error);
    }
  };

  const value: ThemeContextType = {
    theme,
    isDark,
    toggleTheme,
    setTheme: setThemeMode,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};