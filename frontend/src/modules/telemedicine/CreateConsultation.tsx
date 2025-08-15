import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, Video, User, Phone, Settings, Plus } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { useAuth } from '../../hooks/useAuth';
import { useConsultations } from '../../hooks/useConsultations';
import { api, endpoints } from '../../lib/api';
import toast from 'react-hot-toast';

interface Booking {
  id: number;
  patient_name: string;
  doctor_name: string;
  appointment_date: string;
  appointment_time: string;
  status: string;
  duration: number;
}

interface Doctor {
  id: number;
  user: {
    first_name: string;
    last_name: string;
    email: string;
  };
  specialization: string;
  price_per_consultation: number;
}

interface Patient {
  id: number;
  user: {
    first_name: string;
    last_name: string;
    email: string;
  };
  age?: number;
  gender?: string;
}

const CreateConsultation: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { createConsultation } = useConsultations();

  // Form state
  const [selectedBooking, setSelectedBooking] = useState<string>('');
  const [videoProvider, setVideoProvider] = useState<'jitsi' | 'zoom' | 'google_meet'>('jitsi');
  const [recordingEnabled, setRecordingEnabled] = useState(false);
  const [notes, setNotes] = useState('');
  const [scheduledStart, setScheduledStart] = useState('');
  const [customBooking, setCustomBooking] = useState(false);
  const [selectedDoctor, setSelectedDoctor] = useState<string>('');
  const [selectedPatient, setSelectedPatient] = useState<string>('');

  // Data state
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bookingsRes, doctorsRes, patientsRes] = await Promise.all([
        api.get(endpoints.appointments),
        api.get(endpoints.doctors),
        api.get(endpoints.patients),
      ]);

      // Filter bookings that don't have consultations yet
      const availableBookings = bookingsRes.data.filter((booking: Booking) => 
        booking.status === 'confirmed' || booking.status === 'scheduled'
      );

      setBookings(availableBookings);
      setDoctors(doctorsRes.data.results || doctorsRes.data);
      setPatients(patientsRes.data.results || patientsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitLoading(true);

    try {
      const consultationData = {
        booking_id: customBooking ? null : selectedBooking,
        doctor_id: customBooking ? selectedDoctor : undefined,
        patient_id: customBooking ? selectedPatient : undefined,
        video_provider: videoProvider,
        recording_enabled: recordingEnabled,
        notes,
        scheduled_start: scheduledStart || new Date().toISOString(),
      };

      const response = await api.post(endpoints.consultations, consultationData);
      
      toast.success('Consultation created successfully!');
      navigate('/consultations');
    } catch (error: any) {
      console.error('Error creating consultation:', error);
      const message = error.response?.data?.message || 'Failed to create consultation';
      toast.error(message);
    } finally {
      setSubmitLoading(false);
    }
  };

  const getVideoProviderIcon = (provider: string) => {
    switch (provider) {
      case 'zoom':
        return '📹';
      case 'google_meet':
        return '🤝';
      case 'jitsi':
        return '🎥';
      default:
        return '📹';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create New Consultation</h1>
          <p className="text-gray-600">Set up a virtual consultation for your appointment</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              {/* Booking Selection */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-5 w-5" />
                    Appointment Selection
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center gap-4 mb-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        checked={!customBooking}
                        onChange={() => setCustomBooking(false)}
                        className="w-4 h-4 text-primary"
                      />
                      Use existing appointment
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="radio"
                        checked={customBooking}
                        onChange={() => setCustomBooking(true)}
                        className="w-4 h-4 text-primary"
                      />
                      Create custom consultation
                    </label>
                  </div>

                  {!customBooking ? (
                    <div>
                      <Label htmlFor="booking">Select Appointment</Label>
                      <Select value={selectedBooking} onValueChange={setSelectedBooking}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose an appointment" />
                        </SelectTrigger>
                        <SelectContent>
                          {bookings.map((booking) => (
                            <SelectItem key={booking.id} value={booking.id.toString()}>
                              <div className="flex items-center justify-between w-full">
                                <span>
                                  {booking.patient_name} - {booking.doctor_name}
                                </span>
                                <Badge variant="outline">
                                  {booking.appointment_date} at {booking.appointment_time}
                                </Badge>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="doctor">Select Doctor</Label>
                        <Select value={selectedDoctor} onValueChange={setSelectedDoctor}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a doctor" />
                          </SelectTrigger>
                          <SelectContent>
                            {doctors.map((doctor) => (
                              <SelectItem key={doctor.id} value={doctor.id.toString()}>
                                Dr. {doctor.user.first_name} {doctor.user.last_name}
                                {doctor.specialization && ` - ${doctor.specialization}`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="patient">Select Patient</Label>
                        <Select value={selectedPatient} onValueChange={setSelectedPatient}>
                          <SelectTrigger>
                            <SelectValue placeholder="Choose a patient" />
                          </SelectTrigger>
                          <SelectContent>
                            {patients.map((patient) => (
                              <SelectItem key={patient.id} value={patient.id.toString()}>
                                {patient.user.first_name} {patient.user.last_name}
                                {patient.age && ` (${patient.age} years)`}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Consultation Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Consultation Settings
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="videoProvider">Video Platform</Label>
                      <Select value={videoProvider} onValueChange={(value: any) => setVideoProvider(value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="jitsi">
                            <div className="flex items-center gap-2">
                              <span>{getVideoProviderIcon('jitsi')}</span>
                              <span>Jitsi Meet (Free)</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="zoom">
                            <div className="flex items-center gap-2">
                              <span>{getVideoProviderIcon('zoom')}</span>
                              <span>Zoom</span>
                            </div>
                          </SelectItem>
                          <SelectItem value="google_meet">
                            <div className="flex items-center gap-2">
                              <span>{getVideoProviderIcon('google_meet')}</span>
                              <span>Google Meet</span>
                            </div>
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="scheduledStart">Scheduled Start Time</Label>
                      <Input
                        type="datetime-local"
                        value={scheduledStart}
                        onChange={(e) => setScheduledStart(e.target.value)}
                        min={new Date().toISOString().slice(0, 16)}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="recording"
                      checked={recordingEnabled}
                      onChange={(e) => setRecordingEnabled(e.target.checked)}
                      className="w-4 h-4 text-primary rounded"
                    />
                    <Label htmlFor="recording">Enable recording (if supported by platform)</Label>
                  </div>

                  <div>
                    <Label htmlFor="notes">Additional Notes</Label>
                    <Textarea
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Any additional notes or instructions for this consultation..."
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Info */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Platform Features</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2">
                    <h4 className="font-medium">Jitsi Meet</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Free and open source</li>
                      <li>• No account required</li>
                      <li>• Screen sharing</li>
                      <li>• Chat messaging</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Zoom</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Professional features</li>
                      <li>• Recording capabilities</li>
                      <li>• Waiting rooms</li>
                      <li>• Breakout rooms</li>
                    </ul>
                  </div>
                  <div className="space-y-2">
                    <h4 className="font-medium">Google Meet</h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      <li>• Google integration</li>
                      <li>• High quality video</li>
                      <li>• Calendar sync</li>
                      <li>• Mobile friendly</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Submit Button */}
              <Card>
                <CardContent className="pt-6">
                  <Button
                    type="submit"
                    className="w-full"
                    size="lg"
                    disabled={submitLoading || (!selectedBooking && !customBooking) || (customBooking && (!selectedDoctor || !selectedPatient))}
                  >
                    {submitLoading ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Creating...
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <Plus className="h-4 w-4" />
                        Create Consultation
                      </div>
                    )}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full mt-2"
                    onClick={() => navigate('/consultations')}
                  >
                    Cancel
                  </Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateConsultation;