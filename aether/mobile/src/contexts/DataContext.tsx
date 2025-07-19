/**
 * Data Context for managing app-wide data state
 */

import React, {createContext, useContext, useEffect, useState, ReactNode} from 'react';
import NetInfo from '@react-native-community/netinfo';

import ApiService from '../services/ApiService';
import StorageService from '../services/StorageService';
import SyncService from '../services/SyncService';

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

interface DataState {
  ideas: Idea[];
  tasks: Task[];
  conversations: Conversation[];
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime?: Date;
}

interface DataContextType {
  data: DataState;
  addIdea: (content: string, source: 'voice' | 'text' | 'quick') => Promise<string>;
  updateIdea: (id: string, updates: Partial<Idea>) => Promise<void>;
  deleteIdea: (id: string) => Promise<void>;
  addTask: (task: Omit<Task, 'id'>) => Promise<string>;
  updateTask: (id: string, updates: Partial<Task>) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  refreshData: () => Promise<void>;
  syncData: () => Promise<void>;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

interface DataProviderProps {
  children: ReactNode;
}

export const DataProvider: React.FC<DataProviderProps> = ({children}) => {
  const [data, setData] = useState<DataState>({
    ideas: [],
    tasks: [],
    conversations: [],
    isOnline: false,
    isSyncing: false,
  });

  useEffect(() => {
    initializeData();
    setupNetworkListener();
    
    return () => {
      // Cleanup if needed
    };
  }, []);

  const initializeData = async () => {
    try {
      // Load cached data from local storage
      const cachedIdeas = await StorageService.getIdeas();
      const cachedTasks = await StorageService.getTasks();
      const cachedConversations = await StorageService.getConversations();
      const lastSyncTime = await StorageService.getLastSyncTime();

      setData(prev => ({
        ...prev,
        ideas: cachedIdeas,
        tasks: cachedTasks,
        conversations: cachedConversations,
        lastSyncTime,
      }));

      // Try to sync with server if online
      const netInfo = await NetInfo.fetch();
      if (netInfo.isConnected) {
        await syncData();
      }
    } catch (error) {
      console.error('Data initialization error:', error);
    }
  };

  const setupNetworkListener = () => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const wasOffline = !data.isOnline;
      const isNowOnline = !!state.isConnected;
      
      setData(prev => ({
        ...prev,
        isOnline: isNowOnline,
      }));

      // Auto-sync when coming back online
      if (wasOffline && isNowOnline) {
        syncData();
      }
    });

    return unsubscribe;
  };

  const addIdea = async (content: string, source: 'voice' | 'text' | 'quick'): Promise<string> => {
    try {
      const newIdea: Idea = {
        id: Date.now().toString(),
        content,
        timestamp: new Date(),
        source,
        processed: false,
        tags: [],
      };

      // Add to local state
      setData(prev => ({
        ...prev,
        ideas: [newIdea, ...prev.ideas],
      }));

      // Save to local storage
      await StorageService.saveIdea(newIdea);

      // Try to sync with server if online
      if (data.isOnline) {
        try {
          await ApiService.createIdea(newIdea);
        } catch (error) {
          console.warn('Failed to sync idea to server:', error);
          // Mark for later sync
          await SyncService.markForSync('idea', newIdea.id, 'create');
        }
      } else {
        // Mark for later sync
        await SyncService.markForSync('idea', newIdea.id, 'create');
      }

      return newIdea.id;
    } catch (error) {
      console.error('Add idea error:', error);
      throw error;
    }
  };

  const updateIdea = async (id: string, updates: Partial<Idea>): Promise<void> => {
    try {
      setData(prev => ({
        ...prev,
        ideas: prev.ideas.map(idea =>
          idea.id === id ? {...idea, ...updates} : idea
        ),
      }));

      await StorageService.updateIdea(id, updates);

      if (data.isOnline) {
        try {
          await ApiService.updateIdea(id, updates);
        } catch (error) {
          console.warn('Failed to sync idea update to server:', error);
          await SyncService.markForSync('idea', id, 'update');
        }
      } else {
        await SyncService.markForSync('idea', id, 'update');
      }
    } catch (error) {
      console.error('Update idea error:', error);
      throw error;
    }
  };

  const deleteIdea = async (id: string): Promise<void> => {
    try {
      setData(prev => ({
        ...prev,
        ideas: prev.ideas.filter(idea => idea.id !== id),
      }));

      await StorageService.deleteIdea(id);

      if (data.isOnline) {
        try {
          await ApiService.deleteIdea(id);
        } catch (error) {
          console.warn('Failed to sync idea deletion to server:', error);
          await SyncService.markForSync('idea', id, 'delete');
        }
      } else {
        await SyncService.markForSync('idea', id, 'delete');
      }
    } catch (error) {
      console.error('Delete idea error:', error);
      throw error;
    }
  };

  const addTask = async (taskData: Omit<Task, 'id'>): Promise<string> => {
    try {
      const newTask: Task = {
        ...taskData,
        id: Date.now().toString(),
      };

      setData(prev => ({
        ...prev,
        tasks: [newTask, ...prev.tasks],
      }));

      await StorageService.saveTask(newTask);

      if (data.isOnline) {
        try {
          await ApiService.createTask(newTask);
        } catch (error) {
          console.warn('Failed to sync task to server:', error);
          await SyncService.markForSync('task', newTask.id, 'create');
        }
      } else {
        await SyncService.markForSync('task', newTask.id, 'create');
      }

      return newTask.id;
    } catch (error) {
      console.error('Add task error:', error);
      throw error;
    }
  };

  const updateTask = async (id: string, updates: Partial<Task>): Promise<void> => {
    try {
      setData(prev => ({
        ...prev,
        tasks: prev.tasks.map(task =>
          task.id === id ? {...task, ...updates} : task
        ),
      }));

      await StorageService.updateTask(id, updates);

      if (data.isOnline) {
        try {
          await ApiService.updateTask(id, updates);
        } catch (error) {
          console.warn('Failed to sync task update to server:', error);
          await SyncService.markForSync('task', id, 'update');
        }
      } else {
        await SyncService.markForSync('task', id, 'update');
      }
    } catch (error) {
      console.error('Update task error:', error);
      throw error;
    }
  };

  const deleteTask = async (id: string): Promise<void> => {
    try {
      setData(prev => ({
        ...prev,
        tasks: prev.tasks.filter(task => task.id !== id),
      }));

      await StorageService.deleteTask(id);

      if (data.isOnline) {
        try {
          await ApiService.deleteTask(id);
        } catch (error) {
          console.warn('Failed to sync task deletion to server:', error);
          await SyncService.markForSync('task', id, 'delete');
        }
      } else {
        await SyncService.markForSync('task', id, 'delete');
      }
    } catch (error) {
      console.error('Delete task error:', error);
      throw error;
    }
  };

  const refreshData = async (): Promise<void> => {
    if (!data.isOnline) {
      return;
    }

    try {
      const [ideas, tasks, conversations] = await Promise.all([
        ApiService.getIdeas(),
        ApiService.getTasks(),
        ApiService.getConversations(),
      ]);

      setData(prev => ({
        ...prev,
        ideas,
        tasks,
        conversations,
        lastSyncTime: new Date(),
      }));

      // Update local storage
      await StorageService.saveIdeas(ideas);
      await StorageService.saveTasks(tasks);
      await StorageService.saveConversations(conversations);
      await StorageService.setLastSyncTime(new Date());
    } catch (error) {
      console.error('Refresh data error:', error);
      throw error;
    }
  };

  const syncData = async (): Promise<void> => {
    if (!data.isOnline || data.isSyncing) {
      return;
    }

    try {
      setData(prev => ({...prev, isSyncing: true}));
      
      await SyncService.syncPendingChanges();
      await refreshData();
    } catch (error) {
      console.error('Sync data error:', error);
      throw error;
    } finally {
      setData(prev => ({...prev, isSyncing: false}));
    }
  };

  const value: DataContextType = {
    data,
    addIdea,
    updateIdea,
    deleteIdea,
    addTask,
    updateTask,
    deleteTask,
    refreshData,
    syncData,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = (): DataContextType => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};