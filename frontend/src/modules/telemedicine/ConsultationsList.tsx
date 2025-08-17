import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Video, Calendar, Clock, User, Filter, Plus, 
  Search, Eye, Play, Square, X 
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Input } from '../../components/ui/input';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../../components/ui/select';
import { useConsultations, type Consultation, type ConsultationStats } from '../../hooks/useConsultations';
import { useAuth } from '../../hooks/useAuth';
import toast from 'react-hot-toast';

const ConsultationsList: React.FC = () => {
  const { user } = useAuth();
  const {
    consultations,
    loading,
    error,
    fetchConsultations,
    fetchUpcomingConsultations,
    fetchActiveConsultations,
    fetchConsultationStats,
    startConsultation,
    endConsultation,
    cancelConsultation,
  } = useConsultations();

  const [stats, setStats] = useState<ConsultationStats | null>(null);
  const [filteredConsultations, setFilteredConsultations] = useState<Consultation[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');
  const [activeTab, setActiveTab] = useState<'all' | 'upcoming' | 'active' | 'completed'>('all');

  useEffect(() => {
    fetchConsultations();
    loadStats();
  }, []);

  useEffect(() => {
    filterConsultations();
  }, [consultations, searchTerm, statusFilter, providerFilter, activeTab]);

  const loadStats = async () => {
    try {
      const statsData = await fetchConsultationStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const filterConsultations = () => {
    let filtered = consultations;

    // Filter by tab
    const now = new Date();
    switch (activeTab) {
      case 'upcoming':
        filtered = filtered.filter(c => 
          new Date(c.scheduled_start) > now && 
          ['scheduled', 'waiting'].includes(c.status)
        );
        break;
      case 'active':
        filtered = filtered.filter(c => ['waiting', 'in_progress'].includes(c.status));
        break;
      case 'completed':
        filtered = filtered.filter(c => c.status === 'completed');
        break;
      default:
        // Show all
        break;
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(c =>
        c.doctor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        c.meeting_id.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (statusFilter !== 'all') {
      filtered = filtered.filter(c => c.status === statusFilter);
    }

    // Filter by provider
    if (providerFilter !== 'all') {
      filtered = filtered.filter(c => c.video_provider === providerFilter);
    }

    setFilteredConsultations(filtered);
  };

  const handleStartConsultation = async (consultationId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      await startConsultation(consultationId);
      await fetchConsultations();
    } catch (error) {
      console.error('Failed to start consultation:', error);
    }
  };

  const handleEndConsultation = async (consultationId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      await endConsultation(consultationId);
      await fetchConsultations();
    } catch (error) {
      console.error('Failed to end consultation:', error);
    }
  };

  const handleCancelConsultation = async (consultationId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to cancel this consultation?')) {
      return;
    }

    try {
      await cancelConsultation(consultationId);
      await fetchConsultations();
    } catch (error) {
      console.error('Failed to cancel consultation:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-500';
      case 'waiting': return 'bg-yellow-500';
      case 'in_progress': return 'bg-green-500';
      case 'completed': return 'bg-gray-500';
      case 'cancelled': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'jitsi': return '🎥';
      case 'zoom': return '📹';
      case 'google_meet': return '📺';
      default: return '🎬';
    }
  };

  if (loading && consultations.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading consultations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Virtual Consultations</h1>
            <p className="text-gray-600 mt-2">Manage your telemedicine appointments</p>
          </div>
          <Link to="/consultations/create">
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-5 h-5 mr-2" />
              New Consultation
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Calendar className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_consultations}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Play className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.active_consultations}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Clock className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Upcoming</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.upcoming_consultations}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Square className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Completed</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.completed_consultations}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters and Search */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col lg:flex-row gap-4">
              {/* Tabs */}
              <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
                {[
                  { key: 'all', label: 'All' },
                  { key: 'upcoming', label: 'Upcoming' },
                  { key: 'active', label: 'Active' },
                  { key: 'completed', label: 'Completed' },
                ].map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as any)}
                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.key
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Search */}
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search consultations..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Filters */}
              <div className="flex gap-2">
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="scheduled">Scheduled</SelectItem>
                    <SelectItem value="waiting">Waiting</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>

                <Select value={providerFilter} onValueChange={setProviderFilter}>
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Provider" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Providers</SelectItem>
                    <SelectItem value="jitsi">Jitsi Meet</SelectItem>
                    <SelectItem value="zoom">Zoom</SelectItem>
                    <SelectItem value="google_meet">Google Meet</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Consultations List */}
        <div className="grid gap-4">
          {filteredConsultations.length === 0 ? (
            <Card>
              <CardContent className="p-12 text-center">
                <Video className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No consultations found</h3>
                <p className="text-gray-600 mb-6">
                  {searchTerm || statusFilter !== 'all' || providerFilter !== 'all'
                    ? 'Try adjusting your filters or search terms.'
                    : 'Create your first virtual consultation to get started.'
                  }
                </p>
                {!searchTerm && statusFilter === 'all' && providerFilter === 'all' && (
                  <Link to="/consultations/create">
                    <Button className="bg-blue-600 hover:bg-blue-700">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Consultation
                    </Button>
                  </Link>
                )}
              </CardContent>
            </Card>
          ) : (
            filteredConsultations.map((consultation) => (
              <Link
                key={consultation.id}
                to={`/consultations/${consultation.id}`}
                className="block"
              >
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">{getProviderIcon(consultation.video_provider)}</span>
                          </div>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-3 mb-1">
                            <h3 className="text-lg font-semibold text-gray-900 truncate">
                              {user?.role === 'doctor' ? consultation.patient_name : consultation.doctor_name}
                            </h3>
                            <Badge className={`${getStatusColor(consultation.status)} text-white`}>
                              {consultation.status.replace('_', ' ').toUpperCase()}
                            </Badge>
                          </div>
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-600">
                            <div className="flex items-center">
                              <Calendar className="w-4 h-4 mr-1" />
                              {consultation.appointment_date}
                            </div>
                            <div className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              {consultation.appointment_time}
                            </div>
                            <div className="flex items-center">
                              <Video className="w-4 h-4 mr-1" />
                              {consultation.video_provider.replace('_', ' ').toUpperCase()}
                            </div>
                            {consultation.duration_minutes && (
                              <div className="flex items-center">
                                <User className="w-4 h-4 mr-1" />
                                {consultation.duration_minutes} min
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        {consultation.status === 'scheduled' && consultation.can_start && user?.role === 'doctor' && (
                          <Button
                            onClick={(e) => handleStartConsultation(consultation.id, e)}
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Play className="w-4 h-4 mr-1" />
                            Start
                          </Button>
                        )}

                        {consultation.status === 'in_progress' && user?.role === 'doctor' && (
                          <Button
                            onClick={(e) => handleEndConsultation(consultation.id, e)}
                            size="sm"
                            variant="destructive"
                          >
                            <Square className="w-4 h-4 mr-1" />
                            End
                          </Button>
                        )}

                        {['scheduled', 'waiting'].includes(consultation.status) && (
                          <Button
                            onClick={(e) => handleCancelConsultation(consultation.id, e)}
                            size="sm"
                            variant="outline"
                          >
                            <X className="w-4 h-4 mr-1" />
                            Cancel
                          </Button>
                        )}

                        <Button size="sm" variant="outline">
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ConsultationsList;