import { useState, useEffect, useCallback } from 'react';
import { testConnection } from '@/lib/api';

interface ConnectionStatus {
  isOnline: boolean;
  isApiHealthy: boolean;
  latency?: number;
  lastChecked?: Date;
  error?: string;
}

export const useConnectionStatus = (checkInterval: number = 30000) => {
  const [status, setStatus] = useState<ConnectionStatus>({
    isOnline: navigator.onLine,
    isApiHealthy: false,
  });

  const checkConnection = useCallback(async () => {
    const result = await testConnection();
    setStatus(prev => ({
      ...prev,
      isApiHealthy: result.healthy,
      latency: result.latency,
      lastChecked: new Date(),
      error: result.error,
    }));
  }, []);

  const handleOnline = useCallback(() => {
    setStatus(prev => ({ ...prev, isOnline: true }));
    checkConnection();
  }, [checkConnection]);

  const handleOffline = useCallback(() => {
    setStatus(prev => ({ 
      ...prev, 
      isOnline: false, 
      isApiHealthy: false,
      error: 'No internet connection'
    }));
  }, []);

  useEffect(() => {
    // Initial check
    if (navigator.onLine) {
      checkConnection();
    }

    // Set up periodic checks
    const interval = setInterval(() => {
      if (navigator.onLine) {
        checkConnection();
      }
    }, checkInterval);

    // Listen for online/offline events
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [checkConnection, checkInterval, handleOnline, handleOffline]);

  return {
    ...status,
    checkConnection,
  };
};