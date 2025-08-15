import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { NextUIProvider } from '@nextui-org/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { Toaster } from 'react-hot-toast'
import './styles/index.css'
import { AuthProvider } from './hooks/useAuth'
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
      { index: true, element: <PatientDashboard /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { path: 'patients/dashboard', element: <PatientDashboard /> },
      { path: 'patients/profile', element: <ProfilePage /> },
      { path: 'doctors/dashboard', element: <DoctorDashboard /> },
      { path: 'doctors/schedule', element: <SchedulePage /> },
      
      // Appointment and Telemedicine routes
      { path: 'appointments', element: <PatientDashboard /> }, // Will show appointments list
      { path: 'appointments/book', element: <AppointmentBooking /> },
      { path: 'appointments/book/:doctorId', element: <AppointmentBooking /> },
      { path: 'consultations', element: <ConsultationsList /> },
      { path: 'consultations/create', element: <CreateConsultation /> },
      { path: 'consultations/:consultationId', element: <ConsultationRoom /> },
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <NextUIProvider>
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
      </NextUIProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)



