import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import './styles/index.css'
import { AuthProvider } from './hooks/useAuth'
import ErrorBoundary from './components/ErrorBoundary'

// Add console log for debugging
console.log('React app starting...')
console.log('Environment:', import.meta.env)
console.log('API Base:', import.meta.env.VITE_API_BASE)
import AppLayout from './modules/layout/AppLayout'
import LoginPage from './modules/auth/LoginPage'
import RegisterPage from './modules/auth/RegisterPage'
import PatientDashboard from './modules/patient/PatientDashboard'
import DoctorDashboard from './modules/doctor/DoctorDashboard'
import ProfilePage from './modules/account/ProfilePage'
import { SchedulePage } from './modules/doctor/SchedulePage'
import { ConsultationRoom } from './modules/telemedicine/ConsultationRoom'
import ConsultationsList from './modules/telemedicine/ConsultationsList'
import CreateConsultation from './modules/telemedicine/CreateConsultation'
import { AppointmentBooking } from './components/AppointmentBooking'
import AuthGuard from './components/AuthGuard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <AuthGuard><PatientDashboard /></AuthGuard> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      
      // Patient routes
      { 
        path: 'patients/dashboard', 
        element: <AuthGuard requiredRole="patient"><PatientDashboard /></AuthGuard> 
      },
      { 
        path: 'patients/profile', 
        element: <AuthGuard requiredRole="patient"><ProfilePage /></AuthGuard> 
      },
      
      // Doctor routes
      { 
        path: 'doctors/dashboard', 
        element: <AuthGuard requiredRole="doctor"><DoctorDashboard /></AuthGuard> 
      },
      { 
        path: 'doctors/schedule', 
        element: <AuthGuard requiredRole="doctor"><SchedulePage /></AuthGuard> 
      },
      
      // Appointment and Telemedicine routes (authenticated)
      { 
        path: 'appointments', 
        element: <AuthGuard><PatientDashboard /></AuthGuard> 
      },
      { 
        path: 'appointments/book', 
        element: <AuthGuard><AppointmentBooking /></AuthGuard> 
      },
      { 
        path: 'appointments/book/:doctorId', 
        element: <AuthGuard><AppointmentBooking /></AuthGuard> 
      },
      { 
        path: 'consultations', 
        element: <AuthGuard><ConsultationsList /></AuthGuard> 
      },
      { 
        path: 'consultations/create', 
        element: <AuthGuard><CreateConsultation /></AuthGuard> 
      },
      { 
        path: 'consultations/:consultationId', 
        element: <AuthGuard><ConsultationRoom /></AuthGuard> 
      },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)



