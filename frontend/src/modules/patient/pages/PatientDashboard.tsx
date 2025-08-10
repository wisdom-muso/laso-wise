import React, { useState, useEffect } from 'react'
import { apiJson } from '@/lib/api'
import { PatientEHRView } from '../components/PatientEHRView'

interface PatientDashboardProps {
  // Add any props if needed
}

export function PatientDashboard({}: PatientDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const data = await apiJson('/patients/api/dashboard/')
      setDashboardData(data)
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'appointments', name: 'Appointments', icon: '📅' },
    { id: 'health-records', name: 'My Health Records', icon: '🏥' },
    { id: 'prescriptions', name: 'Prescriptions', icon: '💊' }
  ]

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Patient Dashboard</h1>
          <p className="mt-2 text-gray-600">View your appointments, health records, and prescriptions</p>
        </div>

        {/* Stats Overview */}
        {activeTab === 'overview' && dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <span className="text-2xl">📅</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Upcoming Appointments</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.upcoming_count}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <span className="text-2xl">👨‍⚕️</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Doctors Consulted</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.doctors_consulted}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <span className="text-2xl">💊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Prescriptions</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.prescriptions_count}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <span className="text-2xl">📝</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Health Score</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.health_score || 'N/A'}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow">
          {/* Overview Tab */}
          {activeTab === 'overview' && dashboardData && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Appointments</h2>
              {dashboardData.appointments && dashboardData.appointments.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.appointments.map((appointment: any) => (
                    <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {appointment.doctor.name.split(' ').map((n: string) => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Dr. {appointment.doctor.name}</p>
                          <p className="text-sm text-gray-600">
                            {appointment.appointment_date} at {appointment.appointment_time}
                          </p>
                          <p className="text-sm text-gray-500">{appointment.doctor.specialization}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                          appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          appointment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No recent appointments</p>
              )}
            </div>
          )}

          {/* Appointments Tab */}
          {activeTab === 'appointments' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">All Appointments</h2>
              {dashboardData?.appointments && dashboardData.appointments.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.appointments.map((appointment: any) => (
                    <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {appointment.doctor.name.split(' ').map((n: string) => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Dr. {appointment.doctor.name}</p>
                          <p className="text-sm text-gray-600">
                            {appointment.appointment_date} at {appointment.appointment_time}
                          </p>
                          <p className="text-sm text-gray-500">{appointment.doctor.specialization}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                          appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          appointment.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No appointments found</p>
              )}
            </div>
          )}

          {/* Health Records Tab */}
          {activeTab === 'health-records' && (
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-gray-900">My Health Records</h2>
                <p className="text-sm text-gray-600 mt-1">
                  View your complete medical history, medications, and health information
                </p>
              </div>
              <PatientEHRView />
            </div>
          )}

          {/* Prescriptions Tab */}
          {activeTab === 'prescriptions' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">My Prescriptions</h2>
              {dashboardData?.prescriptions && dashboardData.prescriptions.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.prescriptions.map((prescription: any) => (
                    <div key={prescription.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="font-medium text-gray-900">Dr. {prescription.doctor_name}</p>
                          <p className="text-sm text-gray-600">{prescription.created_at}</p>
                        </div>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div>
                          <p className="text-sm font-medium text-gray-700">Symptoms:</p>
                          <p className="text-sm text-gray-600">{prescription.symptoms}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">Diagnosis:</p>
                          <p className="text-sm text-gray-600">{prescription.diagnosis}</p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-700">Medications:</p>
                          <div className="text-sm text-gray-600" 
                               dangerouslySetInnerHTML={{ __html: prescription.medications }} />
                        </div>
                        {prescription.notes && (
                          <div>
                            <p className="text-sm font-medium text-gray-700">Notes:</p>
                            <p className="text-sm text-gray-600">{prescription.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No prescriptions found</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
