import React, { useState, useEffect } from 'react'
import { apiJson } from '@/lib/api'
import { SoapNoteForm } from '../components/SoapNoteForm'
import { SoapNoteList } from '../components/SoapNoteList'
import { EHRRecordView } from '../components/EHRRecordView'

interface DoctorDashboardProps {
  // Add any props if needed
}

export function DoctorDashboard({}: DoctorDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedPatient, setSelectedPatient] = useState<any>(null)
  const [showSoapForm, setShowSoapForm] = useState(false)
  const [selectedSoapNote, setSelectedSoapNote] = useState<any>(null)
  const [dashboardData, setDashboardData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const data = await apiJson('/doctors/api/dashboard/')
      setDashboardData(data)
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePatientSelect = (patient: any) => {
    setSelectedPatient(patient)
    setActiveTab('patient-records')
  }

  const handleCreateSoapNote = (appointmentId: number) => {
    setSelectedPatient({ id: appointmentId })
    setShowSoapForm(true)
    setActiveTab('soap-notes')
  }

  const handleSoapNoteSave = (soapNote: any) => {
    setShowSoapForm(false)
    setSelectedSoapNote(null)
    // Refresh the SOAP notes list
    setActiveTab('soap-notes')
  }

  const handleSoapNoteEdit = (noteId: number) => {
    setSelectedSoapNote({ id: noteId })
    setShowSoapForm(true)
    setActiveTab('soap-notes')
  }

  const tabs = [
    { id: 'overview', name: 'Overview', icon: '📊' },
    { id: 'appointments', name: 'Appointments', icon: '📅' },
    { id: 'soap-notes', name: 'SOAP Notes', icon: '📝' },
    { id: 'patient-records', name: 'Patient Records', icon: '🏥' },
    { id: 'patients', name: 'My Patients', icon: '👥' }
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
          <h1 className="text-3xl font-bold text-gray-900">Doctor Dashboard</h1>
          <p className="mt-2 text-gray-600">Manage your patients, appointments, and medical records</p>
        </div>

        {/* Stats Overview */}
        {activeTab === 'overview' && dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <span className="text-2xl">👥</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Patients</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.total_patients}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <span className="text-2xl">📅</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Today's Appointments</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.today_patients}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <span className="text-2xl">📝</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Appointments</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.total_appointments}</p>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <span className="text-2xl">⏰</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Upcoming</p>
                  <p className="text-2xl font-semibold text-gray-900">{dashboardData.upcoming?.length || 0}</p>
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
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upcoming Appointments</h2>
              {dashboardData.upcoming && dashboardData.upcoming.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.upcoming.map((appointment: any) => (
                    <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {appointment.patient.name.split(' ').map((n: string) => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{appointment.patient.name}</p>
                          <p className="text-sm text-gray-600">
                            {appointment.appointment_date} at {appointment.appointment_time}
                          </p>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleCreateSoapNote(appointment.id)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Create SOAP Note
                        </button>
                        <button
                          onClick={() => handlePatientSelect(appointment.patient)}
                          className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                        >
                          View Records
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No upcoming appointments</p>
              )}
            </div>
          )}

          {/* SOAP Notes Tab */}
          {activeTab === 'soap-notes' && (
            <div className="p-6">
              {showSoapForm ? (
                <SoapNoteForm
                  appointmentId={selectedPatient?.id}
                  soapNoteId={selectedSoapNote?.id}
                  onSave={handleSoapNoteSave}
                  onCancel={() => setShowSoapForm(false)}
                  isEdit={!!selectedSoapNote}
                />
              ) : (
                <div>
                  <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-semibold text-gray-900">SOAP Notes</h2>
                    <button
                      onClick={() => setShowSoapForm(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Create New SOAP Note
                    </button>
                  </div>
                  <SoapNoteList
                    onSelectNote={(note) => setSelectedSoapNote(note)}
                    onEditNote={handleSoapNoteEdit}
                  />
                </div>
              )}
            </div>
          )}

          {/* Patient Records Tab */}
          {activeTab === 'patient-records' && selectedPatient && (
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">
                  Patient Records - {selectedPatient.name}
                </h2>
                <button
                  onClick={() => setSelectedPatient(null)}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  ← Back to Patients
                </button>
              </div>
              <EHRRecordView
                patientId={selectedPatient.id}
                isEditable={true}
                onSave={(record) => console.log('EHR record saved:', record)}
              />
            </div>
          )}

          {/* My Patients Tab */}
          {activeTab === 'patients' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">My Patients</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {dashboardData?.upcoming?.map((appointment: any) => (
                  <div key={appointment.patient.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-gray-600">
                          {appointment.patient.name.split(' ').map((n: string) => n[0]).join('')}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{appointment.patient.name}</p>
                        <p className="text-sm text-gray-600">Age: {appointment.patient.age || 'N/A'}</p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handlePatientSelect(appointment.patient)}
                        className="flex-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        View Records
                      </button>
                      <button
                        onClick={() => handleCreateSoapNote(appointment.id)}
                        className="flex-1 px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                      >
                        SOAP Note
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Appointments Tab */}
          {activeTab === 'appointments' && (
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">All Appointments</h2>
              {dashboardData?.upcoming && dashboardData.upcoming.length > 0 ? (
                <div className="space-y-4">
                  {dashboardData.upcoming.map((appointment: any) => (
                    <div key={appointment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-600">
                            {appointment.patient.name.split(' ').map((n: string) => n[0]).join('')}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{appointment.patient.name}</p>
                          <p className="text-sm text-gray-600">
                            {appointment.appointment_date} at {appointment.appointment_time}
                          </p>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            appointment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                            appointment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {appointment.status}
                          </span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleCreateSoapNote(appointment.id)}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Create SOAP Note
                        </button>
                        <button
                          onClick={() => handlePatientSelect(appointment.patient)}
                          className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                        >
                          View Records
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500">No appointments found</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
