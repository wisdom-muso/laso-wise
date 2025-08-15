import axios, { AxiosResponse, AxiosError } from 'axios';

// Get API base URL from environment variable, fallback to production backend port
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://65.108.91.110:12000';

// Create axios instance with default configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Increased timeout for better reliability
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for CORS
});

// Request retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Function to wait for a specified delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    
    // Add CSRF token if available
    const csrfToken = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.getAttribute('content');
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
    
    // Don't retry if we've already exceeded max retries
    if (!config || config.__retryCount >= MAX_RETRIES) {
      if (error.response?.status === 401) {
        localStorage.removeItem('authToken');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
    
    // Increment retry count
    config.__retryCount = config.__retryCount || 0;
    config.__retryCount += 1;
    
    // Retry on network errors or 5xx errors
    if (
      !error.response || 
      (error.response.status >= 500 && error.response.status <= 599) ||
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED'
    ) {
      console.log(`Retrying request (${config.__retryCount}/${MAX_RETRIES}): ${config.url}`);
      await delay(RETRY_DELAY * config.__retryCount);
      return api(config);
    }
    
    // Handle specific error codes
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    } else if (error.response?.status === 403) {
      console.error('Permission denied:', error.response.data);
    } else if (error.response?.status === 404) {
      console.error('Resource not found:', error.config?.url);
    }
    
    return Promise.reject(error);
  }
);

// For multipart/form-data requests
export const apiJson = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

apiJson.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    
    // Add CSRF token if available
    const csrfToken = document.querySelector<HTMLMetaElement>('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    console.error('apiJson request interceptor error:', error);
    return Promise.reject(error);
  }
);

apiJson.interceptors.response.use(
  (response) => response.data,
  async (error: AxiosError) => {
    const config = error.config as any;
    
    // Same retry logic as main api instance
    if (!config || config.__retryCount >= MAX_RETRIES) {
      if (error.response?.status === 401) {
        localStorage.removeItem('authToken');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      return Promise.reject(error);
    }
    
    config.__retryCount = config.__retryCount || 0;
    config.__retryCount += 1;
    
    if (
      !error.response || 
      (error.response.status >= 500 && error.response.status <= 599) ||
      error.code === 'NETWORK_ERROR' ||
      error.code === 'ECONNABORTED'
    ) {
      console.log(`Retrying apiJson request (${config.__retryCount}/${MAX_RETRIES}): ${config.url}`);
      await delay(RETRY_DELAY * config.__retryCount);
      return apiJson(config);
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Authentication (based on actual Django URLs)
  login: '/accounts/api/login/',
  logout: '/accounts/api/logout/',
  register: '/accounts/api/register/',
  me: '/accounts/api/me/',
  updateProfile: '/accounts/api/me/update/',
  
  // Appointments
  appointments: '/bookings/api/appointments/',
  bookingConsultations: '/bookings/api/appointments/',
  
  // Doctors
  doctors: '/doctors/api/',
  doctorSchedule: '/doctors/api/schedule/',
  
  // Consultations
  consultations: '/telemedicine/api/consultations/',
  
  // Vitals
  vitals: '/vitals/api/records/',
  
  // Patients
  patients: '/patients/api/',
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
    // Try a simple endpoint that doesn't require authentication
    const response = await axios.get(`${API_BASE_URL}/admin/`, {
      timeout: 5000,
      validateStatus: (status) => status < 500, // Accept any status < 500 as "healthy"
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