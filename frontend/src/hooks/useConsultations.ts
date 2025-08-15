import { useState, useEffect, useRef, useCallback } from 'react';
import { api, endpoints, getWebSocketURL } from '../lib/api';
import toast from 'react-hot-toast';

export interface Consultation {
  id: string;
  booking_id?: number;
  doctor_name: string;
  patient_name: string;
  appointment_date?: string;
  appointment_time?: string;
  video_provider: 'jitsi' | 'zoom' | 'google_meet';
  meeting_id: string;
  meeting_url: string;
  meeting_password?: string;
  status: 'scheduled' | 'waiting' | 'in_progress' | 'completed' | 'cancelled';
  scheduled_start: string;
  actual_start?: string;
  actual_end?: string;
  duration_minutes?: number;
  recording_enabled: boolean;
  recording_url?: string;
  connection_quality?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  can_start: boolean;
  meeting_info?: any;
}

export interface ConsultationMessage {
  id: number;
  message: string;
  message_type: 'text' | 'system' | 'file' | 'prescription';
  timestamp: string;
  is_private: boolean;
  sender_name: string;
  sender_role: string;
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
  name: string;
  display_name: string;
  available: boolean;
  features: Record<string, boolean>;
  error?: string;
}

export interface TechnicalIssue {
  id: number;
  issue_type: string;
  description: string;
  severity: string;
  resolved: boolean;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
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
  const [participants, setParticipants] = useState<any[]>([]);
  const [technicalIssues, setTechnicalIssues] = useState<TechnicalIssue[]>([]);
  const [videoProviders, setVideoProviders] = useState<Record<string, VideoProvider>>({});
  const [stats, setStats] = useState<ConsultationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  // WebSocket
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const maxReconnectAttempts = 5;

  // Fetch consultations
  const fetchConsultations = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get(endpoints.consultations);
      setConsultations(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching consultations:', error);
      toast.error('Failed to load consultations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch consultation details
  const fetchConsultationDetails = useCallback(async (id: string) => {
    try {
      const response = await api.get(endpoints.consultationDetails(id));
      const consultation = response.data;
      setCurrentConsultation(consultation);
      
      // Fetch meeting info
      try {
        const meetingResponse = await api.get(endpoints.consultationDetails(id) + 'meeting_info/');
        consultation.meeting_info = meetingResponse.data;
      } catch (meetingError) {
        console.warn('Failed to fetch meeting info:', meetingError);
      }
      
      return consultation;
    } catch (error) {
      console.error('Error fetching consultation details:', error);
      toast.error('Failed to load consultation details');
      return null;
    }
  }, []);

  // Fetch messages
  const fetchMessages = useCallback(async (consultationId: string) => {
    try {
      const response = await api.get(endpoints.consultationMessages(consultationId));
      setMessages(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  }, []);

  // Fetch video providers
  const fetchVideoProviders = useCallback(async () => {
    try {
      const response = await api.get(endpoints.videoProviders);
      setVideoProviders(response.data);
    } catch (error) {
      console.error('Error fetching video providers:', error);
    }
  }, []);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await api.get(endpoints.getStats);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  // Create consultation
  const createConsultation = useCallback(async (data: any) => {
    setLoading(true);
    try {
      const response = await api.post(endpoints.consultations, data);
      const newConsultation = response.data;
      setConsultations(prev => [newConsultation, ...prev]);
      toast.success('Consultation created successfully!');
      return newConsultation;
    } catch (error: any) {
      console.error('Error creating consultation:', error);
      const message = error.response?.data?.error || 'Failed to create consultation';
      toast.error(message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Start consultation
  const startConsultation = useCallback(async (id: string) => {
    try {
      const response = await api.post(endpoints.startConsultation(id));
      if (currentConsultation?.id === id) {
        setCurrentConsultation(prev => prev ? { ...prev, status: 'in_progress' } : null);
      }
      toast.success('Consultation started!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to start consultation';
      toast.error(message);
      throw error;
    }
  }, [currentConsultation]);

  // End consultation
  const endConsultation = useCallback(async (id: string, notes?: string) => {
    try {
      const response = await api.post(endpoints.endConsultation(id), { notes });
      if (currentConsultation?.id === id) {
        setCurrentConsultation(prev => prev ? { 
          ...prev, 
          status: 'completed',
          notes: notes || prev.notes
        } : null);
      }
      toast.success('Consultation ended!');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to end consultation';
      toast.error(message);
      throw error;
    }
  }, [currentConsultation]);

  // Join waiting room
  const joinWaitingRoom = useCallback(async (id: string) => {
    try {
      const response = await api.post(endpoints.joinWaitingRoom(id));
      if (currentConsultation?.id === id) {
        setCurrentConsultation(prev => prev ? { ...prev, status: 'waiting' } : null);
      }
      toast.success('Joined waiting room');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to join waiting room';
      toast.error(message);
      throw error;
    }
  }, [currentConsultation]);

  // Send message
  const sendMessage = useCallback(async (consultationId: string, messageData: any) => {
    try {
      const response = await api.post(endpoints.sendMessage(consultationId), messageData);
      // Message will be added via WebSocket, so no need to update state here
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to send message';
      toast.error(message);
      throw error;
    }
  }, []);

  // Report technical issue
  const reportTechnicalIssue = useCallback(async (consultationId: string, issueData: any) => {
    try {
      const response = await api.post(endpoints.reportIssue(consultationId), issueData);
      setTechnicalIssues(prev => [response.data, ...prev]);
      toast.success('Technical issue reported');
      return response.data;
    } catch (error: any) {
      const message = error.response?.data?.error || 'Failed to report issue';
      toast.error(message);
      throw error;
    }
  }, []);

  // Update connection quality
  const updateConnectionQuality = useCallback(async (consultationId: string, quality: string) => {
    try {
      const response = await api.post(endpoints.updateConnectionQuality(consultationId), { quality });
      if (currentConsultation?.id === consultationId) {
        setCurrentConsultation(prev => prev ? { 
            ...prev, 
            connection_quality: quality 
          } : null);
      }
      return response.data;
    } catch (error: any) {
      console.error('Error updating connection quality:', error);
      throw error;
    }
  }, [currentConsultation]);

  // WebSocket functions
  const connectWebSocket = useCallback((consultationId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const wsUrl = getWebSocketURL(`/ws/consultation/${consultationId}/`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setReconnectAttempts(0);
        toast.success('Connected to consultation');
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket(consultationId);
          }, 1000 * Math.pow(2, reconnectAttempts)); // Exponential backoff
        } else {
          toast.error('Connection lost. Please refresh the page.');
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        toast.error('Connection error occurred');
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      toast.error('Failed to connect to consultation');
    }
  }, [reconnectAttempts]);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
    setReconnectAttempts(0);
  }, []);

  const sendWebSocketMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      toast.error('Not connected to consultation');
    }
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'user_joined':
        toast.success(`${data.user_name} joined the consultation`);
        break;
      
      case 'user_left':
        toast.info(`${data.user_name} left the consultation`);
        break;
      
      case 'new_message':
        setMessages(prev => [...prev, {
          id: data.message_id,
          message: data.message,
          message_type: data.message_type,
          timestamp: data.timestamp,
          is_private: data.is_private,
          sender_name: data.sender_name,
          sender_role: data.sender_role,
        }]);
        break;
      
      case 'consultation_started':
        setCurrentConsultation(prev => prev ? { ...prev, status: 'in_progress' } : null);
        toast.success(`Consultation started by ${data.started_by}`);
        break;
      
      case 'consultation_ended':
        setCurrentConsultation(prev => prev ? { 
          ...prev, 
          status: 'completed',
          duration_minutes: data.duration_minutes 
        } : null);
        toast.info(`Consultation ended by ${data.ended_by}`);
        break;
      
      case 'technical_issue_reported':
        toast.warning(`Technical issue reported: ${data.issue_type}`);
        break;
      
      case 'connection_quality_updated':
        if (currentConsultation) {
          setCurrentConsultation(prev => prev ? { 
            ...prev, 
            connection_quality: data.quality 
          } : null);
        }
        break;
      
      default:
        console.log('Unhandled WebSocket message:', data);
    }
  }, [currentConsultation]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  // Fetch initial data
  useEffect(() => {
    fetchVideoProviders();
  }, [fetchVideoProviders]);

  return {
    // State
    consultations,
    currentConsultation,
    messages,
    participants,
    technicalIssues,
    videoProviders,
    stats,
    loading,
    isConnected,
    reconnectAttempts,

    // Actions
    fetchConsultations,
    fetchConsultationDetails,
    fetchMessages,
    fetchStats,
    createConsultation,
    startConsultation,
    endConsultation,
    joinWaitingRoom,
    sendMessage,
    reportTechnicalIssue,
    updateConnectionQuality,

    // WebSocket
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
  };
};