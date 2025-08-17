import { useState, useEffect, useCallback } from 'react';
import { api, endpoints } from '../lib/api';
import toast from 'react-hot-toast';

export interface Appointment {
  id: number;
  doctor: number;
  patient: number;
  doctor_name: string;
  patient_name: string;
  appointment_date: string;
  appointment_time: string;
  booking_date: string;
  appointment_type: 'in_person' | 'virtual';
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
  consultation_notes?: string;
  preferred_video_provider?: 'zoom' | 'google_meet' | 'jitsi';
  consultation?: {
    id: string;
    meeting_url: string;
    status: string;
  };
}

export interface AppointmentCreateData {
  doctor: number;
  appointment_date: string;
  appointment_time: string;
  appointment_type: 'in_person' | 'virtual';
  consultation_notes?: string;
  preferred_video_provider?: 'zoom' | 'google_meet' | 'jitsi';
}

export interface Doctor {
  id: number;
  first_name: string;
  last_name: string;
  specialization?: string;
  profile_picture?: string;
  rating?: number;
  available_slots?: string[];
  supports_virtual_consultations: boolean;
  preferred_video_providers: string[];
}

export interface AppointmentStats {
  total_appointments: number;
  upcoming_appointments: number;
  completed_appointments: number;
  virtual_appointments: number;
  in_person_appointments: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
}

export const useAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [currentAppointment, setCurrentAppointment] = useState<Appointment | null>(null);
  const [stats, setStats] = useState<AppointmentStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch appointments
  const fetchAppointments = useCallback(async (filters?: any) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams(filters).toString();
      const url = params ? `${endpoints.appointments}?${params}` : endpoints.appointments;
      const response = await api.get(url);
      setAppointments(response.results || response);
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch appointments';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch appointment by ID
  const fetchAppointmentById = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`${endpoints.appointments}${id}/`);
      setCurrentAppointment(response);
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch appointment';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create appointment
  const createAppointment = useCallback(async (data: AppointmentCreateData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(endpoints.appointments, data);
      setAppointments(prev => [response, ...prev]);
      
      // If it's a virtual appointment, show consultation creation success
      if (data.appointment_type === 'virtual') {
        toast.success('Virtual appointment booked successfully! Consultation details will be sent to your email.');
      } else {
        toast.success('Appointment booked successfully!');
      }
      
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create appointment';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update appointment
  const updateAppointment = useCallback(async (id: number, data: Partial<AppointmentCreateData>) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.patch(`${endpoints.appointments}${id}/`, data);
      setAppointments(prev => prev.map(apt => apt.id === id ? response : apt));
      
      if (currentAppointment?.id === id) {
        setCurrentAppointment(response);
      }
      
      toast.success('Appointment updated successfully!');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to update appointment';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [currentAppointment]);

  // Cancel appointment
  const cancelAppointment = useCallback(async (id: number, reason?: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.patch(`${endpoints.appointments}${id}/`, { 
        status: 'cancelled',
        cancellation_reason: reason 
      });
      
      setAppointments(prev => prev.map(apt => 
        apt.id === id ? { ...apt, status: 'cancelled' } : apt
      ));
      
      if (currentAppointment?.id === id) {
        setCurrentAppointment(prev => prev ? { ...prev, status: 'cancelled' } : null);
      }
      
      toast.success('Appointment cancelled successfully');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to cancel appointment';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [currentAppointment]);

  // Confirm appointment
  const confirmAppointment = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.patch(`${endpoints.appointments}${id}/`, { status: 'confirmed' });
      
      setAppointments(prev => prev.map(apt => 
        apt.id === id ? { ...apt, status: 'confirmed' } : apt
      ));
      
      if (currentAppointment?.id === id) {
        setCurrentAppointment(prev => prev ? { ...prev, status: 'confirmed' } : null);
      }
      
      toast.success('Appointment confirmed successfully');
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to confirm appointment';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [currentAppointment]);

  // Convert to virtual consultation
  const convertToVirtualConsultation = useCallback(async (appointmentId: number, videoProvider: string) => {
    setLoading(true);
    setError(null);
    try {
      // First update the appointment to virtual type
      await api.patch(`${endpoints.appointments}${appointmentId}/`, {
        appointment_type: 'virtual',
        preferred_video_provider: videoProvider
      });

      // Create consultation from the booking
      const consultationResponse = await api.post(
        `${endpoints.bookingConsultations}${appointmentId}/create-consultation/`,
        { video_provider: videoProvider }
      );

      // Refresh appointment data
      await fetchAppointmentById(appointmentId);
      
      toast.success('Appointment converted to virtual consultation successfully!');
      return consultationResponse;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to convert to virtual consultation';
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [fetchAppointmentById]);

  // Fetch available doctors
  const fetchDoctors = useCallback(async (filters?: any) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams(filters).toString();
      const url = params ? `${endpoints.doctors}?${params}` : endpoints.doctors;
      const response = await api.get(url);
      setDoctors(response.results || response);
      return response;
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to fetch doctors';
      setError(errorMessage);
      console.error(errorMessage);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Get doctor availability
  const getDoctorAvailability = useCallback(async (doctorId: number, date: string) => {
    try {
      const response = await api.get(`${endpoints.doctors}${doctorId}/availability/?date=${date}`);
      return response.available_slots || [];
    } catch (error: any) {
      console.error('Failed to fetch doctor availability:', error);
      return [];
    }
  }, []);

  // Fetch appointment stats
  const fetchAppointmentStats = useCallback(async () => {
    try {
      const response = await api.get(`${endpoints.appointments}stats/`);
      setStats(response);
      return response;
    } catch (error: any) {
      console.error('Failed to fetch appointment stats:', error);
      return null;
    }
  }, []);

  // Get upcoming appointments
  const getUpcomingAppointments = useCallback(() => {
    const now = new Date();
    return appointments.filter(appointment => {
      const appointmentDateTime = new Date(`${appointment.appointment_date}T${appointment.appointment_time}`);
      return appointmentDateTime > now && ['pending', 'confirmed'].includes(appointment.status);
    }).sort((a, b) => {
      const dateA = new Date(`${a.appointment_date}T${a.appointment_time}`);
      const dateB = new Date(`${b.appointment_date}T${b.appointment_time}`);
      return dateA.getTime() - dateB.getTime();
    });
  }, [appointments]);

  // Get today's appointments
  const getTodayAppointments = useCallback(() => {
    const today = new Date().toISOString().split('T')[0];
    return appointments.filter(appointment => 
      appointment.appointment_date === today
    ).sort((a, b) => a.appointment_time.localeCompare(b.appointment_time));
  }, [appointments]);

  // Get virtual appointments
  const getVirtualAppointments = useCallback(() => {
    return appointments.filter(appointment => 
      appointment.appointment_type === 'virtual'
    );
  }, [appointments]);

  // Check if appointment can be converted to virtual
  const canConvertToVirtual = useCallback((appointment: Appointment) => {
    return (
      appointment.appointment_type === 'in_person' &&
      ['pending', 'confirmed'].includes(appointment.status) &&
      !appointment.consultation
    );
  }, []);

  // Check if appointment can be joined (for virtual consultations)
  const canJoinConsultation = useCallback((appointment: Appointment) => {
    if (appointment.appointment_type !== 'virtual' || !appointment.consultation) {
      return false;
    }

    const appointmentDateTime = new Date(`${appointment.appointment_date}T${appointment.appointment_time}`);
    const now = new Date();
    const fifteenMinutesBefore = new Date(appointmentDateTime.getTime() - 15 * 60 * 1000);
    const oneHourAfter = new Date(appointmentDateTime.getTime() + 60 * 60 * 1000);

    return (
      now >= fifteenMinutesBefore &&
      now <= oneHourAfter &&
      ['confirmed'].includes(appointment.status)
    );
  }, []);

  // Get appointment status color
  const getStatusColor = useCallback((status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'confirmed': return 'text-green-600 bg-green-100';
      case 'completed': return 'text-blue-600 bg-blue-100';
      case 'cancelled': return 'text-red-600 bg-red-100';
      case 'no_show': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  }, []);

  // Get appointment type icon
  const getTypeIcon = useCallback((type: string) => {
    switch (type) {
      case 'virtual': return '💻';
      case 'in_person': return '🏥';
      default: return '📅';
    }
  }, []);

  return {
    // State
    appointments,
    doctors,
    currentAppointment,
    stats,
    loading,
    error,

    // Basic CRUD operations
    fetchAppointments,
    fetchAppointmentById,
    createAppointment,
    updateAppointment,
    cancelAppointment,
    confirmAppointment,

    // Virtual consultation operations
    convertToVirtualConsultation,

    // Doctor operations
    fetchDoctors,
    getDoctorAvailability,

    // Stats and filtering
    fetchAppointmentStats,
    getUpcomingAppointments,
    getTodayAppointments,
    getVirtualAppointments,

    // Helper functions
    canConvertToVirtual,
    canJoinConsultation,
    getStatusColor,
    getTypeIcon,

    // Setters for external use
    setCurrentAppointment,
    setAppointments,
  };
};
