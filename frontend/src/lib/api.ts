import axios, { AxiosResponse } from 'axios';

// Get API base URL from environment variable, fallback to production backend port
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'http://65.108.91.110:12000';

// Create axios instance with default configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// For multipart/form-data requests
export const apiJson = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

apiJson.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiJson.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const endpoints = {
  // Authentication
  login: '/accounts/login/',
  logout: '/accounts/logout/',
  register: '/accounts/register/',
  me: '/accounts/me/',
  updateProfile: '/accounts/profile/',
  
  // Appointments
  appointments: '/bookings/appointments/',
  bookingConsultations: '/bookings/appointments/',
  
  // Doctors
  doctors: '/doctors/',
  doctorSchedule: '/doctors/schedule/',
  
  // Consultations
  consultations: '/telemedicine/consultations/',
  
  // Vitals
  vitals: '/vitals/records/',
  
  // Patients
  patients: '/patients/',
};

// WebSocket URL helper
export const getWebSocketURL = (path: string): string => {
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const wsBase = API_BASE_URL.replace(/^https?/, wsProtocol);
  return `${wsBase}${path}`;
};

export default api;