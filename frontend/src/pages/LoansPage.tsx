/**
 * Página de gerenciamento de empréstimos do IABANK.
 * 
 * Interface principal para operações com empréstimos,
 * incluindo listagem, criação e gestão de parcelas.
 */

export function LoansPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Empréstimos
          </h1>
          
          <div className="mt-6">
            <div className="card p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Gestão de Empréstimos
              </h2>
              <p className="text-gray-600">
                Interface para gerenciamento de empréstimos será implementada
                nas próximas fases do projeto, incluindo:
              </p>
              
              <ul className="mt-4 space-y-2 text-gray-600">
                <li>• Listagem de empréstimos com filtros</li>
                <li>• Criação de novos contratos</li>
                <li>• Gestão de parcelas e pagamentos</li>
                <li>• Relatórios e dashboards</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}