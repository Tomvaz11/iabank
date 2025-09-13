import { Routes, Route, Navigate } from 'react-router-dom'
import { DashboardPage } from '@/pages/Dashboard'
import { LoginPage } from '@/pages/Login'
import { NotFoundPage } from '@/pages/NotFound'

export function AppRouter() {
  return (
    <Routes>
      <Route path='/' element={<Navigate to='/dashboard' replace />} />
      <Route path='/login' element={<LoginPage />} />
      <Route path='/dashboard' element={<DashboardPage />} />
      <Route path='*' element={<NotFoundPage />} />
    </Routes>
  )
}
