/**
 * Página principal do Dashboard do IABANK.
 * 
 * Exibe visão geral do sistema com KPIs principais,
 * atalhos para funcionalidades e resumo de atividades.
 */

export function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Dashboard - IABANK
          </h1>
          
          <div className="mt-6">
            <div className="card p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Bem-vindo ao IABANK
              </h2>
              <p className="text-gray-600">
                Sistema de gestão de empréstimos em construção.
                Esta página será implementada nas próximas fases do projeto.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}