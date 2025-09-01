/**
 * Página de autenticação do IABANK.
 * 
 * Interface de login para acesso ao sistema,
 * integrada com sistema de autenticação do backend.
 */

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            IABANK
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sistema de Gestão de Empréstimos
          </p>
        </div>
        
        <div className="card p-8">
          <form className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Usuário
              </label>
              <input
                id="username"
                name="username"
                type="text"
                className="input mt-1"
                placeholder="Digite seu usuário"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Senha
              </label>
              <input
                id="password"
                name="password"
                type="password"
                className="input mt-1"
                placeholder="Digite sua senha"
              />
            </div>
            
            <div>
              <button
                type="submit"
                className="btn btn-primary w-full"
              >
                Entrar
              </button>
            </div>
          </form>
          
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500">
              Interface de login será implementada nas próximas fases.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}