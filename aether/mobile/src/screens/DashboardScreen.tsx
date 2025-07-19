/**
 * Dashboard Screen Component
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {useTheme} from '../contexts/ThemeContext';
import {useData} from '../contexts/DataContext';

const DashboardScreen: React.FC = () => {
  const {theme} = useTheme();
  const {data} = useData();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    scrollContainer: {
      padding: theme.spacing.md,
    },
    statsContainer: {
      flexDirection: 'row',
      marginBottom: theme.spacing.lg,
    },
    statCard: {
      flex: 1,
      backgroundColor: theme.colors.surface,
      padding: theme.spacing.md,
      borderRadius: theme.borderRadius.md,
      marginHorizontal: theme.spacing.sm,
      alignItems: 'center',
    },
    statNumber: {
      ...theme.typography.h2,
      color: theme.colors.primary,
      marginBottom: theme.spacing.sm,
    },
    statLabel: {
      ...theme.typography.caption,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
    sectionTitle: {
      ...theme.typography.h3,
      color: theme.colors.text,
      marginBottom: theme.spacing.md,
    },
    quickActionsContainer: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginBottom: theme.spacing.lg,
    },
    quickActionButton: {
      width: '48%',
      backgroundColor: theme.colors.surface,
      padding: theme.spacing.md,
      borderRadius: theme.borderRadius.md,
      margin: '1%',
      alignItems: 'center',
    },
    quickActionIcon: {
      marginBottom: theme.spacing.sm,
    },
    quickActionText: {
      ...theme.typography.body,
      color: theme.colors.text,
      textAlign: 'center',
    },
  });

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <View style={styles.statsContainer}>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{data.ideas.length}</Text>
            <Text style={styles.statLabel}>Ideas Captured</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statNumber}>{data.tasks.length}</Text>
            <Text style={styles.statLabel}>Active Tasks</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActionsContainer}>
          <TouchableOpacity style={styles.quickActionButton}>
            <Icon
              name="lightbulb"
              size={32}
              color={theme.colors.primary}
              style={styles.quickActionIcon}
            />
            <Text style={styles.quickActionText}>Capture Idea</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickActionButton}>
            <Icon
              name="chat"
              size={32}
              color={theme.colors.primary}
              style={styles.quickActionIcon}
            />
            <Text style={styles.quickActionText}>Start Chat</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickActionButton}>
            <Icon
              name="assignment"
              size={32}
              color={theme.colors.primary}
              style={styles.quickActionIcon}
            />
            <Text style={styles.quickActionText}>View Tasks</Text>
          </TouchableOpacity>
          
          <TouchableOpacity style={styles.quickActionButton}>
            <Icon
              name="sync"
              size={32}
              color={theme.colors.primary}
              style={styles.quickActionIcon}
            />
            <Text style={styles.quickActionText}>Sync Data</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

export default DashboardScreen;