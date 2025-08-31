/**
 * Página de gerenciamento de clientes do IABANK.
 * 
 * Interface principal para operações com clientes,
 * incluindo cadastro, edição e consulta de histórico.
 */

export function CustomersPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            Clientes
          </h1>
          
          <div className="mt-6">
            <div className="card p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Gestão de Clientes
              </h2>
              <p className="text-gray-600">
                Interface para gerenciamento de clientes será implementada
                nas próximas fases do projeto, incluindo:
              </p>
              
              <ul className="mt-4 space-y-2 text-gray-600">
                <li>• Listagem de clientes com busca</li>
                <li>• Cadastro de novos clientes</li>
                <li>• Edição de dados pessoais</li>
                <li>• Histórico de empréstimos</li>
                <li>• Análise de crédito</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}