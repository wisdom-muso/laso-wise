import React, { useState, useEffect } from 'react'
import { apiJson } from '@/lib/api'

interface SoapNote {
  id: number
  patient_name: string
  doctor_name: string
  appointment_date: string
  created_at: string
  updated_at: string
  is_draft: boolean
}

interface SoapNoteListProps {
  patientId?: number
  onSelectNote?: (note: SoapNote) => void
  onEditNote?: (noteId: number) => void
  onDeleteNote?: (noteId: number) => void
}

export function SoapNoteList({ 
  patientId, 
  onSelectNote, 
  onEditNote, 
  onDeleteNote 
}: SoapNoteListProps) {
  const [soapNotes, setSoapNotes] = useState<SoapNote[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterDraft, setFilterDraft] = useState(false)

  useEffect(() => {
    fetchSoapNotes()
  }, [patientId])

  const fetchSoapNotes = async () => {
    try {
      setLoading(true)
      let url = '/core/api/soap-notes/'
      if (patientId) {
        url += `?patient=${patientId}`
      }
      const data = await apiJson(url)
      setSoapNotes(data.results || data)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch SOAP notes')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (noteId: number) => {
    if (!confirm('Are you sure you want to delete this SOAP note?')) {
      return
    }

    try {
      await apiJson(`/core/api/soap-notes/${noteId}/`, {
        method: 'DELETE'
      })
      setSoapNotes(prev => prev.filter(note => note.id !== noteId))
      onDeleteNote?.(noteId)
    } catch (err: any) {
      setError(err.message || 'Failed to delete SOAP note')
    }
  }

  const filteredNotes = soapNotes.filter(note => {
    const matchesSearch = 
      note.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      note.doctor_name.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesDraftFilter = !filterDraft || note.is_draft
    
    return matchesSearch && matchesDraftFilter
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
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
          onClick={fetchSoapNotes}
          className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">
            SOAP Notes {patientId && `for Patient`}
          </h2>
          <div className="text-sm text-gray-500">
            {filteredNotes.length} of {soapNotes.length} notes
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by patient or doctor name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="flex items-center">
            <input
              id="filter-draft"
              type="checkbox"
              checked={filterDraft}
              onChange={(e) => setFilterDraft(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="filter-draft" className="ml-2 text-sm text-gray-700">
              Show drafts only
            </label>
          </div>
        </div>
      </div>

      {/* Notes List */}
      <div className="divide-y divide-gray-200">
        {filteredNotes.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <p className="text-gray-500">No SOAP notes found</p>
          </div>
        ) : (
          filteredNotes.map((note) => (
            <div key={note.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-sm font-medium text-gray-900">
                      {note.patient_name}
                    </h3>
                    {note.is_draft && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                        Draft
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-1">
                    <span className="font-medium">Doctor:</span> {note.doctor_name}
                  </p>
                  <p className="text-sm text-gray-600 mb-1">
                    <span className="font-medium">Appointment:</span> {note.appointment_date}
                  </p>
                  <p className="text-xs text-gray-500">
                    Created: {formatDate(note.created_at)}
                    {note.updated_at !== note.created_at && (
                      <span> • Updated: {formatDate(note.updated_at)}</span>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => onSelectNote?.(note)}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View
                  </button>
                  <button
                    onClick={() => onEditNote?.(note.id)}
                    className="text-sm text-green-600 hover:text-green-800 font-medium"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(note.id)}
                    className="text-sm text-red-600 hover:text-red-800 font-medium"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
