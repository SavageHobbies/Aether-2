/**
 * Onboarding Screen Component
 */

import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';

import {useTheme} from '../contexts/ThemeContext';
import {useAuth} from '../contexts/AuthContext';

const {width: screenWidth} = Dimensions.get('window');

interface OnboardingSlide {
  id: string;
  title: string;
  description: string;
  icon: string;
}

const onboardingSlides: OnboardingSlide[] = [
  {
    id: '1',
    title: 'Welcome to Aether',
    description: 'Your intelligent AI companion for capturing ideas, managing tasks, and staying organized.',
    icon: 'psychology',
  },
  {
    id: '2',
    title: 'Capture Ideas Instantly',
    description: 'Use voice or text to quickly capture your thoughts and ideas wherever you are.',
    icon: 'lightbulb',
  },
  {
    id: '3',
    title: 'Smart Task Management',
    description: 'Automatically convert ideas to tasks and get intelligent reminders and suggestions.',
    icon: 'assignment',
  },
  {
    id: '4',
    title: 'Always in Sync',
    description: 'Your data syncs seamlessly across all your devices with secure encryption.',
    icon: 'sync',
  },
];

const OnboardingScreen: React.FC = () => {
  const {theme} = useTheme();
  const {completeOnboarding} = useAuth();
  const [currentSlide, setCurrentSlide] = useState(0);

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    slideContainer: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: theme.spacing.lg,
    },
    iconContainer: {
      width: 120,
      height: 120,
      borderRadius: 60,
      backgroundColor: theme.colors.primary,
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: theme.spacing.xl,
    },
    icon: {
      color: 'white',
    },
    title: {
      ...theme.typography.h1,
      color: theme.colors.text,
      textAlign: 'center',
      marginBottom: theme.spacing.md,
    },
    description: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      textAlign: 'center',
      lineHeight: 24,
      marginBottom: theme.spacing.xl,
    },
    pagination: {
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: theme.spacing.xl,
    },
    paginationDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      marginHorizontal: 4,
    },
    paginationDotActive: {
      backgroundColor: theme.colors.primary,
    },
    paginationDotInactive: {
      backgroundColor: theme.colors.border,
    },
    buttonContainer: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: theme.spacing.lg,
      paddingBottom: theme.spacing.xl,
    },
    button: {
      paddingVertical: theme.spacing.md,
      paddingHorizontal: theme.spacing.lg,
      borderRadius: theme.borderRadius.lg,
      minWidth: 100,
      alignItems: 'center',
    },
    primaryButton: {
      backgroundColor: theme.colors.primary,
    },
    secondaryButton: {
      backgroundColor: 'transparent',
    },
    primaryButtonText: {
      ...theme.typography.body,
      color: 'white',
      fontWeight: '600',
    },
    secondaryButtonText: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      fontWeight: '600',
    },
  });

  const handleNext = () => {
    if (currentSlide < onboardingSlides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    } else {
      completeOnboarding();
    }
  };

  const handleSkip = () => {
    completeOnboarding();
  };

  const handlePrevious = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const currentSlideData = onboardingSlides[currentSlide];
  const isLastSlide = currentSlide === onboardingSlides.length - 1;

  return (
    <View style={styles.container}>
      <View style={styles.slideContainer}>
        <View style={styles.iconContainer}>
          <Icon name={currentSlideData.icon} size={60} style={styles.icon} />
        </View>
        
        <Text style={styles.title}>{currentSlideData.title}</Text>
        <Text style={styles.description}>{currentSlideData.description}</Text>
        
        <View style={styles.pagination}>
          {onboardingSlides.map((_, index) => (
            <View
              key={index}
              style={[
                styles.paginationDot,
                index === currentSlide
                  ? styles.paginationDotActive
                  : styles.paginationDotInactive,
              ]}
            />
          ))}
        </View>
      </View>
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={currentSlide > 0 ? handlePrevious : handleSkip}
        >
          <Text style={styles.secondaryButtonText}>
            {currentSlide > 0 ? 'Previous' : 'Skip'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, styles.primaryButton]}
          onPress={handleNext}
        >
          <Text style={styles.primaryButtonText}>
            {isLastSlide ? 'Get Started' : 'Next'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default OnboardingScreen;