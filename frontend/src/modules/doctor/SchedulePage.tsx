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
import { 
  Calendar,
  Clock,
  Plus,
  Trash2,
  Save,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { api, endpoints } from '../../lib/api';
import toast from 'react-hot-toast';

interface TimeBlock {
  start: string;
  end: string;
  slots_per_hour: number;
}

interface Schedule {
  sunday: TimeBlock[];
  monday: TimeBlock[];
  tuesday: TimeBlock[];
  wednesday: TimeBlock[];
  thursday: TimeBlock[];
  friday: TimeBlock[];
  saturday: TimeBlock[];
}

type DayKey = keyof Schedule;

export function SchedulePage() {
  const [schedule, setSchedule] = useState<Schedule>({
    sunday: [],
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: []
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const days: DayKey[] = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];

  useEffect(() => {
    fetchSchedule();
  }, []);

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const response = await api.get(endpoints.doctorSchedule);
      setSchedule(response.data);
    } catch (error: any) {
      console.error('Error fetching schedule:', error);
      toast.error('Failed to fetch schedule');
    } finally {
      setLoading(false);
    }
  };

  const addBlock = (day: DayKey) => {
    setSchedule(prev => ({
      ...prev,
      [day]: [...prev[day], { start: '09:00', end: '10:00', slots_per_hour: 4 }]
    }));
  };

  const updateBlock = (day: DayKey, index: number, updates: Partial<TimeBlock>) => {
    setSchedule(prev => ({
      ...prev,
      [day]: prev[day].map((block, i) => 
        i === index ? { ...block, ...updates } : block
      )
    }));
  };

  const removeBlock = (day: DayKey, index: number) => {
    setSchedule(prev => ({
      ...prev,
      [day]: prev[day].filter((_, i) => i !== index)
    }));
  };

  const saveSchedule = async () => {
    setSaving(true);
    try {
      await api.post(endpoints.doctorSchedule, schedule);
      toast.success('Schedule saved successfully!');
    } catch (error: any) {
      console.error('Error saving schedule:', error);
      toast.error('Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-600">Loading schedule...</p>
        </div>
      </div>
    );
  }

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
          <Button 
            onClick={saveSchedule} 
            disabled={saving}
            className="bg-primary text-white"
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Schedule
              </>
            )}
          </Button>
        </motion.div>

        {/* Schedule Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {days.map((day, dayIndex) => (
            <motion.div
              key={day}
              variants={itemVariants}
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: dayIndex * 0.1 }}
            >
              <Card className="shadow-lg">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-5 w-5 text-blue-600" />
                      <CardTitle className="capitalize">{day}</CardTitle>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {schedule[day].length} time blocks
                      </Badge>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => addBlock(day)}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add Block
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {schedule[day].length === 0 ? (
                    <div className="text-center py-8">
                      <Clock className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-500 text-sm">No time blocks set</p>
                      <p className="text-gray-400 text-xs">Add time blocks to set your availability</p>
                    </div>
                  ) : (
                    schedule[day].map((block, blockIndex) => (
                      <motion.div
                        key={blockIndex}
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: blockIndex * 0.1 }}
                        className="p-4 border border-gray-200 rounded-lg bg-gray-50"
                      >
                        <div className="grid grid-cols-3 gap-3 items-center">
                          <div className="space-y-1">
                            <Label className="text-xs text-gray-600">Start Time</Label>
                            <Input
                              type="time"
                              value={block.start}
                              onChange={(e) => updateBlock(day, blockIndex, { start: e.target.value })}
                              className="text-sm"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs text-gray-600">End Time</Label>
                            <Input
                              type="time"
                              value={block.end}
                              onChange={(e) => updateBlock(day, blockIndex, { end: e.target.value })}
                              className="text-sm"
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs text-gray-600">Slots/Hour</Label>
                            <Input
                              type="number"
                              min="1"
                              max="6"
                              value={block.slots_per_hour}
                              onChange={(e) => updateBlock(day, blockIndex, { slots_per_hour: parseInt(e.target.value) || 4 })}
                              className="text-sm"
                            />
                          </div>
                        </div>
                        <div className="flex justify-end mt-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => removeBlock(day, blockIndex)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Remove
                          </Button>
                        </div>
                      </motion.div>
                    ))
                  )}
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Info Card */}
        <motion.div variants={itemVariants}>
          <Card className="shadow-lg border-l-4 border-l-blue-500">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-blue-600" />
                <CardTitle>Schedule Information</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Time Blocks</h4>
                  <p className="text-gray-600">Define your working hours for each day</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Slots per Hour</h4>
                  <p className="text-gray-600">Number of appointments you can handle per hour</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-1">Patient Booking</h4>
                  <p className="text-gray-600">Patients can only book within your available time slots</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
}






