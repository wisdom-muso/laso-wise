import { useState, useEffect, useRef, useCallback } from 'react';
import { api, endpoints, getWebSocketURL } from '../lib/api';
import toast from 'react-hot-toast';

export interface Consultation {
  id: string;
  booking?: number;
  doctor: number;
  patient: number;
  doctor_name: string;
  patient_name: string;
  appointment_date?: string;
  appointment_time?: string;
  video_provider: 'jitsi' | 'zoom' | 'google_meet';
  meeting_id: string;
  meeting_url: string;
  meeting_password?: string;
  status: 'scheduled' | 'waiting' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';
  scheduled_start: string;
  actual_start?: string;
  actual_end?: string;
  duration_minutes?: number;
  recording_enabled: boolean;
  recording_url?: string;
  connection_quality?: 'excellent' | 'good' | 'fair' | 'poor';
  notes?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  can_start: boolean;
  meeting_info?: any;
}

export interface ConsultationMessage {
  id: number;
  consultation: string;
  sender: number;
  message: string;
  message_type: 'text' | 'system' | 'file' | 'prescription';
  timestamp: string;
  is_private: boolean;
  sender_name: string;
  sender_role: string;
}

export interface ConsultationParticipant {
  id: number;
  consultation: string;
  user: number;
  role: 'doctor' | 'patient' | 'observer' | 'assistant';
  joined_at?: string;
  left_at?: string;
  connection_issues: number;
  user_name: string;
}

export interface ConsultationStats {
  total_consultations: number;
  completed_consultations: number;
  upcoming_consultations: number;
  active_consultations: number;
  average_duration: number;
  total_duration: number;
  by_provider: Record<string, number>;
  by_status: Record<string, number>;
}

export interface VideoProvider {
  provider: string;
  display_name: string;
  is_active: boolean;
  available: boolean;
  features: Record<string, boolean>;
  error?: string;
}

export interface TechnicalIssue {
  id: number;
  consultation: string;
  reporter: number;
  issue_type: 'audio' | 'video' | 'connection' | 'screen_share' | 'recording' | 'other';
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  resolved: boolean;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
  reporter_name: string;
}

export interface ConsultationRecording {
  id: number;
  consultation: string;
  recording_id: string;
  recording_url: string;
  download_url?: string;
  file_size_mb?: number;
  duration_seconds?: number;
  expires_at?: string;
  is_processed: boolean;
  is_available: boolean;
  created_at: string;
}

export interface WebSocketMessage {
  type: string;
  consultation_id: string;
  [key: string]: any;
}

export const useConsultations = () => {
  // State
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [currentConsultation, setCurrentConsultation] = useState<Consultation | null>(null);
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [participants, setParticipants] = useState<ConsultationParticipant[]>([]);
  const [technicalIssues, setTechnicalIssues] = useState<TechnicalIssue[]>([]);
  const [recordings, setRecordings] = useState<ConsultationRecording[]>([]);
  const [videoProviders, setVideoProviders] = useState<Record<string, VideoProvider>>({});
  const [stats, setStats] = useState<ConsultationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // WebSocket
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const maxReconnectAttempts = 5;

  // Enhanced API functions
  const fetchConsultations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoints.consultations);
      setConsultations(response.results || response);
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch consultations';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConsultationById = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`${endpoints.consultations}${id}/`);
      setCurrentConsultation(response);
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const createConsultation = useCallback(async (data: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(endpoints.consultations, data);
      setConsultations(prev => [response, ...prev]);
      toast.success('Consultation created successfully');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const createConsultationFromBooking = useCallback(async (bookingId: number, data: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`${endpoints.bookingConsultations}${bookingId}/create-consultation/`, data);
      toast.success('Virtual consultation created from appointment');
      await fetchConsultations(); // Refresh list
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create consultation from booking';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchConsultations]);

  const startConsultation = useCallback(async (consultationId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/start/`);
      setCurrentConsultation(response);
      toast.success('Consultation started');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to start consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const endConsultation = useCallback(async (consultationId: string, notes?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/end/`, { notes });
      setCurrentConsultation(response);
      toast.success('Consultation ended');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to end consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const joinConsultation = useCallback(async (consultationId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/join/`);
      toast.success('Joined consultation');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to join consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const leaveConsultation = useCallback(async (consultationId: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/leave/`);
      toast.success('Left consultation');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to leave consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchVideoProviders = useCallback(async () => {
    try {
      const response = await api.get(endpoints.videoProviders);
      const providers = response.reduce((acc: any, provider: VideoProvider) => {
        acc[provider.provider] = provider;
        return acc;
      }, {});
      setVideoProviders(providers);
      return providers;
    } catch (error: any) {
      console.error('Failed to fetch video providers:', error);
      return {};
    }
  }, []);

  const fetchConsultationStats = useCallback(async () => {
    try {
      const response = await api.get(`${endpoints.consultations}stats/`);
      setStats(response);
      return response;
    } catch (error: any) {
      console.error('Failed to fetch consultation stats:', error);
      return null;
    }
  }, []);

  const fetchTechnicalIssues = useCallback(async (consultationId?: string) => {
    try {
      const url = consultationId 
        ? `${endpoints.technicalIssues}?consultation=${consultationId}`
        : endpoints.technicalIssues;
      const response = await api.get(url);
      setTechnicalIssues(response.results || response);
      return response;
    } catch (error: any) {
      console.error('Failed to fetch technical issues:', error);
      return [];
    }
  }, []);

  const reportTechnicalIssue = useCallback(async (data: any) => {
    setError(null);
    try {
      const response = await api.post(endpoints.technicalIssues, data);
      setTechnicalIssues(prev => [response, ...prev]);
      toast.success('Technical issue reported');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to report technical issue';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    }
  }, []);

  const fetchRecordings = useCallback(async (consultationId?: string) => {
    try {
      const url = consultationId 
        ? `${endpoints.consultationRecordings}?consultation=${consultationId}`
        : endpoints.consultationRecordings;
      const response = await api.get(url);
      setRecordings(response.results || response);
      return response;
    } catch (error: any) {
      console.error('Failed to fetch recordings:', error);
      return [];
    }
  }, []);

  // WebSocket functions
  const connectWebSocket = useCallback((consultationId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close();
    }

    const wsUrl = getWebSocketURL(`/ws/consultation/${consultationId}/`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setReconnectAttempts(0);
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket(consultationId);
          }, Math.pow(2, reconnectAttempts) * 1000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }, [reconnectAttempts]);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setReconnectAttempts(0);
  }, []);

  const sendWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'chat_message':
        setMessages(prev => [...prev, data.message]);
        break;
      case 'user_joined':
        setParticipants(prev => [...prev, data.participant]);
        toast(`${data.user_name} joined the consultation`);
        break;
      case 'user_left':
        setParticipants(prev => prev.filter(p => p.user !== data.user_id));
        toast(`${data.user_name} left the consultation`);
        break;
      case 'consultation_started':
        if (currentConsultation) {
          setCurrentConsultation({
            ...currentConsultation,
            status: 'in_progress',
            actual_start: data.actual_start
          });
        }
        toast.success('Consultation started');
        break;
      case 'consultation_ended':
        if (currentConsultation) {
          setCurrentConsultation({
            ...currentConsultation,
            status: 'completed',
            actual_end: data.actual_end
          });
        }
        toast(`Consultation ended by ${data.ended_by}`);
        break;
      case 'technical_issue':
        toast.error(`Technical issue reported: ${data.issue_type}`);
        break;
      case 'recording_started':
        toast.success('Recording started');
        break;
      case 'recording_stopped':
        toast.success('Recording stopped');
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  }, [currentConsultation]);

  // Cleanup
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    // State
    consultations,
    currentConsultation,
    messages,
    participants,
    technicalIssues,
    recordings,
    videoProviders,
    stats,
    loading,
    error,
    isConnected,

    // Actions
    fetchConsultations,
    fetchConsultationById,
    createConsultation,
    createConsultationFromBooking,
    startConsultation,
    endConsultation,
    joinConsultation,
    leaveConsultation,
    fetchVideoProviders,
    fetchConsultationStats,
    fetchTechnicalIssues,
    reportTechnicalIssue,
    fetchRecordings,

    // WebSocket
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,

    // Helper methods
    setCurrentConsultation,
    setMessages,
    setParticipants,
  };
};