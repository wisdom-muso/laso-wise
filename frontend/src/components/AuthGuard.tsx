import React, { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { Navigate, useLocation } from 'react-router-dom';
import { Spinner } from './ui/spinner';

interface AuthGuardProps {
  children: React.ReactNode;
  requiredRole?: 'patient' | 'doctor' | 'admin';
  fallbackPath?: string;
}

export const AuthGuard: React.FC<AuthGuardProps> = ({ 
  children, 
  requiredRole, 
  fallbackPath = '/login' 
}) => {
  const { user, loading, isAuthenticated, checkAuth } = useAuth();
  const location = useLocation();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      if (!isAuthenticated && localStorage.getItem('authToken')) {
        // Try to validate the token if we have one but aren't authenticated
        await checkAuth();
      }
      setChecking(false);
    };

    verifyAuth();
  }, [isAuthenticated, checkAuth]);

  // Show loading spinner while checking authentication
  if (loading || checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Spinner size="lg" />
          <p className="mt-4 text-gray-600">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRole && user.role !== requiredRole) {
    // Redirect based on user's actual role
    const redirectPath = user.role === 'doctor' ? '/doctors/dashboard' : '/patients/dashboard';
    return <Navigate to={redirectPath} replace />;
  }

  return <>{children}</>;
};

export default AuthGuard;