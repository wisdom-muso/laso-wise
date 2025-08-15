import { useState, useEffect, useRef, useCallback } from 'react';
import { api, endpoints } from '../lib/api';
import toast from 'react-hot-toast';

export interface Consultation {
  id: string;
  booking_id: number;
  doctor_name: string;
  patient_name: string;
  appointment_date: string;
  appointment_time: string;
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

export const useConsultations = () => {
  const [consultations, setConsultations] = useState<Consultation[]>([]);
  const [activeConsultation, setActiveConsultation] = useState<Consultation | null>(null);
  const [messages, setMessages] = useState<ConsultationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<string[]>([]);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const fetchConsultations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoints.consultations);
      setConsultations(response.data.results || response.data);
    } catch (error: any) {
      console.error('Error fetching consultations:', error);
      setError(error.response?.data?.message || 'Failed to fetch consultations');
      toast.error('Failed to fetch consultations');
    } finally {
      setLoading(false);
    }
  };

  const fetchUpcomingConsultations = async () => {
    try {
      const response = await api.get(`${endpoints.consultations}upcoming/`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching upcoming consultations:', error);
      throw error;
    }
  };

  const fetchActiveConsultations = async () => {
    try {
      const response = await api.get(`${endpoints.consultations}active/`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching active consultations:', error);
      throw error;
    }
  };

  const fetchConsultationStats = async (): Promise<ConsultationStats> => {
    try {
      const response = await api.get(`${endpoints.consultations}stats/`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching consultation stats:', error);
      throw error;
    }
  };

  const createConsultation = async (bookingId: number, data: {
    video_provider?: string;
    recording_enabled?: boolean;
    notes?: string;
  }) => {
    try {
      setLoading(true);
      const response = await api.post(`/telemedicine/api/bookings/${bookingId}/create-consultation/`, data);
      await fetchConsultations();
      toast.success('Virtual consultation created successfully!');
      return response.data;
    } catch (error: any) {
      console.error('Error creating consultation:', error);
      const message = error.response?.data?.error || 'Failed to create consultation';
      toast.error(message);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const startConsultation = async (consultationId: string) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/start/`);
      await fetchConsultations();
      toast.success('Consultation started successfully!');
      return response.data;
    } catch (error: any) {
      console.error('Error starting consultation:', error);
      const message = error.response?.data?.error || 'Failed to start consultation';
      toast.error(message);
      throw error;
    }
  };

  const endConsultation = async (consultationId: string, notes?: string) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/end/`, {
        notes: notes || ''
      });
      await fetchConsultations();
      toast.success('Consultation ended successfully!');
      return response.data;
    } catch (error: any) {
      console.error('Error ending consultation:', error);
      const message = error.response?.data?.error || 'Failed to end consultation';
      toast.error(message);
      throw error;
    }
  };

  const cancelConsultation = async (consultationId: string, notes?: string) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/cancel/`, {
        notes: notes || ''
      });
      await fetchConsultations();
      toast.success('Consultation cancelled successfully!');
      return response.data;
    } catch (error: any) {
      console.error('Error cancelling consultation:', error);
      const message = error.response?.data?.error || 'Failed to cancel consultation';
      toast.error(message);
      throw error;
    }
  };

  const fetchMessages = async (consultationId: string) => {
    try {
      const response = await api.get(`${endpoints.consultations}${consultationId}/messages/`);
      setMessages(response.data);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching messages:', error);
      throw error;
    }
  };

  const sendMessage = async (consultationId: string, message: string, isPrivate = false) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/send_message/`, {
        message,
        is_private: isPrivate,
        message_type: 'text'
      });
      return response.data;
    } catch (error: any) {
      console.error('Error sending message:', error);
      throw error;
    }
  };

  const joinWaitingRoom = async (consultationId: string) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/join_waiting_room/`);
      toast.success('Joined waiting room');
      return response.data;
    } catch (error: any) {
      console.error('Error joining waiting room:', error);
      const message = error.response?.data?.error || 'Failed to join waiting room';
      toast.error(message);
      throw error;
    }
  };

  const reportTechnicalIssue = async (consultationId: string, issueData: {
    issue_type: string;
    description: string;
    severity?: string;
  }) => {
    try {
      const response = await api.post(`${endpoints.consultations}${consultationId}/report_issue/`, issueData);
      toast.success('Technical issue reported');
      return response.data;
    } catch (error: any) {
      console.error('Error reporting issue:', error);
      const message = error.response?.data?.error || 'Failed to report issue';
      toast.error(message);
      throw error;
    }
  };

  // WebSocket connection management
  const connectWebSocket = useCallback((consultationId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/consultation/${consultationId}/`;

    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    wsRef.current.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      setIsConnected(false);
      
      // Attempt to reconnect after a delay
      if (event.code !== 1000) { // Not a normal closure
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket(consultationId);
        }, 3000);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  }, []);

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000); // Normal closure
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const sendWebSocketMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'chat_message':
        setMessages(prev => [...prev, {
          id: data.message_id,
          message: data.message,
          message_type: 'text',
          timestamp: data.timestamp,
          is_private: data.is_private,
          sender_name: data.sender_name,
          sender_role: data.sender_role
        }]);
        break;

      case 'user_joined':
        setParticipants(prev => [...prev.filter(p => p !== data.user_name), data.user_name]);
        toast.success(`${data.user_name} joined the consultation`);
        break;

      case 'user_left':
        setParticipants(prev => prev.filter(p => p !== data.user_name));
        toast(`${data.user_name} left the consultation`);
        break;

      case 'consultation_started':
        toast.success(`Consultation started by ${data.started_by}`);
        fetchConsultations();
        break;

      case 'consultation_ended':
        toast.success(`Consultation ended by ${data.ended_by}`);
        fetchConsultations();
        break;

      case 'patient_waiting':
        toast(`${data.patient_name} is waiting in the waiting room`);
        break;

      case 'technical_issue_reported':
        toast.error(`Technical issue reported: ${data.issue_type}`);
        break;

      case 'consultation_status':
        // Update active consultation status
        if (activeConsultation && activeConsultation.id === data.consultation_id) {
          setActiveConsultation(prev => prev ? { ...prev, ...data } : null);
        }
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    consultations,
    activeConsultation,
    setActiveConsultation,
    messages,
    loading,
    error,
    isConnected,
    participants,
    
    // API methods
    fetchConsultations,
    fetchUpcomingConsultations,
    fetchActiveConsultations,
    fetchConsultationStats,
    createConsultation,
    startConsultation,
    endConsultation,
    cancelConsultation,
    fetchMessages,
    sendMessage,
    joinWaitingRoom,
    reportTechnicalIssue,
    
    // WebSocket methods
    connectWebSocket,
    disconnectWebSocket,
    sendWebSocketMessage,
  };
};