import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/Registerpage'
import DashboardPage from './pages/Dashboardpage'
import DocumentsPage from './pages/DocumentsPage'
import ChatPage from './pages/ChatPage'
import CategoriesPage from './pages/CategoriesPage'
import ReportsPage from './pages/ReportsPage'
import UsersPage from './pages/UsersPage'
import SettingsPage from './pages/SettingsPage'

function ProtectedLayout() {
  const { user } = useAuth()
  const adminPage = (page: React.ReactElement) =>
    user?.role === 'admin' ? page : <Navigate to="/chat" replace />

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/categories" element={adminPage(<CategoriesPage />)} />
          <Route path="/reports" element={adminPage(<ReportsPage />)} />
          <Route path="/users" element={adminPage(<UsersPage />)} />
          <Route path="/settings" element={adminPage(<SettingsPage />)} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const { token } = useAuth()

  return (
    <Routes>
      <Route path="/" element={<Navigate to={token ? "/dashboard" : "/login"} replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/*"
        element={token ? <ProtectedLayout /> : <Navigate to="/login" />}
      />
    </Routes>
  )
}
