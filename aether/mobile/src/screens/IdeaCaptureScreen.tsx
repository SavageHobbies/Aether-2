/**
 * Idea Capture Screen Component
 */

import React, {useState, useEffect, useRef} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Animated,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  Vibration,
} from 'react-native';
import {RouteProp} from '@react-navigation/native';
import {StackNavigationProp} from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialIcons';
import Voice from '@react-native-voice/voice';
import HapticFeedback from 'react-native-haptic-feedback';

import {useTheme} from '../contexts/ThemeContext';
import {useData} from '../contexts/DataContext';
import {RootStackParamList} from '../navigation/AppNavigator';

type IdeaCaptureScreenRouteProp = RouteProp<RootStackParamList, 'IdeaCapture'>;
type IdeaCaptureScreenNavigationProp = StackNavigationProp<RootStackParamList, 'IdeaCapture'>;

interface Props {
  route: IdeaCaptureScreenRouteProp;
  navigation: IdeaCaptureScreenNavigationProp;
}

const {width: screenWidth, height: screenHeight} = Dimensions.get('window');

const IdeaCaptureScreen: React.FC<Props> = ({route, navigation}) => {
  const {theme} = useTheme();
  const {addIdea} = useData();
  
  const [ideaText, setIdeaText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [captureMode, setCaptureMode] = useState<'text' | 'voice'>('text');
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');
  
  // Animation values
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  
  // Refs
  const textInputRef = useRef<TextInput>(null);
  const recordingTimer = useRef<NodeJS.Timeout | null>(null);
  
  // Initialize with route params
  useEffect(() => {
    const {initialText, source} = route.params || {};
    
    if (initialText) {
      setIdeaText(initialText);
    }
    
    if (source === 'voice') {
      setCaptureMode('voice');
      startVoiceCapture();
    } else if (source === 'quick') {
      // Quick capture mode - focus on text input immediately
      setTimeout(() => textInputRef.current?.focus(), 100);
    }
    
    // Animate screen entrance
    Animated.parallel([
      Animated.timing(slideAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start();
    
    return () => {
      if (recordingTimer.current) {
        clearInterval(recordingTimer.current);
      }
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, [route.params]);

  // Voice recording setup
  useEffect(() => {
    Voice.onSpeechStart = onSpeechStart;
    Voice.onSpeechRecognized = onSpeechRecognized;
    Voice.onSpeechEnd = onSpeechEnd;
    Voice.onSpeechError = onSpeechError;
    Voice.onSpeechResults = onSpeechResults;
    Voice.onSpeechPartialResults = onSpeechPartialResults;

    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  // Pulse animation for recording
  useEffect(() => {
    if (isRecording) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      );
      pulse.start();
      
      // Start recording timer
      recordingTimer.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      return () => {
        pulse.stop();
        if (recordingTimer.current) {
          clearInterval(recordingTimer.current);
        }
      };
    } else {
      pulseAnim.setValue(1);
      setRecordingTime(0);
      if (recordingTimer.current) {
        clearInterval(recordingTimer.current);
      }
    }
  }, [isRecording, pulseAnim]);

  const onSpeechStart = () => {
    console.log('Speech recognition started');
  };

  const onSpeechRecognized = () => {
    console.log('Speech recognized');
  };

  const onSpeechEnd = () => {
    console.log('Speech recognition ended');
    setIsRecording(false);
  };

  const onSpeechError = (error: any) => {
    console.error('Speech recognition error:', error);
    setIsRecording(false);
    setIsProcessing(false);
    Alert.alert('Voice Recognition Error', 'Failed to recognize speech. Please try again.');
  };

  const onSpeechResults = (event: any) => {
    const result = event.value[0];
    if (result) {
      setIdeaText(prev => prev ? `${prev} ${result}` : result);
    }
    setIsProcessing(false);
  };

  const onSpeechPartialResults = (event: any) => {
    const partialResult = event.value[0];
    // Could show partial results in real-time if desired
  };

  const startVoiceCapture = async () => {
    try {
      setIsRecording(true);
      setIsProcessing(true);
      
      // Haptic feedback
      HapticFeedback.trigger('impactLight');
      
      await Voice.start('en-US');
    } catch (error) {
      console.error('Start voice capture error:', error);
      setIsRecording(false);
      setIsProcessing(false);
      Alert.alert('Voice Error', 'Failed to start voice recording. Please check permissions.');
    }
  };

  const stopVoiceCapture = async () => {
    try {
      await Voice.stop();
      setIsRecording(false);
      
      // Haptic feedback
      HapticFeedback.trigger('impactMedium');
    } catch (error) {
      console.error('Stop voice capture error:', error);
      setIsRecording(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      stopVoiceCapture();
    } else {
      startVoiceCapture();
    }
  };

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleSave = async () => {
    if (!ideaText.trim()) {
      Alert.alert('Empty Idea', 'Please enter some text or record your idea.');
      return;
    }

    try {
      setIsProcessing(true);
      
      const source = route.params?.source || (captureMode === 'voice' ? 'voice' : 'text');
      await addIdea(ideaText.trim(), source);
      
      // Success haptic feedback
      HapticFeedback.trigger('notificationSuccess');
      
      // Show success and navigate back
      Alert.alert(
        'Idea Saved!',
        'Your idea has been captured successfully.',
        [
          {
            text: 'Add Another',
            onPress: () => {
              setIdeaText('');
              setTags([]);
              setCaptureMode('text');
              textInputRef.current?.focus();
            },
          },
          {
            text: 'Done',
            onPress: () => navigation.goBack(),
            style: 'default',
          },
        ]
      );
    } catch (error) {
      console.error('Save idea error:', error);
      Alert.alert('Save Error', 'Failed to save your idea. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleQuickSave = async () => {
    if (ideaText.trim()) {
      try {
        const source = route.params?.source || 'quick';
        await addIdea(ideaText.trim(), source);
        HapticFeedback.trigger('notificationSuccess');
        navigation.goBack();
      } catch (error) {
        console.error('Quick save error:', error);
      }
    }
  };

  const formatRecordingTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.background,
    },
    animatedContainer: {
      flex: 1,
      transform: [
        {
          translateY: slideAnim.interpolate({
            inputRange: [0, 1],
            outputRange: [50, 0],
          }),
        },
      ],
      opacity: fadeAnim,
    },
    scrollContainer: {
      flexGrow: 1,
      padding: theme.spacing.lg,
    },
    header: {
      alignItems: 'center',
      marginBottom: theme.spacing.xl,
    },
    title: {
      ...theme.typography.h2,
      color: theme.colors.text,
      marginBottom: theme.spacing.sm,
    },
    subtitle: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
    modeSelector: {
      flexDirection: 'row',
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius.lg,
      padding: 4,
      marginBottom: theme.spacing.lg,
    },
    modeButton: {
      flex: 1,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      borderRadius: theme.borderRadius.md,
      alignItems: 'center',
    },
    modeButtonActive: {
      backgroundColor: theme.colors.primary,
    },
    modeButtonText: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      fontWeight: '500',
    },
    modeButtonTextActive: {
      color: 'white',
    },
    inputContainer: {
      marginBottom: theme.spacing.lg,
    },
    textInput: {
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius.lg,
      padding: theme.spacing.lg,
      ...theme.typography.body,
      color: theme.colors.text,
      minHeight: 120,
      textAlignVertical: 'top',
      borderWidth: 2,
      borderColor: 'transparent',
    },
    textInputFocused: {
      borderColor: theme.colors.primary,
    },
    voiceContainer: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 200,
    },
    voiceButton: {
      width: 120,
      height: 120,
      borderRadius: 60,
      backgroundColor: theme.colors.primary,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: theme.spacing.md,
      elevation: 8,
      shadowColor: theme.colors.primary,
      shadowOffset: {width: 0, height: 4},
      shadowOpacity: 0.3,
      shadowRadius: 8,
    },
    voiceButtonRecording: {
      backgroundColor: theme.colors.error,
    },
    voiceButtonProcessing: {
      backgroundColor: theme.colors.warning,
    },
    recordingTime: {
      ...theme.typography.h3,
      color: theme.colors.text,
      marginBottom: theme.spacing.sm,
    },
    recordingStatus: {
      ...theme.typography.body,
      color: theme.colors.textSecondary,
      textAlign: 'center',
    },
    tagsContainer: {
      marginBottom: theme.spacing.lg,
    },
    tagsLabel: {
      ...theme.typography.body,
      color: theme.colors.text,
      fontWeight: '600',
      marginBottom: theme.spacing.sm,
    },
    tagInputContainer: {
      flexDirection: 'row',
      marginBottom: theme.spacing.md,
    },
    tagInput: {
      flex: 1,
      backgroundColor: theme.colors.surface,
      borderRadius: theme.borderRadius.md,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      ...theme.typography.body,
      color: theme.colors.text,
      marginRight: theme.spacing.sm,
    },
    addTagButton: {
      backgroundColor: theme.colors.primary,
      borderRadius: theme.borderRadius.md,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      justifyContent: 'center',
    },
    addTagButtonText: {
      color: 'white',
      fontWeight: '600',
    },
    tagsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: theme.spacing.sm,
    },
    tag: {
      backgroundColor: theme.colors.primary,
      borderRadius: theme.borderRadius.lg,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      flexDirection: 'row',
      alignItems: 'center',
    },
    tagText: {
      color: 'white',
      ...theme.typography.caption,
      marginRight: theme.spacing.sm,
    },
    removeTagButton: {
      padding: 2,
    },
    actionsContainer: {
      flexDirection: 'row',
      gap: theme.spacing.md,
      marginTop: 'auto',
      paddingTop: theme.spacing.lg,
    },
    actionButton: {
      flex: 1,
      backgroundColor: theme.colors.surface,
      paddingVertical: theme.spacing.md,
      borderRadius: theme.borderRadius.lg,
      alignItems: 'center',
      flexDirection: 'row',
      justifyContent: 'center',
      gap: theme.spacing.sm,
    },
    primaryButton: {
      backgroundColor: theme.colors.primary,
    },
    actionButtonText: {
      ...theme.typography.body,
      color: theme.colors.text,
      fontWeight: '600',
    },
    primaryButtonText: {
      color: 'white',
    },
    quickActions: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      paddingVertical: theme.spacing.md,
      borderTopWidth: 1,
      borderTopColor: theme.colors.border,
      marginTop: theme.spacing.lg,
    },
    quickActionButton: {
      alignItems: 'center',
      padding: theme.spacing.sm,
    },
    quickActionText: {
      ...theme.typography.caption,
      color: theme.colors.textSecondary,
      marginTop: theme.spacing.xs,
    },
  });

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <Animated.View style={styles.animatedContainer}>
        <ScrollView
          contentContainerStyle={styles.scrollContainer}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.title}>Capture Your Idea</Text>
            <Text style={styles.subtitle}>
              Express your thoughts through text or voice
            </Text>
          </View>

          <View style={styles.modeSelector}>
            <TouchableOpacity
              style={[
                styles.modeButton,
                captureMode === 'text' && styles.modeButtonActive,
              ]}
              onPress={() => setCaptureMode('text')}
            >
              <Text
                style={[
                  styles.modeButtonText,
                  captureMode === 'text' && styles.modeButtonTextActive,
                ]}
              >
                Text
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.modeButton,
                captureMode === 'voice' && styles.modeButtonActive,
              ]}
              onPress={() => setCaptureMode('voice')}
            >
              <Text
                style={[
                  styles.modeButtonText,
                  captureMode === 'voice' && styles.modeButtonTextActive,
                ]}
              >
                Voice
              </Text>
            </TouchableOpacity>
          </View>

          {captureMode === 'text' ? (
            <View style={styles.inputContainer}>
              <TextInput
                ref={textInputRef}
                style={styles.textInput}
                value={ideaText}
                onChangeText={setIdeaText}
                placeholder="What's on your mind?"
                placeholderTextColor={theme.colors.textSecondary}
                multiline
                autoFocus={route.params?.source === 'quick'}
                textAlignVertical="top"
              />
            </View>
          ) : (
            <View style={styles.voiceContainer}>
              <Animated.View style={{transform: [{scale: pulseAnim}]}}>
                <TouchableOpacity
                  style={[
                    styles.voiceButton,
                    isRecording && styles.voiceButtonRecording,
                    isProcessing && styles.voiceButtonProcessing,
                  ]}
                  onPress={handleVoiceToggle}
                  disabled={isProcessing}
                >
                  <Icon
                    name={isRecording ? 'stop' : 'mic'}
                    size={48}
                    color="white"
                  />
                </TouchableOpacity>
              </Animated.View>
              
              {isRecording && (
                <Text style={styles.recordingTime}>
                  {formatRecordingTime(recordingTime)}
                </Text>
              )}
              
              <Text style={styles.recordingStatus}>
                {isRecording
                  ? 'Recording... Tap to stop'
                  : isProcessing
                  ? 'Processing...'
                  : 'Tap to start recording'}
              </Text>
              
              {ideaText ? (
                <View style={[styles.inputContainer, {marginTop: theme.spacing.lg}]}>
                  <TextInput
                    style={styles.textInput}
                    value={ideaText}
                    onChangeText={setIdeaText}
                    placeholder="Edit your transcribed text..."
                    placeholderTextColor={theme.colors.textSecondary}
                    multiline
                    textAlignVertical="top"
                  />
                </View>
              ) : null}
            </View>
          )}

          <View style={styles.tagsContainer}>
            <Text style={styles.tagsLabel}>Tags (Optional)</Text>
            <View style={styles.tagInputContainer}>
              <TextInput
                style={styles.tagInput}
                value={newTag}
                onChangeText={setNewTag}
                placeholder="Add a tag..."
                placeholderTextColor={theme.colors.textSecondary}
                onSubmitEditing={addTag}
              />
              <TouchableOpacity style={styles.addTagButton} onPress={addTag}>
                <Text style={styles.addTagButtonText}>Add</Text>
              </TouchableOpacity>
            </View>
            
            {tags.length > 0 && (
              <View style={styles.tagsRow}>
                {tags.map((tag, index) => (
                  <View key={index} style={styles.tag}>
                    <Text style={styles.tagText}>{tag}</Text>
                    <TouchableOpacity
                      style={styles.removeTagButton}
                      onPress={() => removeTag(tag)}
                    >
                      <Icon name="close" size={16} color="white" />
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            )}
          </View>
        </ScrollView>

        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigation.goBack()}
          >
            <Icon name="close" size={20} color={theme.colors.text} />
            <Text style={styles.actionButtonText}>Cancel</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={handleSave}
            disabled={isProcessing || !ideaText.trim()}
          >
            <Icon name="save" size={20} color="white" />
            <Text style={styles.primaryButtonText}>
              {isProcessing ? 'Saving...' : 'Save Idea'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.quickActions}>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={handleQuickSave}
            disabled={!ideaText.trim()}
          >
            <Icon
              name="flash-on"
              size={24}
              color={ideaText.trim() ? theme.colors.primary : theme.colors.textSecondary}
            />
            <Text style={styles.quickActionText}>Quick Save</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => {
              setIdeaText('');
              setTags([]);
              textInputRef.current?.focus();
            }}
          >
            <Icon name="refresh" size={24} color={theme.colors.textSecondary} />
            <Text style={styles.quickActionText}>Clear</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => setCaptureMode(captureMode === 'text' ? 'voice' : 'text')}
          >
            <Icon
              name={captureMode === 'text' ? 'mic' : 'keyboard'}
              size={24}
              color={theme.colors.textSecondary}
            />
            <Text style={styles.quickActionText}>Switch Mode</Text>
          </TouchableOpacity>
        </View>
      </Animated.View>
    </KeyboardAvoidingView>
  );
};

export default IdeaCaptureScreen;