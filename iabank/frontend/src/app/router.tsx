/**
 * Configuração de roteamento da aplicação IABANK.
 * 
 * Define as rotas principais e controle de acesso
 * baseado em autenticação e permissões.
 */

import { Routes, Route, Navigate } from 'react-router-dom'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { LoansPage } from '@/pages/LoansPage'
import { CustomersPage } from '@/pages/CustomersPage'

export function AppRouter() {
  // TODO: Implementar lógica de autenticação
  const isAuthenticated = false

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/loans/*" element={<LoansPage />} />
      <Route path="/customers/*" element={<CustomersPage />} />
      <Route path="/login" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}