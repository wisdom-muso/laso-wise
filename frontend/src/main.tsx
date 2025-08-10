import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import './styles/index.css'
import { AppLayout } from './modules/layout/AppLayout'
import { LoginPage } from './modules/auth/LoginPage'
import { RegisterPage } from './modules/auth/RegisterPage'
import { PatientDashboard } from './modules/patient/PatientDashboard'
import { DoctorDashboard } from './modules/doctor/DoctorDashboard'
import { ProfilePage } from './modules/account/ProfilePage'
import { SchedulePage } from './modules/doctor/SchedulePage'

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
    ],
  },
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)



