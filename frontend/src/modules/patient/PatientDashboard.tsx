import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../../components/ui/avatar';
import { Button } from '../../components/ui/button';
import { 
  Card as NextUICard,
  Divider,
  Chip,
  User,
  Button as NextUIButton
} from '@nextui-org/react';
import { 
  Heart, 
  Activity, 
  Shield, 
  Bell, 
  Download, 
  Globe, 
  Calendar,
  Clock,
  Pill,
  CheckCircle,
  AlertCircle,
  Info,
  MessageCircle,
  FileText,
  Settings,
  TrendingUp,
  Zap,
  Droplets,
  Activity as ActivityIcon,
  Loader2
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useAppointments } from '../../hooks/useAppointments';
import { useVitals } from '../../hooks/useVitals';

const PatientDashboard: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const { 
    appointments, 
    loading: appointmentsLoading, 
    fetchAppointments, 
    getUpcomingAppointments, 
    getTodayAppointments 
  } = useAppointments();
  const { 
    vitalRecords, 
    loading: vitalsLoading, 
    getLatestVitals, 
    getHealthAssessment 
  } = useVitals();

  useEffect(() => {
    if (user) {
      fetchAppointments();
    }
  }, [user, fetchAppointments]);

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

  // Get real data from backend
  const latestVitals = getLatestVitals();
  const healthAssessment = getHealthAssessment();
  const upcomingAppointments = getUpcomingAppointments();
  const todayAppointments = getTodayAppointments();
  const nextAppointment = upcomingAppointments[0];

  // Loading state
  if (authLoading || appointmentsLoading || vitalsLoading) {
  return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
          <p className="text-gray-600">Loading your health dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state - user not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-4">Please log in to access your health dashboard.</p>
          <Button onClick={() => window.location.href = '/login'}>
            Go to Login
          </Button>
        </div>
      </div>
    );
  }

  // Format vital signs for display
  const vitalSigns = latestVitals.map(vital => ({
    name: vital.category.name,
    value: `${vital.value} ${vital.category.unit}`,
    icon: getVitalIcon(vital.category.name),
    color: getVitalColor(vital.category.name),
    recordedAt: new Date(vital.recorded_at).toLocaleDateString()
  }));

  // Mock medications (this would come from a medications API)
  const medications = [
    { name: 'Lisinopril', dosage: '10mg', time: '08:00 AM Daily', taken: false },
    { name: 'Metformin', dosage: '500mg', time: '12:00 PM Twice daily', taken: true },
    { name: 'Atorvastatin', dosage: '20mg', time: '08:00 PM Daily', taken: false }
  ];

  // Health recommendations based on assessment
  const recommendations = [
    { 
      type: 'continue', 
      text: 'Continue with current medication', 
      icon: CheckCircle, 
      color: 'text-green-600' 
    },
    ...healthAssessment.issues.map(issue => ({
      type: 'action',
      text: issue,
      icon: AlertCircle,
      color: 'text-yellow-600'
    })),
    { 
      type: 'lifestyle', 
      text: 'Follow DASH diet plan', 
      icon: Info, 
      color: 'text-blue-600' 
    },
    { 
      type: 'lifestyle', 
      text: 'Maintain regular exercise routine', 
      icon: Info, 
      color: 'text-blue-600' 
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 p-6">
        <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="max-w-7xl mx-auto space-y-6"
      >
        {/* Header Section */}
        <motion.div variants={itemVariants} className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome back, {user.first_name}!
            </h1>
            <p className="text-gray-600 mt-1">
              {nextAppointment 
                ? `Your next appointment is on ${new Date(nextAppointment.appointment_date).toLocaleDateString()} at ${nextAppointment.appointment_time}`
                : 'No upcoming appointments'
              }
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              Notifications
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download History
            </Button>
            <Button className="bg-primary text-white">
              <Globe className="h-4 w-4 mr-2" />
              Laso Connect
            </Button>
            <Avatar className="h-10 w-10">
              <AvatarImage src={user.profile?.avatar || "/api/placeholder/40/40"} />
              <AvatarFallback className="bg-primary text-white">
                {user.first_name[0]}{user.last_name[0]}
              </AvatarFallback>
            </Avatar>
          </div>
        </motion.div>

        {/* Health Assessment Card */}
        <motion.div variants={itemVariants}>
          <NextUICard className="border-l-4 border-l-green-500 shadow-lg">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-green-600" />
                <CardTitle>Latest Health Assessment</CardTitle>
              </div>
              <div className="flex items-center space-x-2">
                <Badge 
                  variant={healthAssessment.riskLevel === 'Low' ? 'success' : healthAssessment.riskLevel === 'Medium' ? 'warning' : 'danger'} 
                  className="text-xs"
                >
                  {healthAssessment.riskLevel} Risk
                </Badge>
                <div className="flex items-center text-green-600">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  <span className="text-sm font-semibold">
                    {healthAssessment.issues.length === 0 ? '0' : healthAssessment.issues.length} issues
                  </span>
                          </div>
                        </div>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  {new Date(healthAssessment.lastAssessment).toLocaleDateString()} • Health Risk Assessment
                </p>
                <p className="text-gray-700">
                  {healthAssessment.issues.length === 0 
                    ? 'Your vital signs are within normal range. Continue with your current lifestyle and medication.'
                    : `Found ${healthAssessment.issues.length} health concern${healthAssessment.issues.length > 1 ? 's' : ''}. Please consult with your healthcare provider.`
                  }
                </p>
                        </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {vitalSigns.length > 0 ? (
                  vitalSigns.map((vital, index) => (
                    <motion.div
                      key={vital.name}
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-white rounded-lg p-4 border border-gray-100 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center space-x-2 mb-2">
                        <vital.icon className={`h-4 w-4 ${vital.color}`} />
                        <span className="text-xs text-gray-500">{vital.name}</span>
                      </div>
                      <p className={`text-lg font-semibold ${vital.color}`}>{vital.value}</p>
                      <p className="text-xs text-gray-400">Updated {vital.recordedAt}</p>
                    </motion.div>
                  ))
                ) : (
                  <div className="col-span-4 text-center py-8">
                    <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">No vital signs recorded yet</p>
                    <Button variant="outline" size="sm" className="mt-2">
                      Add Vital Signs
                    </Button>
                  </div>
                )}
                  </div>
            </CardContent>
          </NextUICard>
        </motion.div>

        {/* Three Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Medication Reminders */}
          <motion.div variants={itemVariants}>
            <Card className="shadow-lg">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Pill className="h-5 w-5 text-blue-600" />
                    <CardTitle>Medication Reminders</CardTitle>
                  </div>
                  <Button size="sm" variant="outline">
                    Add Medication
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {medications.map((med, index) => (
        <motion.div
                    key={med.name}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-3 rounded-lg border ${
                      med.taken 
                        ? 'border-green-200 bg-green-50' 
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
          <div>
                        <h4 className="font-medium text-gray-900">{med.name}</h4>
                        <p className="text-sm text-gray-600">{med.dosage}</p>
                        <p className="text-xs text-gray-500">{med.time}</p>
          </div>
                      {med.taken ? (
                        <div className="flex items-center text-green-600">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          <span className="text-xs">Taken</span>
          </div>
                      ) : (
                        <Button size="sm" variant="outline">
                          Mark Taken
                        </Button>
                      )}
          </div>
                  </motion.div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Health Recommendations */}
          <motion.div variants={itemVariants}>
            <Card className="shadow-lg">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <CardTitle>Health Recommendations</CardTitle>
          </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {recommendations.map((rec, index) => (
                  <motion.div
                    key={rec.text}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className={`flex items-start space-x-3 p-3 rounded-lg ${
                      rec.type === 'action' 
                        ? 'bg-yellow-50 border border-yellow-200' 
                        : 'bg-gray-50 border border-gray-200'
                    }`}
                  >
                    <rec.icon className={`h-4 w-4 mt-0.5 ${rec.color}`} />
                    <span className="text-sm text-gray-700">{rec.text}</span>
                  </motion.div>
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Next Appointment & Quick Actions */}
          <motion.div variants={itemVariants} className="space-y-6">
            {/* Next Appointment */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Next Appointment</CardTitle>
              </CardHeader>
              <CardContent>
                {nextAppointment ? (
                  <div className="flex items-center space-x-3 mb-4">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={nextAppointment.doctor.profile?.avatar || "/api/placeholder/48/48"} />
                      <AvatarFallback className="bg-primary text-white">
                        {nextAppointment.doctor.first_name[0]}{nextAppointment.doctor.last_name[0]}
                      </AvatarFallback>
                    </Avatar>
          <div>
                      <h4 className="font-medium">
                        Dr. {nextAppointment.doctor.first_name} {nextAppointment.doctor.last_name}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {new Date(nextAppointment.appointment_date).toLocaleDateString()} • {nextAppointment.appointment_time}
                      </p>
                      <Badge variant="outline" className="mt-1">
                        {nextAppointment.doctor.profile?.specialization || 'General Consultation'}
                      </Badge>
          </div>
        </div>
                ) : (
                  <div className="text-center py-4">
                    <Calendar className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500 text-sm">No upcoming appointments</p>
                  </div>
                )}
                <Button className="w-full bg-primary text-white">
                  <Calendar className="h-4 w-4 mr-2" />
                  Manage Appointments
                </Button>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="ghost" className="w-full justify-start">
                  <FileText className="h-4 w-4 mr-2" />
                  View Medical Records
                </Button>
                <Button variant="ghost" className="w-full justify-start">
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Message Healthcare Provider
                </Button>
                <Button variant="ghost" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-2" />
                  Profile Settings
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

// Helper functions for vital signs
const getVitalIcon = (vitalName: string) => {
  const iconMap: { [key: string]: any } = {
    'Blood Pressure': Activity,
    'Heart Rate': Heart,
    'Cholesterol': Droplets,
    'Blood Glucose': Zap,
    'Temperature': Activity,
    'Weight': Activity,
    'Height': Activity,
  };
  return iconMap[vitalName] || Activity;
};

const getVitalColor = (vitalName: string) => {
  const colorMap: { [key: string]: string } = {
    'Blood Pressure': 'text-blue-600',
    'Heart Rate': 'text-red-600',
    'Cholesterol': 'text-purple-600',
    'Blood Glucose': 'text-green-600',
    'Temperature': 'text-orange-600',
    'Weight': 'text-indigo-600',
    'Height': 'text-teal-600',
  };
  return colorMap[vitalName] || 'text-gray-600';
};

export default PatientDashboard;



