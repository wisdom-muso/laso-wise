#!/bin/bash

echo "🔧 Fixing React Frontend Issues..."

# 1. Install dependencies
echo "📦 Installing dependencies..."
npm install

# 2. Check for TypeScript errors
echo "🔍 Checking TypeScript errors..."
npx tsc --noEmit

# 3. Create missing directories if they don't exist
echo "📁 Creating missing directories..."
mkdir -p src/modules/patient
mkdir -p src/modules/doctor
mkdir -p src/modules/mobile-clinic
mkdir -p src/hooks
mkdir -p src/contexts
mkdir -p src/types

# 4. Create basic API configuration
echo "⚙️ Creating API configuration..."
cat > src/lib/api.ts << 'EOF'
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
EOF

# 5. Create basic auth hook
echo "🔐 Creating auth hook..."
cat > src/hooks/useAuth.ts << 'EOF'
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'patient' | 'doctor' | 'admin';
  profile?: {
    phone?: string;
    avatar?: string;
  };
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get('/accounts/api/me/');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('authToken');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await api.post('/accounts/login/', { email, password });
    const { token } = response.data;
    localStorage.setItem('authToken', token);
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return { user, loading, login, logout, fetchUser };
};
EOF

# 6. Create basic appointment hook
echo "📅 Creating appointment hook..."
cat > src/hooks/useAppointments.ts << 'EOF'
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

interface Appointment {
  id: number;
  doctor: {
    id: number;
    first_name: string;
    last_name: string;
    profile: {
      specialization: string;
      price_per_consultation: number;
    };
  };
  patient: {
    id: number;
    first_name: string;
    last_name: string;
  };
  appointment_date: string;
  appointment_time: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  created_at: string;
}

export const useAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/bookings/api/');
      setAppointments(response.data);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const createAppointment = async (appointmentData: any) => {
    try {
      const response = await api.post('/bookings/api/', appointmentData);
      await fetchAppointments();
      return response.data;
    } catch (error) {
      console.error('Error creating appointment:', error);
      throw error;
    }
  };

  return { appointments, loading, fetchAppointments, createAppointment };
};
EOF

# 7. Create basic mobile clinic hook
echo "🚑 Creating mobile clinic hook..."
cat > src/hooks/useMobileClinic.ts << 'EOF'
import { useState, useEffect } from 'react';
import { api } from '../lib/api';

interface MobileClinicRequest {
  id: number;
  patient: {
    id: number;
    first_name: string;
    last_name: string;
  };
  requested_date: string;
  requested_time: string;
  address: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  created_at: string;
}

export const useMobileClinic = () => {
  const [requests, setRequests] = useState<MobileClinicRequest[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const response = await api.get('/mobile-clinic/api/');
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching mobile clinic requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const createRequest = async (requestData: any) => {
    try {
      const response = await api.post('/mobile-clinic/api/', requestData);
      await fetchRequests();
      return response.data;
    } catch (error) {
      console.error('Error creating mobile clinic request:', error);
      throw error;
    }
  };

  return { requests, loading, fetchRequests, createRequest };
};
EOF

# 8. Create environment file
echo "🌍 Creating environment file..."
cat > .env.example << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=LASO Health
EOF

# 9. Update package.json scripts
echo "📝 Updating package.json scripts..."
npm pkg set scripts.lint="eslint src --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
npm pkg set scripts.lint:fix="eslint src --ext ts,tsx --fix"

echo "✅ Frontend fixes completed!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and update API URL"
echo "2. Run 'npm run dev' to start development server"
echo "3. Create missing page components as needed"
echo "4. Test all user flows"
echo ""
echo "📋 See FRONTEND_AUDIT_FIXES.md for detailed audit report"
