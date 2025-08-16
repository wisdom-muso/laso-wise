import { useState, useEffect, createContext, useContext } from 'react';
import { api, endpoints } from '../lib/api';
import { authAPI, validateToken } from '../lib/apiUtils';
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
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  register: (userData: any) => Promise<boolean>;
  updateProfile: (data: any) => Promise<boolean>;
  checkAuth: () => Promise<boolean>;
  refreshToken: () => Promise<boolean>;
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
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    fetchUser();
    
    // Set up periodic token validation (every 30 minutes)
    const interval = setInterval(() => {
      if (user && localStorage.getItem('authToken')) {
        checkAuth();
      }
    }, 30 * 60 * 1000);

    return () => clearInterval(interval);
  }, [user]);

  const fetchUser = async () => {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
      setLoading(false);
      setIsAuthenticated(false);
      return;
    }
    
    try {
      // Validate token first
      const isValid = await validateToken(token);
      if (!isValid) {
        localStorage.removeItem('authToken');
        setUser(null);
        setIsAuthenticated(false);
        setLoading(false);
        return;
      }
      
      const response = await api.get(endpoints.me);
      setUser(response);
      setIsAuthenticated(true);
    } catch (error: any) {
      console.error('Error fetching user:', error);
      
      // If it's an authentication error, clear the token
      if (error.response?.status === 401) {
        localStorage.removeItem('authToken');
        setUser(null);
        setIsAuthenticated(false);
      } else {
        // For other errors, show user-friendly message
        toast.error('Failed to load user profile. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const checkAuth = async (): Promise<boolean> => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      setIsAuthenticated(false);
      return false;
    }

    try {
      const isValid = await validateToken(token);
      setIsAuthenticated(isValid);
      if (!isValid) {
        localStorage.removeItem('authToken');
        setUser(null);
      }
      return isValid;
    } catch (error) {
      console.error('Token validation failed:', error);
      setIsAuthenticated(false);
      return false;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    // Note: Django's Token authentication doesn't typically have refresh tokens
    // This would be for JWT if implemented
    try {
      // For now, just validate the current token
      const isValid = await checkAuth();
      if (isValid) {
        await fetchUser();
      }
      return isValid;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  };

  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Clear any existing token first
      localStorage.removeItem('authToken');
      
      const response = await authAPI.login({ email, password });
      
      if (response.token) {
        // Set user data immediately if available in response
        if (response.user) {
          setUser(response.user);
          setIsAuthenticated(true);
        } else {
          // Fetch user data if not in response
          await fetchUser();
        }
        
        return true;
      } else {
        toast.error('Invalid response from server');
        return false;
      }
    } catch (error: any) {
      console.error('Login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData: any): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await authAPI.register(userData);
      
      if (response.user) {
        setUser(response.user);
        setIsAuthenticated(true);
      } else {
        await fetchUser();
      }
      
      return true;
    } catch (error: any) {
      console.error('Registration error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const updateProfile = async (data: any): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await authAPI.updateProfile(data);
      if (response) {
        setUser(response);
      }
      return true;
    } catch (error: any) {
      console.error('Profile update error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    register,
    updateProfile,
    checkAuth,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
