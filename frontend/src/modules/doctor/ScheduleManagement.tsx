import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
import {
  Clock,
  Calendar,
  Plus,
  Trash2,
  Save,
  Eye,
  EyeOff
} from 'lucide-react';

interface TimeSlot {
  id: string;
  startTime: string;
  endTime: string;
}

interface DaySchedule {
  enabled: boolean;
  slots: TimeSlot[];
}

interface WeekSchedule {
  [key: string]: DaySchedule;
}

const DAYS = [
  { key: 'sunday', name: 'Sunday', shortName: 'Sun' },
  { key: 'monday', name: 'Monday', shortName: 'Mon' },
  { key: 'tuesday', name: 'Tuesday', shortName: 'Tue' },
  { key: 'wednesday', name: 'Wednesday', shortName: 'Wed' },
  { key: 'thursday', name: 'Thursday', shortName: 'Thu' },
  { key: 'friday', name: 'Friday', shortName: 'Fri' },
  { key: 'saturday', name: 'Saturday', shortName: 'Sat' }
];

const ScheduleManagement: React.FC = () => {
  const [schedule, setSchedule] = useState<WeekSchedule>({});
  const [isSaving, setIsSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(true);

  // Initialize schedule
  useEffect(() => {
    const initialSchedule: WeekSchedule = {};
    DAYS.forEach(day => {
      initialSchedule[day.key] = {
        enabled: false,
        slots: []
      };
    });
    setSchedule(initialSchedule);
  }, []);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const toggleDay = (dayKey: string) => {
    setSchedule(prev => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        enabled: !prev[dayKey]?.enabled,
        slots: !prev[dayKey]?.enabled ? 
          prev[dayKey]?.slots?.length > 0 ? prev[dayKey].slots : [{ id: generateId(), startTime: '09:00', endTime: '17:00' }] :
          []
      }
    }));
  };

  const addTimeSlot = (dayKey: string) => {
    setSchedule(prev => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        slots: [
          ...prev[dayKey].slots,
          { id: generateId(), startTime: '09:00', endTime: '17:00' }
        ]
      }
    }));
  };

  const removeTimeSlot = (dayKey: string, slotId: string) => {
    setSchedule(prev => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        slots: prev[dayKey].slots.filter(slot => slot.id !== slotId)
      }
    }));
  };

  const updateTimeSlot = (dayKey: string, slotId: string, field: 'startTime' | 'endTime', value: string) => {
    setSchedule(prev => ({
      ...prev,
      [dayKey]: {
        ...prev[dayKey],
        slots: prev[dayKey].slots.map(slot =>
          slot.id === slotId ? { ...slot, [field]: value } : slot
        )
      }
    }));
  };

  const validateSchedule = (): string[] => {
    const errors: string[] = [];
    
    Object.entries(schedule).forEach(([dayKey, daySchedule]) => {
      if (daySchedule.enabled) {
        const dayName = DAYS.find(d => d.key === dayKey)?.name || dayKey;
        
        if (daySchedule.slots.length === 0) {
          errors.push(`${dayName}: No time slots defined`);
        }
        
        daySchedule.slots.forEach((slot, index) => {
          if (!slot.startTime || !slot.endTime) {
            errors.push(`${dayName} Slot ${index + 1}: Start and end times are required`);
          } else if (slot.startTime >= slot.endTime) {
            errors.push(`${dayName} Slot ${index + 1}: End time must be after start time`);
          }
        });
        
        // Check for overlapping slots
        for (let i = 0; i < daySchedule.slots.length - 1; i++) {
          const currentSlot = daySchedule.slots[i];
          const nextSlot = daySchedule.slots[i + 1];
          
          if (currentSlot.endTime > nextSlot.startTime) {
            errors.push(`${dayName}: Overlapping time slots detected`);
          }
        }
      }
    });
    
    const hasEnabledDays = Object.values(schedule).some(day => day.enabled);
    if (!hasEnabledDays) {
      errors.push('At least one day must be enabled');
    }
    
    return errors;
  };

  const handleSave = async () => {
    const errors = validateSchedule();
    if (errors.length > 0) {
      alert('Please fix the following errors:\n' + errors.join('\n'));
      return;
    }

    setIsSaving(true);
    try {
      // TODO: Replace with actual API call
      console.log('Saving schedule:', schedule);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      alert('Schedule updated successfully!');
    } catch (error) {
      console.error('Error saving schedule:', error);
      alert('Error updating schedule. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const getEnabledDaysCount = () => {
    return Object.values(schedule).filter(day => day.enabled).length;
  };

  const getTotalSlots = () => {
    return Object.values(schedule).reduce((total, day) => 
      total + (day.enabled ? day.slots.length : 0), 0
    );
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5 }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-6xl mx-auto space-y-6"
      >
        {/* Header */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Schedule Management</h1>
            <p className="text-gray-600 mt-1">Set your availability for patient appointments</p>
          </div>
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              onClick={() => setShowPreview(!showPreview)}
              className="flex items-center space-x-2"
            >
              {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              <span>{showPreview ? 'Hide' : 'Show'} Preview</span>
            </Button>
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="bg-primary text-white"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Schedule
                </>
              )}
            </Button>
          </div>
        </motion.div>

        {/* Statistics */}
        <motion.div variants={itemVariants}>
          <Card>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{getEnabledDaysCount()}</div>
                  <div className="text-sm text-gray-600">Active Days</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{getTotalSlots()}</div>
                  <div className="text-sm text-gray-600">Time Slots</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {Object.values(schedule).reduce((total, day) => 
                      total + day.slots.reduce((slots, slot) => {
                        if (!slot.startTime || !slot.endTime) return slots;
                        const start = new Date(`2000-01-01T${slot.startTime}`);
                        const end = new Date(`2000-01-01T${slot.endTime}`);
                        return slots + (end.getTime() - start.getTime()) / (1000 * 60 * 60);
                      }, 0), 0
                    ).toFixed(1)}h
                  </div>
                  <div className="text-sm text-gray-600">Total Hours/Week</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Schedule Preview */}
        {showPreview && (
          <motion.div variants={itemVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2" />
                  Schedule Preview
                </CardTitle>
                <CardDescription>Your current weekly availability</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  {DAYS.map(day => {
                    const daySchedule = schedule[day.key];
                    return (
                      <div key={day.key} className="space-y-2">
                        <div className="text-sm font-medium text-center">
                          {day.shortName}
                        </div>
                        {daySchedule?.enabled ? (
                          <div className="space-y-1">
                            {daySchedule.slots.map(slot => (
                              <div
                                key={slot.id}
                                className="text-xs bg-blue-100 text-blue-800 p-2 rounded text-center"
                              >
                                {slot.startTime} - {slot.endTime}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-xs text-gray-400 text-center py-4">
                            Unavailable
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Schedule Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {DAYS.map(day => {
            const daySchedule = schedule[day.key] || { enabled: false, slots: [] };
            
            return (
              <motion.div key={day.key} variants={itemVariants}>
                <Card className={`transition-all duration-200 ${
                  daySchedule.enabled 
                    ? 'border-blue-200 bg-blue-50/30' 
                    : 'border-gray-200'
                }`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <Switch
                          checked={daySchedule.enabled}
                          onCheckedChange={() => toggleDay(day.key)}
                        />
                        <CardTitle className={daySchedule.enabled ? 'text-blue-700' : 'text-gray-500'}>
                          {day.name}
                        </CardTitle>
                      </div>
                      {daySchedule.enabled && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => addTimeSlot(day.key)}
                          className="text-xs"
                        >
                          <Plus className="h-3 w-3 mr-1" />
                          Add Slot
                        </Button>
                      )}
                    </div>
                  </CardHeader>
                  
                  {daySchedule.enabled && (
                    <CardContent>
                      <div className="space-y-3">
                        {daySchedule.slots.map((slot, index) => (
                          <div key={slot.id} className="flex items-center space-x-3 p-3 bg-white rounded-lg border">
                            <div className="flex-1">
                              <Label className="text-xs text-gray-600">From</Label>
                              <Input
                                type="time"
                                value={slot.startTime}
                                onChange={(e) => updateTimeSlot(day.key, slot.id, 'startTime', e.target.value)}
                                className="mt-1"
                              />
                            </div>
                            <div className="flex-1">
                              <Label className="text-xs text-gray-600">To</Label>
                              <Input
                                type="time"
                                value={slot.endTime}
                                onChange={(e) => updateTimeSlot(day.key, slot.id, 'endTime', e.target.value)}
                                className="mt-1"
                              />
                            </div>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => removeTimeSlot(day.key, slot.id)}
                              className="text-red-600 hover:text-red-700 mt-5"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                        
                        {daySchedule.slots.length === 0 && (
                          <div className="text-center py-4 text-gray-500 text-sm">
                            No time slots added yet
                          </div>
                        )}
                      </div>
                    </CardContent>
                  )}
                </Card>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
};

export default ScheduleManagement;