import { useState, useEffect } from 'react';
import { api, endpoints } from '../lib/api';
import toast from 'react-hot-toast';

interface Appointment {
  id: number;
  doctor: {
    id: number;
    first_name: string;
    last_name: string;
    username: string;
    profile: {
      specialization: string;
      price_per_consultation: number;
      avatar?: string;
    };
  };
  patient: {
    id: number;
    first_name: string;
    last_name: string;
    profile: {
      avatar?: string;
    };
  };
  appointment_date: string;
  appointment_time: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  created_at: string;
  booking_date: string;
}

interface CreateAppointmentData {
  doctor_username: string;
  appointment_date: string;
  appointment_time: string;
}

export const useAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAppointments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(endpoints.appointments);
      setAppointments(response.data);
    } catch (error: any) {
      console.error('Error fetching appointments:', error);
      setError(error.response?.data?.message || 'Failed to fetch appointments');
      toast.error('Failed to fetch appointments');
    } finally {
      setLoading(false);
    }
  };

  const createAppointment = async (appointmentData: CreateAppointmentData): Promise<boolean> => {
    try {
      setLoading(true);
      const response = await api.post(endpoints.appointments, appointmentData);
      await fetchAppointments();
      toast.success('Appointment created successfully!');
      return true;
    } catch (error: any) {
      console.error('Error creating appointment:', error);
      const message = error.response?.data?.message || 'Failed to create appointment';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const updateAppointment = async (id: number, data: Partial<Appointment>): Promise<boolean> => {
    try {
      setLoading(true);
      await api.put(endpoints.appointmentDetail(id), data);
      await fetchAppointments();
      toast.success('Appointment updated successfully!');
      return true;
    } catch (error: any) {
      console.error('Error updating appointment:', error);
      const message = error.response?.data?.message || 'Failed to update appointment';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const cancelAppointment = async (id: number): Promise<boolean> => {
    try {
      setLoading(true);
      await api.put(endpoints.appointmentDetail(id), { status: 'cancelled' });
      await fetchAppointments();
      toast.success('Appointment cancelled successfully!');
      return true;
    } catch (error: any) {
      console.error('Error cancelling appointment:', error);
      const message = error.response?.data?.message || 'Failed to cancel appointment';
      toast.error(message);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getUpcomingAppointments = () => {
    const today = new Date();
    return appointments.filter(appointment => {
      const appointmentDate = new Date(appointment.appointment_date);
      return appointmentDate >= today && appointment.status !== 'cancelled';
    }).sort((a, b) => new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime());
  };

  const getTodayAppointments = () => {
    const today = new Date().toISOString().split('T')[0];
    return appointments.filter(appointment => 
      appointment.appointment_date === today && appointment.status !== 'cancelled'
    ).sort((a, b) => a.appointment_time.localeCompare(b.appointment_time));
  };

  return {
    appointments,
    loading,
    error,
    fetchAppointments,
    createAppointment,
    updateAppointment,
    cancelAppointment,
    getUpcomingAppointments,
    getTodayAppointments,
  };
};
