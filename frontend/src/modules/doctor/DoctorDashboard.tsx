import React from 'react';
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
import { Separator } from '../../components/ui/separator';
import { Chip } from '../../components/ui/chip';
import { User } from '../../components/ui/user';
import { 
  Stethoscope,
  Users,
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Heart,
  MessageCircle,
  FileText,
  Settings,
  Bell,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Star,
  CheckCircle,
  AlertCircle,
  UserCheck,
  UserX
} from 'lucide-react';

const DoctorDashboard: React.FC = () => {
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

  const stats = [
    { 
      title: 'Total Patients', 
      value: '1,247', 
      change: '+12%', 
      trend: 'up',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    { 
      title: 'Today\'s Appointments', 
      value: '18', 
      change: '+3', 
      trend: 'up',
      icon: Calendar,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    { 
      title: 'Pending Reviews', 
      value: '7', 
      change: '-2', 
      trend: 'down',
      icon: FileText,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    { 
      title: 'Patient Satisfaction', 
      value: '4.8', 
      change: '+0.2', 
      trend: 'up',
      icon: Star,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  const upcomingAppointments = [
    {
      id: 1,
      patient: 'Sarah Johnson',
      time: '09:00 AM',
      type: 'Follow-up',
      status: 'confirmed',
      avatar: '/api/placeholder/40/40'
    },
    {
      id: 2,
      patient: 'Michael Chen',
      time: '10:30 AM',
      type: 'Initial Consultation',
      status: 'confirmed',
      avatar: '/api/placeholder/40/40'
    },
    {
      id: 3,
      patient: 'Emily Davis',
      time: '02:00 PM',
      type: 'Emergency',
      status: 'pending',
      avatar: '/api/placeholder/40/40'
    },
    {
      id: 4,
      patient: 'Robert Wilson',
      time: '03:30 PM',
      type: 'Routine Check',
      status: 'confirmed',
      avatar: '/api/placeholder/40/40'
    }
  ];

  const recentPatients = [
    {
      id: 1,
      name: 'Sarah Johnson',
      lastVisit: '2 days ago',
      nextAppointment: 'Today, 09:00 AM',
      status: 'active',
      avatar: '/api/placeholder/40/40'
    },
    {
      id: 2,
      name: 'Michael Chen',
      lastVisit: '1 week ago',
      nextAppointment: 'Today, 10:30 AM',
      status: 'active',
      avatar: '/api/placeholder/40/40'
    },
    {
      id: 3,
      name: 'Emily Davis',
      lastVisit: '3 days ago',
      nextAppointment: 'Tomorrow, 11:00 AM',
      status: 'pending',
      avatar: '/api/placeholder/40/40'
    }
  ];

  const quickActions = [
    { title: 'Add Patient', icon: Plus, color: 'bg-blue-500' },
    { title: 'Schedule Appointment', icon: Calendar, color: 'bg-green-500' },
    { title: 'View Records', icon: FileText, color: 'bg-purple-500' },
    { title: 'Send Message', icon: MessageCircle, color: 'bg-orange-500' }
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
            <h1 className="text-3xl font-bold text-gray-900">Doctor Dashboard</h1>
            <p className="text-gray-600 mt-1">Welcome back, Dr. Sarah Chen</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              Notifications
            </Button>
            <Button className="bg-primary text-white">
              <Plus className="h-4 w-4 mr-2" />
              New Patient
            </Button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.title}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 shadow-lg border border-gray-100"
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
                <div className="flex items-center space-x-1">
                  {stat.trend === 'up' ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${
                    stat.trend === 'up' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change}
                  </span>
                </div>
      </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-1">{stat.value}</h3>
              <p className="text-gray-600 text-sm">{stat.title}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Upcoming Appointments */}
          <motion.div variants={itemVariants} className="lg:col-span-2">
            <Card className="shadow-lg">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-blue-600" />
                  <CardTitle>Today's Appointments</CardTitle>
                </div>
                <Button size="sm" variant="outline">
                  View All
                </Button>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {upcomingAppointments.map((appointment, index) => (
          <motion.div
                      key={appointment.id}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center justify-between p-4 rounded-lg border border-gray-100 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center space-x-4">
                        <Avatar className="h-10 w-10">
                          <AvatarImage src={appointment.avatar} />
                          <AvatarFallback className="bg-primary text-white">
                            {appointment.patient.split(' ').map(n => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-medium text-gray-900">{appointment.patient}</h4>
                          <p className="text-sm text-gray-600">{appointment.type}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900">{appointment.time}</p>
                          <Badge 
                            variant={appointment.status === 'confirmed' ? 'success' : 'warning'}
                            className="text-xs"
                          >
                            {appointment.status}
                          </Badge>
                        </div>
                        <Button size="sm" variant="ghost">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quick Actions & Recent Patients */}
          <motion.div variants={itemVariants} className="space-y-6">
            {/* Quick Actions */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {quickActions.map((action, index) => (
                  <motion.div
                    key={action.title}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Button 
                      variant="ghost" 
                      className="w-full justify-start p-4 h-auto"
                    >
                      <div className={`w-8 h-8 ${action.color} rounded-lg flex items-center justify-center mr-3`}>
                        <action.icon className="h-4 w-4 text-white" />
                      </div>
                      <span className="font-medium">{action.title}</span>
                    </Button>
          </motion.div>
        ))}
              </CardContent>
            </Card>

            {/* Recent Patients */}
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Recent Patients</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {recentPatients.map((patient, index) => (
                  <motion.div
                    key={patient.id}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center space-x-3 p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={patient.avatar} />
                      <AvatarFallback className="bg-primary text-white">
                        {patient.name.split(' ').map(n => n[0]).join('')}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-900 truncate">{patient.name}</h4>
                      <p className="text-xs text-gray-500">Last visit: {patient.lastVisit}</p>
                      <p className="text-xs text-blue-600">Next: {patient.nextAppointment}</p>
      </div>
                    <Badge 
                      variant={patient.status === 'active' ? 'success' : 'warning'}
                      className="text-xs"
                    >
                      {patient.status}
                    </Badge>
                  </motion.div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Bottom Section - Analytics */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Patient Satisfaction Chart */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Patient Satisfaction</CardTitle>
              <CardDescription>Monthly average ratings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary mb-2">4.8</div>
                  <div className="flex items-center justify-center space-x-1 mb-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star 
                        key={star} 
                        className={`h-5 w-5 ${star <= 4 ? 'text-yellow-400 fill-current' : 'text-gray-300'}`} 
                      />
                    ))}
                  </div>
                  <p className="text-sm text-gray-600">Based on 247 reviews</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <UserCheck className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">New patient registered</p>
                    <p className="text-xs text-gray-500">2 minutes ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Calendar className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Appointment scheduled</p>
                    <p className="text-xs text-gray-500">15 minutes ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <FileText className="h-4 w-4 text-purple-600" />
              </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Medical record updated</p>
                    <p className="text-xs text-gray-500">1 hour ago</p>
          </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default DoctorDashboard;


