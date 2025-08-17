import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Video, User, MapPin, Phone, Star, CheckCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
  DialogDescription, DialogFooter 
} from './ui/dialog';
import { useAppointments, type Doctor, type AppointmentCreateData } from '../hooks/useAppointments';
import { useConsultations } from '../hooks/useConsultations';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

interface AppointmentBookingProps {
  doctorId?: number;
  onBookingComplete?: (appointment: any) => void;
}

export const AppointmentBooking: React.FC<AppointmentBookingProps> = ({ 
  doctorId, 
  onBookingComplete 
}) => {
  const { user } = useAuth();
  const {
    doctors,
    fetchDoctors,
    getDoctorAvailability,
    createAppointment,
    convertToVirtualConsultation,
    loading: appointmentLoading
  } = useAppointments();
  
  const {
    videoProviders,
    fetchVideoProviders,
    createConsultationFromBooking
  } = useConsultations();

  // Form state
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [appointmentType, setAppointmentType] = useState<'in_person' | 'virtual'>('in_person');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [selectedVideoProvider, setSelectedVideoProvider] = useState<'zoom' | 'google_meet' | 'jitsi'>('jitsi');
  const [consultationNotes, setConsultationNotes] = useState('');
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [step, setStep] = useState<'doctor' | 'datetime' | 'type' | 'details' | 'confirm'>('doctor');
  const [isBooking, setIsBooking] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [bookedAppointment, setBookedAppointment] = useState<any>(null);

  // Load initial data
  useEffect(() => {
    fetchDoctors();
    fetchVideoProviders();
  }, [fetchDoctors, fetchVideoProviders]);

  // Auto-select doctor if provided
  useEffect(() => {
    if (doctorId && doctors.length > 0) {
      const doctor = doctors.find(d => d.id === doctorId);
      if (doctor) {
        setSelectedDoctor(doctor);
        setStep('datetime');
      }
    }
  }, [doctorId, doctors]);

  // Load available slots when date changes
  useEffect(() => {
    if (selectedDoctor && selectedDate) {
      loadAvailableSlots();
    }
  }, [selectedDoctor, selectedDate]);

  const loadAvailableSlots = async () => {
    if (!selectedDoctor || !selectedDate) return;
    
    try {
      const slots = await getDoctorAvailability(selectedDoctor.id, selectedDate);
      setAvailableSlots(slots);
    } catch (error) {
      console.error('Failed to load available slots:', error);
      setAvailableSlots([]);
    }
  };

  const handleDoctorSelect = (doctor: Doctor) => {
    setSelectedDoctor(doctor);
    setStep('datetime');
  };

  const handleDateTimeNext = () => {
    if (!selectedDate || !selectedTime) {
      toast.error('Please select both date and time');
      return;
    }
    setStep('type');
  };

  const handleTypeNext = () => {
    setStep('details');
  };

  const handleDetailsNext = () => {
    setStep('confirm');
  };

  const handleBookAppointment = async () => {
    if (!selectedDoctor || !selectedDate || !selectedTime) {
      toast.error('Please complete all required fields');
      return;
    }

    setIsBooking(true);
    
    try {
      const appointmentData: AppointmentCreateData = {
        doctor: selectedDoctor.id,
        appointment_date: selectedDate,
        appointment_time: selectedTime,
        appointment_type: appointmentType,
        consultation_notes: consultationNotes,
        ...(appointmentType === 'virtual' && { preferred_video_provider: selectedVideoProvider })
      };

      const appointment = await createAppointment(appointmentData);

      // If it's a virtual appointment, automatically create consultation
      if (appointmentType === 'virtual') {
        try {
          await createConsultationFromBooking(appointment.id, {
            video_provider: selectedVideoProvider
          });
        } catch (consultationError) {
          console.error('Failed to create consultation:', consultationError);
          toast.error('Appointment booked but failed to set up virtual consultation');
        }
      }

      setBookedAppointment(appointment);
      setShowSuccess(true);
      
      if (onBookingComplete) {
        onBookingComplete(appointment);
      }
    } catch (error) {
      console.error('Failed to book appointment:', error);
    } finally {
      setIsBooking(false);
    }
  };

  const resetForm = () => {
    setSelectedDoctor(null);
    setAppointmentType('in_person');
    setSelectedDate('');
    setSelectedTime('');
    setSelectedVideoProvider('jitsi');
    setConsultationNotes('');
    setAvailableSlots([]);
    setStep('doctor');
    setShowSuccess(false);
    setBookedAppointment(null);
  };

  const getNextAvailableDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  const formatTime = (time: string) => {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getVideoProviderInfo = (provider: string) => {
    switch (provider) {
      case 'zoom':
        return { name: 'Zoom', description: 'Professional video conferencing with HD quality' };
      case 'google_meet':
        return { name: 'Google Meet', description: 'Easy-to-use Google video calling' };
      case 'jitsi':
        return { name: 'Jitsi Meet', description: 'Open-source, secure video conferencing' };
      default:
        return { name: provider, description: 'Video conferencing platform' };
    }
  };

  if (showSuccess) {
    return (
      <div className="max-w-md mx-auto">
        <Card>
          <CardContent className="text-center p-6">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-green-600 mb-2">Booking Confirmed!</h2>
            <p className="text-gray-600 mb-4">
              Your {appointmentType === 'virtual' ? 'virtual consultation' : 'appointment'} has been successfully booked.
            </p>
            
            {bookedAppointment && (
              <div className="bg-gray-50 rounded-lg p-4 mb-4 text-left">
                <h3 className="font-semibold mb-2">Appointment Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-2 text-gray-500" />
                    <span>Dr. {selectedDoctor?.first_name} {selectedDoctor?.last_name}</span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-2 text-gray-500" />
                    <span>{new Date(selectedDate).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-gray-500" />
                    <span>{formatTime(selectedTime)}</span>
                  </div>
                  <div className="flex items-center">
                    {appointmentType === 'virtual' ? (
                      <Video className="w-4 h-4 mr-2 text-gray-500" />
                    ) : (
                      <MapPin className="w-4 h-4 mr-2 text-gray-500" />
                    )}
                    <span>
                      {appointmentType === 'virtual' 
                        ? `Virtual - ${getVideoProviderInfo(selectedVideoProvider).name}`
                        : 'In-Person Visit'
                      }
                    </span>
                  </div>
                </div>
              </div>
            )}

            {appointmentType === 'virtual' && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-blue-800 text-sm">
                  <Video className="w-4 h-4 inline mr-1" />
                  Meeting details will be sent to your email before the appointment.
                </p>
              </div>
            )}
            
            <div className="flex space-x-3">
              <Button onClick={resetForm} variant="outline" className="flex-1">
                Book Another
              </Button>
              <Button 
                onClick={() => window.location.href = '/appointments'} 
                className="flex-1"
              >
                View Appointments
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {['doctor', 'datetime', 'type', 'details', 'confirm'].map((stepName, index) => (
            <div key={stepName} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === stepName ? 'bg-primary-600 text-white' :
                ['doctor', 'datetime', 'type', 'details', 'confirm'].indexOf(step) > index 
                  ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
              }`}>
                {['doctor', 'datetime', 'type', 'details', 'confirm'].indexOf(step) > index ? '✓' : index + 1}
              </div>
              {index < 4 && (
                <div className={`w-16 h-0.5 ml-2 ${
                  ['doctor', 'datetime', 'type', 'details', 'confirm'].indexOf(step) > index 
                    ? 'bg-green-500' : 'bg-gray-300'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-sm text-gray-600">
          <span>Doctor</span>
          <span>Date & Time</span>
          <span>Type</span>
          <span>Details</span>
          <span>Confirm</span>
        </div>
      </div>

      {/* Step 1: Doctor Selection */}
      {step === 'doctor' && (
        <div>
          <h2 className="text-2xl font-bold mb-6">Select a Doctor</h2>
          <div className="grid gap-4">
            {doctors.map((doctor) => (
              <Card key={doctor.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center">
                      {doctor.profile_picture ? (
                        <img 
                          src={doctor.profile_picture} 
                          alt={`Dr. ${doctor.first_name} ${doctor.last_name}`}
                          className="w-full h-full object-cover rounded-full"
                        />
                      ) : (
                        <User className="w-8 h-8 text-gray-400" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">
                        Dr. {doctor.first_name} {doctor.last_name}
                      </h3>
                      {doctor.specialization && (
                        <p className="text-gray-600">{doctor.specialization}</p>
                      )}
                      {doctor.rating && (
                        <div className="flex items-center mt-1">
                          <Star className="w-4 h-4 text-yellow-400 fill-current" />
                          <span className="ml-1 text-sm text-gray-600">{doctor.rating}/5</span>
                        </div>
                      )}
                      <div className="flex items-center mt-2 space-x-4">
                        {doctor.supports_virtual_consultations && (
                          <Badge variant="outline" className="text-blue-600 border-blue-600">
                            <Video className="w-3 h-3 mr-1" />
                            Virtual Available
                          </Badge>
                        )}
                      </div>
                    </div>
                    <Button onClick={() => handleDoctorSelect(doctor)}>
                      Select
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Date & Time Selection */}
      {step === 'datetime' && selectedDoctor && (
        <div>
          <h2 className="text-2xl font-bold mb-6">Select Date & Time</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">Choose Date</h3>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={getNextAvailableDate()}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Available Times</h3>
              {selectedDate ? (
                <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                  {availableSlots.length > 0 ? (
                    availableSlots.map((slot) => (
                      <Button
                        key={slot}
                        variant={selectedTime === slot ? "default" : "outline"}
                        onClick={() => setSelectedTime(slot)}
                        className="justify-center"
                      >
                        {formatTime(slot)}
                      </Button>
                    ))
                  ) : (
                    <p className="text-gray-600 col-span-2">No available slots for this date</p>
                  )}
                </div>
              ) : (
                <p className="text-gray-600">Please select a date first</p>
              )}
            </div>
          </div>
          
          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={() => setStep('doctor')}>
              Back
            </Button>
            <Button onClick={handleDateTimeNext}>
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Appointment Type */}
      {step === 'type' && selectedDoctor && (
        <div>
          <h2 className="text-2xl font-bold mb-6">Appointment Type</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <Card 
              className={`cursor-pointer transition-all ${
                appointmentType === 'in_person' ? 'ring-2 ring-primary-500 bg-primary-50' : 'hover:shadow-md'
              }`}
              onClick={() => setAppointmentType('in_person')}
            >
              <CardContent className="p-6 text-center">
                <MapPin className="w-12 h-12 mx-auto mb-4 text-primary-600" />
                <h3 className="text-xl font-semibold mb-2">In-Person Visit</h3>
                <p className="text-gray-600">
                  Meet with the doctor at their clinic for a comprehensive examination.
                </p>
              </CardContent>
            </Card>

            <Card 
              className={`cursor-pointer transition-all ${
                appointmentType === 'virtual' ? 'ring-2 ring-primary-500 bg-primary-50' : 'hover:shadow-md'
              } ${!selectedDoctor.supports_virtual_consultations ? 'opacity-50 cursor-not-allowed' : ''}`}
              onClick={() => {
                if (selectedDoctor.supports_virtual_consultations) {
                  setAppointmentType('virtual');
                }
              }}
            >
              <CardContent className="p-6 text-center">
                <Video className="w-12 h-12 mx-auto mb-4 text-primary-600" />
                <h3 className="text-xl font-semibold mb-2">Virtual Consultation</h3>
                <p className="text-gray-600">
                  Connect with the doctor online through secure video calling.
                </p>
                {!selectedDoctor.supports_virtual_consultations && (
                  <p className="text-red-500 text-sm mt-2">Not available for this doctor</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Video Provider Selection for Virtual Appointments */}
          {appointmentType === 'virtual' && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4">Select Video Platform</h3>
              <div className="grid md:grid-cols-3 gap-4">
                {Object.keys(videoProviders).filter(provider => 
                  selectedDoctor.preferred_video_providers.includes(provider) || 
                  selectedDoctor.preferred_video_providers.length === 0
                ).map((provider) => {
                  const providerInfo = getVideoProviderInfo(provider);
                  return (
                    <Card
                      key={provider}
                      className={`cursor-pointer transition-all ${
                        selectedVideoProvider === provider ? 'ring-2 ring-primary-500' : 'hover:shadow-md'
                      }`}
                      onClick={() => setSelectedVideoProvider(provider as any)}
                    >
                      <CardContent className="p-4 text-center">
                        <h4 className="font-semibold">{providerInfo.name}</h4>
                        <p className="text-sm text-gray-600">{providerInfo.description}</p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={() => setStep('datetime')}>
              Back
            </Button>
            <Button onClick={handleTypeNext}>
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Additional Details */}
      {step === 'details' && (
        <div>
          <h2 className="text-2xl font-bold mb-6">Additional Details</h2>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Consultation Notes (Optional)
              </label>
              <Textarea
                value={consultationNotes}
                onChange={(e) => setConsultationNotes(e.target.value)}
                placeholder="Please describe your symptoms, concerns, or any specific questions you'd like to discuss..."
                rows={4}
                className="w-full"
              />
              <p className="text-sm text-gray-500 mt-1">
                This information helps the doctor prepare for your consultation.
              </p>
            </div>
          </div>
          
          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={() => setStep('type')}>
              Back
            </Button>
            <Button onClick={handleDetailsNext}>
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Step 5: Confirmation */}
      {step === 'confirm' && selectedDoctor && (
        <div>
          <h2 className="text-2xl font-bold mb-6">Confirm Your Appointment</h2>
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center">
                  <User className="w-5 h-5 mr-3 text-gray-500" />
                  <div>
                    <p className="font-semibold">Dr. {selectedDoctor.first_name} {selectedDoctor.last_name}</p>
                    {selectedDoctor.specialization && (
                      <p className="text-sm text-gray-600">{selectedDoctor.specialization}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 mr-3 text-gray-500" />
                  <div>
                    <p className="font-semibold">{new Date(selectedDate).toLocaleDateString()}</p>
                    <p className="text-sm text-gray-600">
                      {new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long' })}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <Clock className="w-5 h-5 mr-3 text-gray-500" />
                  <p className="font-semibold">{formatTime(selectedTime)}</p>
                </div>
                
                <div className="flex items-center">
                  {appointmentType === 'virtual' ? (
                    <Video className="w-5 h-5 mr-3 text-gray-500" />
                  ) : (
                    <MapPin className="w-5 h-5 mr-3 text-gray-500" />
                  )}
                  <div>
                    <p className="font-semibold">
                      {appointmentType === 'virtual' ? 'Virtual Consultation' : 'In-Person Visit'}
                    </p>
                    {appointmentType === 'virtual' && (
                      <p className="text-sm text-gray-600">
                        via {getVideoProviderInfo(selectedVideoProvider).name}
                      </p>
                    )}
                  </div>
                </div>
                
                {consultationNotes && (
                  <div className="border-t pt-4 mt-4">
                    <p className="font-semibold mb-2">Notes:</p>
                    <p className="text-gray-600">{consultationNotes}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          
          {appointmentType === 'virtual' && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Virtual Consultation Info</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Meeting link will be sent to your email</li>
                <li>• Join 5-10 minutes early to test your connection</li>
                <li>• Ensure you have a stable internet connection</li>
                <li>• Find a quiet, private space for your consultation</li>
              </ul>
            </div>
          )}
          
          <div className="flex justify-between mt-8">
            <Button variant="outline" onClick={() => setStep('details')}>
              Back
            </Button>
            <Button 
              onClick={handleBookAppointment} 
              disabled={isBooking}
              className="px-8"
            >
              {isBooking ? 'Booking...' : 'Confirm Booking'}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};