import React, { useState, useEffect } from 'react'
import { apiJson } from '@/lib/api'

interface EHRRecord {
  id: number
  patient: number
  patient_name: string
  allergies: string
  medications: string
  medical_history: string
  immunizations: string
  lab_results: Record<string, any[]>
  imaging_results: Record<string, any[]>
  vital_signs_history: any[]
  emergency_contacts: any[]
  insurance_info: Record<string, any>
  created_at: string
  updated_at: string
  last_updated_by_name: string
  soap_notes_count: number
}

interface EHRRecordViewProps {
  patientId: number
  isEditable?: boolean
  onSave?: (record: EHRRecord) => void
}

export function EHRRecordView({ patientId, isEditable = false, onSave }: EHRRecordViewProps) {
  const [ehrRecord, setEhrRecord] = useState<EHRRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    allergies: '',
    medications: '',
    medical_history: '',
    immunizations: ''
  })

  useEffect(() => {
    fetchEHRRecord()
  }, [patientId])

  const fetchEHRRecord = async () => {
    try {
      setLoading(true)
      const data = await apiJson(`/core/api/ehr/?patient=${patientId}`)
      if (data.results && data.results.length > 0) {
        const record = data.results[0]
        setEhrRecord(record)
        setFormData({
          allergies: record.allergies || '',
          medications: record.medications || '',
          medical_history: record.medical_history || '',
          immunizations: record.immunizations || ''
        })
      } else {
        // Create new EHR record if none exists
        const newRecord = await apiJson('/core/api/ehr/', {
          method: 'POST',
          body: { patient: patientId }
        })
        setEhrRecord(newRecord)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch EHR record')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!ehrRecord) return

    try {
      const updatedRecord = await apiJson(`/core/api/ehr/${ehrRecord.id}/`, {
        method: 'PUT',
        body: formData
      })
      setEhrRecord(updatedRecord)
      setIsEditing(false)
      onSave?.(updatedRecord)
    } catch (err: any) {
      setError(err.message || 'Failed to save EHR record')
    }
  }

  const handleCancel = () => {
    if (ehrRecord) {
      setFormData({
        allergies: ehrRecord.allergies || '',
        medications: ehrRecord.medications || '',
        medical_history: ehrRecord.medical_history || '',
        immunizations: ehrRecord.immunizations || ''
      })
    }
    setIsEditing(false)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-800">{error}</p>
        <button
          onClick={fetchEHRRecord}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    )
  }

  if (!ehrRecord) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
        <p className="text-yellow-800">No EHR record found for this patient</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Electronic Health Record
            </h2>
            <p className="text-sm text-gray-600">
              Patient: {ehrRecord.patient_name}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isEditable && !isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Edit
              </button>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleCancel}
                  className="px-3 py-1 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Save
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* EHR Content */}
      <div className="p-6 space-y-6">
        {/* Basic Medical Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Allergies */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Allergies
            </label>
            {isEditing ? (
              <textarea
                value={formData.allergies}
                onChange={(e) => setFormData(prev => ({ ...prev, allergies: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                placeholder="Known allergies and reactions..."
              />
            ) : (
              <div className="p-3 bg-gray-50 rounded-md min-h-[80px]">
                {ehrRecord.allergies || (
                  <span className="text-gray-500 italic">No allergies recorded</span>
                )}
              </div>
            )}
          </div>

          {/* Medications */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Current Medications
            </label>
            {isEditing ? (
              <textarea
                value={formData.medications}
                onChange={(e) => setFormData(prev => ({ ...prev, medications: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                rows={4}
                placeholder="Current medications and dosages..."
              />
            ) : (
              <div className="p-3 bg-gray-50 rounded-md min-h-[80px]">
                {ehrRecord.medications || (
                  <span className="text-gray-500 italic">No medications recorded</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Medical History */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Medical History
          </label>
          {isEditing ? (
            <textarea
              value={formData.medical_history}
              onChange={(e) => setFormData(prev => ({ ...prev, medical_history: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              placeholder="Past medical conditions, surgeries, and significant events..."
            />
          ) : (
            <div className="p-3 bg-gray-50 rounded-md min-h-[80px]">
              {ehrRecord.medical_history || (
                <span className="text-gray-500 italic">No medical history recorded</span>
              )}
            </div>
          )}
        </div>

        {/* Immunizations */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Immunization History
          </label>
          {isEditing ? (
            <textarea
              value={formData.immunizations}
              onChange={(e) => setFormData(prev => ({ ...prev, immunizations: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              placeholder="Immunization history and dates..."
            />
          ) : (
            <div className="p-3 bg-gray-50 rounded-md min-h-[80px]">
              {ehrRecord.immunizations || (
                <span className="text-gray-500 italic">No immunization history recorded</span>
              )}
            </div>
          )}
        </div>

        {/* Vital Signs History */}
        {ehrRecord.vital_signs_history && ehrRecord.vital_signs_history.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Vital Signs</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">BP</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">HR</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Temp</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Weight</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {ehrRecord.vital_signs_history.slice(-5).map((vital, index) => (
                    <tr key={index}>
                      <td className="px-3 py-2 text-sm text-gray-900">
                        {vital.timestamp ? formatDate(vital.timestamp) : 'N/A'}
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-900">{vital.blood_pressure || 'N/A'}</td>
                      <td className="px-3 py-2 text-sm text-gray-900">{vital.heart_rate || 'N/A'}</td>
                      <td className="px-3 py-2 text-sm text-gray-900">{vital.temperature || 'N/A'}</td>
                      <td className="px-3 py-2 text-sm text-gray-900">{vital.weight || 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Lab Results */}
        {ehrRecord.lab_results && Object.keys(ehrRecord.lab_results).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Lab Results</h3>
            <div className="space-y-3">
              {Object.entries(ehrRecord.lab_results).map(([testName, results]) => (
                <div key={testName} className="border border-gray-200 rounded-md p-3">
                  <h4 className="font-medium text-gray-900 mb-2">{testName}</h4>
                  {results.slice(-3).map((result, index) => (
                    <div key={index} className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">Date:</span> {result.timestamp ? formatDate(result.timestamp) : 'N/A'}
                      {result.value && <span className="ml-4"><span className="font-medium">Value:</span> {result.value}</span>}
                      {result.unit && <span className="ml-2">({result.unit})</span>}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Imaging Results */}
        {ehrRecord.imaging_results && Object.keys(ehrRecord.imaging_results).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Imaging Results</h3>
            <div className="space-y-3">
              {Object.entries(ehrRecord.imaging_results).map(([studyType, results]) => (
                <div key={studyType} className="border border-gray-200 rounded-md p-3">
                  <h4 className="font-medium text-gray-900 mb-2">{studyType}</h4>
                  {results.slice(-3).map((result, index) => (
                    <div key={index} className="text-sm text-gray-600 mb-1">
                      <span className="font-medium">Date:</span> {result.timestamp ? formatDate(result.timestamp) : 'N/A'}
                      {result.findings && <span className="ml-4"><span className="font-medium">Findings:</span> {result.findings}</span>}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
            <div>
              <span className="font-medium">SOAP Notes:</span> {ehrRecord.soap_notes_count}
            </div>
            <div>
              <span className="font-medium">Last Updated:</span> {formatDate(ehrRecord.updated_at)}
            </div>
            <div>
              <span className="font-medium">Updated By:</span> {ehrRecord.last_updated_by_name}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
