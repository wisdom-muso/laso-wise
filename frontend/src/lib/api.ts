import axios, { AxiosResponse, AxiosError } from 'axios';

// Get API base URL from environment variable, with fallback for Docker development
const getApiBaseUrl = () => {
  // In production, use the environment variable
  if (import.meta.env.VITE_API_BASE) {
    return import.meta.env.VITE_API_BASE;
  }
  
  // In development, check if we're running in Docker
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8005';
  }
  
  // For production without explicit config, use current origin
  return window.location.origin;
};

const API_BASE_URL = getApiBaseUrl();

// Create axios instance with default configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for CSRF
});

// Request retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Function to wait for a specified delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// CSRF token cache to avoid repeated requests
let csrfTokenCache: string | null = null;
let csrfTokenExpiry = 0;

// Function to get CSRF token with caching
const getCSRFToken = async (): Promise<string | null> => {
  const now = Date.now();
  
  // Return cached token if still valid (cache for 30 minutes)
  if (csrfTokenCache && now < csrfTokenExpiry) {
    return csrfTokenCache;
  }
  
  try {
    const csrfResponse = await axios.get(`${API_BASE_URL}/api/csrf/`, {
      withCredentials: true,
      timeout: 5000,
    });
    
    if (csrfResponse.data?.csrfToken) {
      csrfTokenCache = csrfResponse.data.csrfToken;
      csrfTokenExpiry = now + (30 * 60 * 1000); // 30 minutes
      return csrfTokenCache;
    }
  } catch (error) {
    console.warn('Could not fetch CSRF token:', error);
  }
  
  return null;
};

// Add request interceptor to include auth token and CSRF token
api.interceptors.request.use(
  async (config) => {
    // Get auth token from localStorage
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    
    // Get CSRF token for Django (with caching)
    const csrfToken = await getCSRFToken();
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling and retries
api.interceptors.response.use(
  (response) => response.data,
  async (error: AxiosError) => {
    const config = error.config as any;
    
    // Don't retry authentication endpoints to avoid infinite loops
    const isAuthEndpoint = config?.url?.includes('/accounts/api/');
    
    // Don't retry if we've already exceeded max retries
    if (!config || config.__retryCount >= MAX_RETRIES || isAuthEndpoint) {
      if (error.response?.status === 401) {
        // Clear authentication state
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login' && !isAuthEndpoint) {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
    
    // Increment retry count
    config.__retryCount = config.__retryCount || 0;
    config.__retryCount += 1;
    
    // Retry on network errors, timeouts, or 5xx errors
    if (
      !error.response || 
      (error.response.status >= 500 && error.response.status <= 599) ||
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED' ||
      error.code === 'TIMEOUT'
    ) {
      console.log(`Retrying request (${config.__retryCount}/${MAX_RETRIES}): ${config.url}`);
      await delay(RETRY_DELAY * config.__retryCount);
      
      // For CSRF errors, clear the cache and retry
      if (error.response?.status === 403) {
        csrfTokenCache = null;
        csrfTokenExpiry = 0;
      }
      
      return api(config);
    }
    
    // Handle specific error codes
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login' && !isAuthEndpoint) {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      console.error('Permission denied:', error.response.data);
      // Clear CSRF token cache in case it's a CSRF issue
      csrfTokenCache = null;
      csrfTokenExpiry = 0;
    } else if (error.response?.status === 404) {
      console.error('Resource not found:', error.config?.url);
    } else if (error.response?.status === 429) {
      console.warn('Rate limited. Please try again later.');
    }
    
    return Promise.reject(error);
  }
);

// API endpoints matching Django URL patterns
export const endpoints = {
  // Authentication
  login: '/accounts/api/login/',
  logout: '/accounts/api/logout/',
  register: '/accounts/api/register/',
  me: '/accounts/api/me/',
  csrf: '/api/csrf/',
  
  // User profile
  updateProfile: '/accounts/api/me/update/',
  
  // Appointments/Bookings
  appointments: '/api/bookings/',
  createAppointment: '/api/bookings/create/',
  
  // Doctors
  doctors: '/api/doctors/',
  doctorDetail: (id: number) => `/api/doctors/${id}/`,
  doctorSchedule: (id: number) => `/api/doctors/${id}/schedule/`,
  
  // Patients
  patients: '/api/patients/',
  patientDetail: (id: number) => `/api/patients/${id}/`,
  
  // Consultations (Telemedicine)
  consultations: '/api/consultations/',
  createConsultation: '/api/consultations/create/',
  consultationDetail: (id: string) => `/api/consultations/${id}/`,
  joinConsultation: (id: string) => `/api/consultations/${id}/join/`,
  
  // Vitals
  vitals: '/api/vitals/',
  vitalCategories: '/api/vitals/categories/',
  createVital: '/api/vitals/create/',
  
  // Dashboard
  dashboard: '/api/dashboard/',
  stats: '/api/dashboard/stats/',
};

// Auth helper functions
export const authAPI = {
  login: async (credentials: { username: string; password: string }) => {
    try {
      const response = await api.post(endpoints.login, credentials);
      if (response.token) {
        localStorage.setItem('authToken', response.token);
        localStorage.setItem('user', JSON.stringify(response.user));
      }
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post(endpoints.logout);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
  },

  register: async (userData: {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
  }) => {
    try {
      const response = await api.post(endpoints.register, userData);
      if (response.token) {
        localStorage.setItem('authToken', response.token);
        localStorage.setItem('user', JSON.stringify(response.user));
      }
      return response;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  getCurrentUser: async () => {
    try {
      return await api.get(endpoints.me);
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },
};

// WebSocket URL helper
export const getWebSocketURL = (path: string): string => {
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const wsBase = API_BASE_URL.replace(/^https?/, wsProtocol);
  return `${wsBase}${path}`;
};

// API Health Check
export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/health/`, {
      timeout: 5000,
      validateStatus: (status) => status < 500,
    });
    return true;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};

// Connection test function
export const testConnection = async (): Promise<{
  healthy: boolean;
  latency?: number;
  error?: string;
}> => {
  const startTime = Date.now();
  try {
    await healthCheck();
    const latency = Date.now() - startTime;
    return { healthy: true, latency };
  } catch (error: any) {
    return {
      healthy: false,
      error: error.message || 'Connection failed',
    };
  }
};

// Token validation helper
export const validateToken = async (token: string): Promise<boolean> => {
  try {
    const response = await axios.get(`${API_BASE_URL}${endpoints.me}`, {
      headers: {
        Authorization: `Token ${token}`,
      },
      timeout: 5000,
    });
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export default api;