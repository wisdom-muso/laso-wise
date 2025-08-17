import { api, endpoints } from './api';
import toast from 'react-hot-toast';

// Enhanced API utility with better error handling
export const apiJson = async (url: string, options: any = {}) => {
  try {
    const method = options.method || 'GET';
    const config = {
      method,
      url,
      ...options,
    };

    if (method !== 'GET' && options.data) {
      config.data = options.data;
    }

    const response = await api(config);
    return response;
  } catch (error: any) {
    console.error(`API Error [${options.method || 'GET'}] ${url}:`, error);
    
    // Handle specific error scenarios
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          toast.error(data?.message || 'Invalid request. Please check your input.');
          break;
        case 401:
          toast.error('Authentication required. Please log in again.');
          break;
        case 403:
          toast.error('Permission denied. You don\'t have access to this resource.');
          break;
        case 404:
          toast.error('Resource not found.');
          break;
        case 429:
          toast.error('Too many requests. Please try again later.');
          break;
        case 500:
          toast.error('Server error. Please try again later.');
          break;
        default:
          toast.error(data?.message || 'An unexpected error occurred.');
      }
    } else if (error.code === 'NETWORK_ERROR') {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred.');
    }
    
    throw error;
  }
};

// Authentication-specific API calls with better error handling
export const authAPI = {
  async login(credentials: { email: string; password: string }) {
    try {
      const response = await apiJson(endpoints.login, {
        method: 'POST',
        data: credentials
      });
      
      if (response.token) {
        localStorage.setItem('authToken', response.token);
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
        }
        toast.success('Login successful!');
      }
      
      return response;
    } catch (error: any) {
      // Login-specific error handling
      if (error.response?.status === 401) {
        toast.error('Invalid email or password');
      }
      throw error;
    }
  },

  async register(userData: any) {
    try {
      const response = await apiJson(endpoints.register, {
        method: 'POST',
        data: userData
      });
      
      if (response.token) {
        localStorage.setItem('authToken', response.token);
        if (response.user) {
          localStorage.setItem('user', JSON.stringify(response.user));
        }
        toast.success('Registration successful!');
      }
      
      return response;
    } catch (error: any) {
      // Registration-specific error handling
      const message = error.response?.data?.message || 'Registration failed';
      toast.error(message);
      throw error;
    }
  },

  async logout() {
    try {
      await apiJson(endpoints.logout, { method: 'POST' });
      toast.success('Logged out successfully');
    } catch (error) {
      console.warn('Logout request failed, but clearing local storage anyway');
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  },

  async getCurrentUser() {
    try {
      return await apiJson(endpoints.me);
    } catch (error: any) {
      if (error.response?.status === 401) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        throw new Error('Authentication expired');
      }
      throw error;
    }
  },

  async updateProfile(data: any) {
    try {
      const response = await apiJson(endpoints.updateProfile, {
        method: 'POST',
        data
      });
      toast.success('Profile updated successfully!');
      return response;
    } catch (error: any) {
      const message = error.response?.data?.message || 'Profile update failed';
      toast.error(message);
      throw error;
    }
  }
};

// Token validation with better error handling
export const validateToken = async (token: string): Promise<boolean> => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8005'}${endpoints.me}`, {
      method: 'GET',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    
    return response.ok;
  } catch (error) {
    console.warn('Token validation failed:', error);
    return false;
  }
};

// Network connectivity check
export const checkNetworkConnectivity = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8005'}/api/health/`, {
      method: 'GET',
      timeout: 5000 as any,
    });
    return response.ok;
  } catch (error) {
    return false;
  }
};

// Safe API call wrapper that handles offline scenarios
export const safeApiCall = async <T>(
  apiCall: () => Promise<T>,
  fallbackValue?: T,
  showErrorToast = true
): Promise<T | null> => {
  try {
    return await apiCall();
  } catch (error: any) {
    console.error('API call failed:', error);
    
    if (showErrorToast) {
      if (error.code === 'NETWORK_ERROR') {
        toast.error('Network error. Please check your connection.');
      } else if (!navigator.onLine) {
        toast.error('You are offline. Please check your internet connection.');
      }
    }
    
    return fallbackValue || null;
  }
};

export default apiJson;