import { useState, useEffect, createContext, useContext } from 'react';
import { api, endpoints } from '../lib/api';
import toast from 'react-hot-toast';

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
    age?: number;
    gender?: string;
    city?: string;
    specialization?: string;
    experience?: number;
    price_per_consultation?: number;
  };
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  register: (userData: any) => Promise<boolean>;
  updateProfile: (data: any) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get(endpoints.me);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      localStorage.removeItem('authToken');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.post(endpoints.login, { email, password });
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
      }
      
      await fetchUser();
      toast.success('Login successful!');
      return true;
    } catch (error: any) {
      console.error('Login error:', error);
      const message = error.response?.data?.message || 'Login failed. Please try again.';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: any): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.post(endpoints.register, userData);
      
      if (response.data.token) {
        localStorage.setItem('authToken', response.data.token);
      }
      
      await fetchUser();
      toast.success('Registration successful!');
      return true;
    } catch (error: any) {
      console.error('Registration error:', error);
      const message = error.response?.data?.message || 'Registration failed. Please try again.';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post(endpoints.logout);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      setUser(null);
      toast.success('Logged out successfully');
    }
  };

  const updateProfile = async (data: any): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.put(endpoints.updateProfile, data);
      setUser(response.data);
      toast.success('Profile updated successfully!');
      return true;
    } catch (error: any) {
      console.error('Profile update error:', error);
      const message = error.response?.data?.message || 'Profile update failed.';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    login,
    logout,
    register,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
