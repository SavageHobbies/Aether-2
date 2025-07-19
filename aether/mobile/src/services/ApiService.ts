/**
 * API Service for backend communication
 */

import axios, {AxiosInstance, AxiosResponse} from 'axios';
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

class ApiService {
  private static instance: AxiosInstance;
  private static baseURL = 'http://localhost:8000'; // TODO: Use environment variable

  static async initialize(): Promise<void> {
    this.instance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to include auth token
    this.instance.interceptors.request.use(
      async (config) => {
        try {
          const token = await EncryptedStorage.getItem('authToken');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          console.error('Error getting auth token:', error);
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.instance.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          // TODO: Implement logout logic
        }
        return Promise.reject(error);
      }
    );
  }

  // Ideas API
  static async getIdeas(): Promise<Idea[]> {
    try {
      const response: AxiosResponse<Idea[]> = await this.instance.get('/api/ideas');
      return response.data.map(idea => ({
        ...idea,
        timestamp: new Date(idea.timestamp),
      }));
    } catch (error) {
      console.error('Get ideas error:', error);
      throw error;
    }
  }

  static async createIdea(idea: Idea): Promise<Idea> {
    try {
      const response: AxiosResponse<Idea> = await this.instance.post('/api/ideas', idea);
      return {
        ...response.data,
        timestamp: new Date(response.data.timestamp),
      };
    } catch (error) {
      console.error('Create idea error:', error);
      throw error;
    }
  }

  static async updateIdea(id: string, updates: Partial<Idea>): Promise<Idea> {
    try {
      const response: AxiosResponse<Idea> = await this.instance.put(`/api/ideas/${id}`, updates);
      return {
        ...response.data,
        timestamp: new Date(response.data.timestamp),
      };
    } catch (error) {
      console.error('Update idea error:', error);
      throw error;
    }
  }

  static async deleteIdea(id: string): Promise<void> {
    try {
      await this.instance.delete(`/api/ideas/${id}`);
    } catch (error) {
      console.error('Delete idea error:', error);
      throw error;
    }
  }

  // Tasks API
  static async getTasks(): Promise<Task[]> {
    try {
      const response: AxiosResponse<Task[]> = await this.instance.get('/api/tasks');
      return response.data.map(task => ({
        ...task,
        dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
      }));
    } catch (error) {
      console.error('Get tasks error:', error);
      throw error;
    }
  }

  static async createTask(task: Task): Promise<Task> {
    try {
      const response: AxiosResponse<Task> = await this.instance.post('/api/tasks', task);
      return {
        ...response.data,
        dueDate: response.data.dueDate ? new Date(response.data.dueDate) : undefined,
      };
    } catch (error) {
      console.error('Create task error:', error);
      throw error;
    }
  }

  static async updateTask(id: string, updates: Partial<Task>): Promise<Task> {
    try {
      const response: AxiosResponse<Task> = await this.instance.put(`/api/tasks/${id}`, updates);
      return {
        ...response.data,
        dueDate: response.data.dueDate ? new Date(response.data.dueDate) : undefined,
      };
    } catch (error) {
      console.error('Update task error:', error);
      throw error;
    }
  }

  static async deleteTask(id: string): Promise<void> {
    try {
      await this.instance.delete(`/api/tasks/${id}`);
    } catch (error) {
      console.error('Delete task error:', error);
      throw error;
    }
  }

  // Conversations API
  static async getConversations(): Promise<Conversation[]> {
    try {
      const response: AxiosResponse<Conversation[]> = await this.instance.get('/api/conversations');
      return response.data.map(conv => ({
        ...conv,
        timestamp: new Date(conv.timestamp),
      }));
    } catch (error) {
      console.error('Get conversations error:', error);
      throw error;
    }
  }

  static async createConversation(message: string): Promise<{conversationId: string; response: string}> {
    try {
      const response = await this.instance.post('/api/conversations', {message});
      return response.data;
    } catch (error) {
      console.error('Create conversation error:', error);
      throw error;
    }
  }

  static async sendMessage(conversationId: string, message: string): Promise<string> {
    try {
      const response = await this.instance.post(`/api/conversations/${conversationId}/messages`, {message});
      return response.data.response;
    } catch (error) {
      console.error('Send message error:', error);
      throw error;
    }
  }

  // Dashboard API
  static async getDashboardData(): Promise<{
    stats: {
      ideasCount: number;
      tasksCount: number;
      completedTasksCount: number;
    };
    recentIdeas: Idea[];
    recentTasks: Task[];
  }> {
    try {
      const response = await this.instance.get('/api/dashboard');
      return {
        ...response.data,
        recentIdeas: response.data.recentIdeas.map((idea: any) => ({
          ...idea,
          timestamp: new Date(idea.timestamp),
        })),
        recentTasks: response.data.recentTasks.map((task: any) => ({
          ...task,
          dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
        })),
      };
    } catch (error) {
      console.error('Get dashboard data error:', error);
      throw error;
    }
  }

  // Sync API
  static async syncData(data: {
    ideas: Idea[];
    tasks: Task[];
    lastSyncTime?: Date;
  }): Promise<{
    ideas: Idea[];
    tasks: Task[];
    syncTime: Date;
  }> {
    try {
      const response = await this.instance.post('/api/sync', {
        ...data,
        lastSyncTime: data.lastSyncTime?.toISOString(),
      });
      
      return {
        ideas: response.data.ideas.map((idea: any) => ({
          ...idea,
          timestamp: new Date(idea.timestamp),
        })),
        tasks: response.data.tasks.map((task: any) => ({
          ...task,
          dueDate: task.dueDate ? new Date(task.dueDate) : undefined,
        })),
        syncTime: new Date(response.data.syncTime),
      };
    } catch (error) {
      console.error('Sync data error:', error);
      throw error;
    }
  }

  // Health check
  static async healthCheck(): Promise<boolean> {
    try {
      const response = await this.instance.get('/api/health');
      return response.status === 200;
    } catch (error) {
      console.error('Health check error:', error);
      return false;
    }
  }

  // Get server status
  static async getServerStatus(): Promise<{
    status: 'online' | 'offline';
    version?: string;
    uptime?: number;
  }> {
    try {
      const response = await this.instance.get('/api/status');
      return response.data;
    } catch (error) {
      console.error('Get server status error:', error);
      return {status: 'offline'};
    }
  }
}

export default ApiService;