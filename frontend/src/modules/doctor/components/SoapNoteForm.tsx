import React, { useState, useEffect } from 'react'
import { apiJson } from '@/lib/api'

interface SoapNoteFormProps {
  appointmentId?: number
  patientId?: number
  soapNoteId?: number
  onSave?: (soapNote: any) => void
  onCancel?: () => void
  isEdit?: boolean
}

interface SoapNoteData {
  patient: number
  appointment: number
  subjective: string
  objective: string
  assessment: string
  plan: string
  is_draft: boolean
}

export function SoapNoteForm({ 
  appointmentId, 
  patientId, 
  soapNoteId, 
  onSave, 
  onCancel, 
  isEdit = false 
}: SoapNoteFormProps) {
  const [formData, setFormData] = useState<SoapNoteData>({
    patient: patientId || 0,
    appointment: appointmentId || 0,
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    is_draft: false
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [appointment, setAppointment] = useState<any>(null)

  useEffect(() => {
    if (appointmentId) {
      fetchAppointmentDetails()
    }
    if (soapNoteId && isEdit) {
      fetchSoapNote()
    }
  }, [appointmentId, soapNoteId, isEdit])

  const fetchAppointmentDetails = async () => {
    try {
      const data = await apiJson(`/bookings/api/appointments/${appointmentId}/`)
      setAppointment(data)
      setFormData(prev => ({
        ...prev,
        patient: data.patient.id,
        appointment: data.id
      }))
    } catch (err) {
      setError('Failed to fetch appointment details')
    }
  }

  const fetchSoapNote = async () => {
    try {
      const data = await apiJson(`/core/api/soap-notes/${soapNoteId}/`)
      setFormData({
        patient: data.patient,
        appointment: data.appointment,
        subjective: data.subjective,
        objective: data.objective,
        assessment: data.assessment,
        plan: data.plan,
        is_draft: data.is_draft
      })
    } catch (err) {
      setError('Failed to fetch SOAP note')
    }
  }

  const handleInputChange = (field: keyof SoapNoteData, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      let data
      if (isEdit && soapNoteId) {
        data = await apiJson(`/core/api/soap-notes/${soapNoteId}/`, {
          method: 'PUT',
          body: formData
        })
      } else {
        data = await apiJson('/core/api/soap-notes/', {
          method: 'POST',
          body: formData
        })
      }
      
      onSave?.(data)
    } catch (err: any) {
      setError(err.message || 'Failed to save SOAP note')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveDraft = async () => {
    setFormData(prev => ({ ...prev, is_draft: true }))
    await handleSubmit(new Event('submit') as any)
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {isEdit ? 'Edit SOAP Note' : 'Create SOAP Note'}
        </h2>
        {appointment && (
          <div className="text-sm text-gray-600">
            <p><strong>Patient:</strong> {appointment.patient?.name}</p>
            <p><strong>Appointment:</strong> {appointment.appointment_date} at {appointment.appointment_time}</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Subjective */}
        <div>
          <label htmlFor="subjective" className="block text-sm font-medium text-gray-700 mb-2">
            Subjective (S)
          </label>
          <textarea
            id="subjective"
            value={formData.subjective}
            onChange={(e) => handleInputChange('subjective', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
            placeholder="Patient-reported symptoms, history, and concerns..."
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Document what the patient tells you about their symptoms and medical history
          </p>
        </div>

        {/* Objective */}
        <div>
          <label htmlFor="objective" className="block text-sm font-medium text-gray-700 mb-2">
            Objective (O)
          </label>
          <textarea
            id="objective"
            value={formData.objective}
            onChange={(e) => handleInputChange('objective', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
            placeholder="Observations, test results, vital signs..."
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Document your observations, physical exam findings, and test results
          </p>
        </div>

        {/* Assessment */}
        <div>
          <label htmlFor="assessment" className="block text-sm font-medium text-gray-700 mb-2">
            Assessment (A)
          </label>
          <textarea
            id="assessment"
            value={formData.assessment}
            onChange={(e) => handleInputChange('assessment', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
            placeholder="Your diagnosis, impressions, and clinical reasoning..."
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Document your diagnosis, differential diagnoses, and clinical reasoning
          </p>
        </div>

        {/* Plan */}
        <div>
          <label htmlFor="plan" className="block text-sm font-medium text-gray-700 mb-2">
            Plan (P)
          </label>
          <textarea
            id="plan"
            value={formData.plan}
            onChange={(e) => handleInputChange('plan', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={4}
            placeholder="Treatment plan, follow-up instructions, medications..."
            required
          />
          <p className="mt-1 text-sm text-gray-500">
            Document treatment plan, medications, follow-up instructions, and patient education
          </p>
        </div>

        {/* Draft Checkbox */}
        <div className="flex items-center">
          <input
            id="is_draft"
            type="checkbox"
            checked={formData.is_draft}
            onChange={(e) => handleInputChange('is_draft', e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="is_draft" className="ml-2 block text-sm text-gray-900">
            Save as draft
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          {!isEdit && (
            <button
              type="button"
              onClick={handleSaveDraft}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Draft'}
            </button>
          )}
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Saving...' : (isEdit ? 'Update SOAP Note' : 'Save SOAP Note')}
          </button>
        </div>
      </form>
    </div>
  )
}
