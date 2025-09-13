export function DashboardPage() {
  return (
    <div className='p-6'>
      <h1 className='text-3xl font-bold text-gray-900'>Dashboard - IABANK</h1>
      <p className='mt-4 text-gray-600'>
        Bem-vindo à plataforma IABANK de gestão de empréstimos.
      </p>
      <div className='mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3'>
        <div className='rounded-lg bg-white p-6 shadow'>
          <h2 className='text-lg font-semibold text-gray-900'>Clientes</h2>
          <p className='mt-2 text-sm text-gray-600'>
            Gerencie seus clientes e análises de crédito
          </p>
        </div>
        <div className='rounded-lg bg-white p-6 shadow'>
          <h2 className='text-lg font-semibold text-gray-900'>Empréstimos</h2>
          <p className='mt-2 text-sm text-gray-600'>
            Crie e gerencie empréstimos
          </p>
        </div>
        <div className='rounded-lg bg-white p-6 shadow'>
          <h2 className='text-lg font-semibold text-gray-900'>Relatórios</h2>
          <p className='mt-2 text-sm text-gray-600'>
            Visualize relatórios financeiros
          </p>
        </div>
      </div>
    </div>
  )
}
