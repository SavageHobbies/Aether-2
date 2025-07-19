/**
 * Local Storage Service
 * Handles encrypted local storage for sensitive data
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import EncryptedStorage from 'react-native-encrypted-storage';

interface Idea {
  id: string;
  content: string;
  timestamp: Date;
  source: 'voice' | 'text' | 'quick';
  processed: boolean;
  tags: string[];
}

interface Task {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high';
  dueDate?: Date;
  completed: boolean;
  sourceIdeaId?: string;
}

interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
}

class StorageService {
  private static readonly KEYS = {
    IDEAS: 'ideas',
    TASKS: 'tasks',
    CONVERSATIONS: 'conversations',
    LAST_SYNC_TIME: 'lastSyncTime',
    USER_PREFERENCES: 'userPreferences',
    SYNC_QUEUE: 'syncQueue',
  };

  static async initialize(): Promise<void> {
    try {
      // Initialize storage if needed
      console.log('Storage service initialized');
    } catch (error) {
      console.error('Storage initialization error:', error);
      throw error;
    }
  }

  // Ideas
  static async getIdeas(): Promise<Idea[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.IDEAS);
      if (!data) return [];
      
      const ideas = JSON.parse(data);
      return ideas.map((idea: any) => ({
        ...idea,
        timestamp: new Date(idea.timestamp),
        dueDate: idea.dueDate ? new Date(idea.dueDate) : undefined,
      }));
    } catch (error) {
      console.error('Get ideas error:', error);
      return [];
    }
  }

  static async saveIdeas(ideas: Idea[]): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.IDEAS, JSON.stringify(ideas));
    } catch (error) {
      console.error('Save ideas error:', error);
      throw error;
    }
  }

  static async saveIdea(idea: Idea): Promise<void> {
    try {
      const ideas = await this.getIdeas();
      const existingIndex = ideas.findIndex(i => i.id === idea.id);
      
      if (existingIndex >= 0) {
        ideas[existingIndex] = idea;
      } else {
        ideas.unshift(idea);
      }
      
      await this.saveIdeas(ideas);
    } catch (error) {
      console.error('Save idea error:', error);
      throw error;
    }
  }

  static async updateIdea(id: string, updates: Partial<Idea>): Promise<void> {
    try {
      const ideas = await this.getIdeas();
      const index = ideas.findIndex(idea => idea.id === id);
      
      if (index >= 0) {
        ideas[index] = {...ideas[index], ...updates};
        await this.saveIdeas(ideas);
      }
    } catch (error) {
      console.error('Update idea error:', error);
      throw error;
    }
  }

  static async deleteIdea(id: string): Promise<void> {
    try {
      const ideas = await this.getIdeas();
      const filteredIdeas = ideas.filter(idea => idea.id !== id);
      await this.saveIdeas(filteredIdeas);
    } catch (error) {
      console.error('Delete idea error:', error);
      throw error;
    }
  }

  // Tasks
  static async getTasks(): Promise<Task[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.TASKS);
      if (!data) return [];
      
      const tasks = JSON.parse(data);
      return tasks.map((task: any) => ({
        ...task,
        dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
      }));
    } catch (error) {
      console.error('Get tasks error:', error);
      return [];
    }
  }

  static async saveTasks(tasks: Task[]): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.TASKS, JSON.stringify(tasks));
    } catch (error) {
      console.error('Save tasks error:', error);
      throw error;
    }
  }

  static async saveTask(task: Task): Promise<void> {
    try {
      const tasks = await this.getTasks();
      const existingIndex = tasks.findIndex(t => t.id === task.id);
      
      if (existingIndex >= 0) {
        tasks[existingIndex] = task;
      } else {
        tasks.unshift(task);
      }
      
      await this.saveTasks(tasks);
    } catch (error) {
      console.error('Save task error:', error);
      throw error;
    }
  }

  static async updateTask(id: string, updates: Partial<Task>): Promise<void> {
    try {
      const tasks = await this.getTasks();
      const index = tasks.findIndex(task => task.id === id);
      
      if (index >= 0) {
        tasks[index] = {...tasks[index], ...updates};
        await this.saveTasks(tasks);
      }
    } catch (error) {
      console.error('Update task error:', error);
      throw error;
    }
  }

  static async deleteTask(id: string): Promise<void> {
    try {
      const tasks = await this.getTasks();
      const filteredTasks = tasks.filter(task => task.id !== id);
      await this.saveTasks(filteredTasks);
    } catch (error) {
      console.error('Delete task error:', error);
      throw error;
    }
  }

  // Conversations
  static async getConversations(): Promise<Conversation[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.CONVERSATIONS);
      if (!data) return [];
      
      const conversations = JSON.parse(data);
      return conversations.map((conv: any) => ({
        ...conv,
        timestamp: new Date(conv.timestamp),
      }));
    } catch (error) {
      console.error('Get conversations error:', error);
      return [];
    }
  }

  static async saveConversations(conversations: Conversation[]): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.CONVERSATIONS, JSON.stringify(conversations));
    } catch (error) {
      console.error('Save conversations error:', error);
      throw error;
    }
  }

  // Sync management
  static async getLastSyncTime(): Promise<Date | undefined> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.LAST_SYNC_TIME);
      return data ? new Date(data) : undefined;
    } catch (error) {
      console.error('Get last sync time error:', error);
      return undefined;
    }
  }

  static async setLastSyncTime(time: Date): Promise<void> {
    try {
      await AsyncStorage.setItem(this.KEYS.LAST_SYNC_TIME, time.toISOString());
    } catch (error) {
      console.error('Set last sync time error:', error);
      throw error;
    }
  }

  // Sync queue for offline operations
  static async getSyncQueue(): Promise<any[]> {
    try {
      const data = await AsyncStorage.getItem(this.KEYS.SYNC_QUEUE);
      return data ? JSON.parse(data) : [];
    } catch (error) {
      console.error('Get sync queue error:', error);
      return [];
    }
  }

  static async addToSyncQueue(operation: any): Promise<void> {
    try {
      const queue = await this.getSyncQueue();
      queue.push(operation);
      await AsyncStorage.setItem(this.KEYS.SYNC_QUEUE, JSON.stringify(queue));
    } catch (error) {
      console.error('Add to sync queue error:', error);
      throw error;
    }
  }

  static async clearSyncQueue(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.KEYS.SYNC_QUEUE);
    } catch (error) {
      console.error('Clear sync queue error:', error);
      throw error;
    }
  }

  // Secure storage for sensitive data
  static async getSecureItem(key: string): Promise<string | null> {
    try {
      return await EncryptedStorage.getItem(key);
    } catch (error) {
      console.error('Get secure item error:', error);
      return null;
    }
  }

  static async setSecureItem(key: string, value: string): Promise<void> {
    try {
      await EncryptedStorage.setItem(key, value);
    } catch (error) {
      console.error('Set secure item error:', error);
      throw error;
    }
  }

  static async removeSecureItem(key: string): Promise<void> {
    try {
      await EncryptedStorage.removeItem(key);
    } catch (error) {
      console.error('Remove secure item error:', error);
      throw error;
    }
  }

  // Clear all data (for logout/reset)
  static async clearAllData(): Promise<void> {
    try {
      await Promise.all([
        AsyncStorage.multiRemove([
          this.KEYS.IDEAS,
          this.KEYS.TASKS,
          this.KEYS.CONVERSATIONS,
          this.KEYS.LAST_SYNC_TIME,
          this.KEYS.SYNC_QUEUE,
        ]),
        EncryptedStorage.clear(),
      ]);
    } catch (error) {
      console.error('Clear all data error:', error);
      throw error;
    }
  }
}

export default StorageService;