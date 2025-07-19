/**
 * Tasks Screen Component
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';

import {useTheme} from '../contexts/ThemeContext';

const TasksScreen: React.FC = () => {
  const {theme} = useTheme();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
      justifyContent: 'center',
      alignItems: 'center',
      padding: theme.spacing.lg,
    },
    title: {
      ...theme.typography.h2,
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    subtitle: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
  });

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Tasks</Text>
      <Text style={styles.subtitle}>
        Task management interface will be implemented here
      </Text>
    </View>
  );
};

export default TasksScreen;