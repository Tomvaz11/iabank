import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className='flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8'>
      <div className='w-full max-w-md text-center'>
        <div className='mx-auto h-12 w-12 text-gray-400'>
          <svg
            fill='none'
            viewBox='0 0 24 24'
            strokeWidth={1.5}
            stroke='currentColor'
            className='h-12 w-12'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              d='M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z'
            />
          </svg>
        </div>
        <h1 className='mt-4 text-3xl font-bold tracking-tight text-gray-900 sm:text-5xl'>
          404
        </h1>
        <p className='mt-6 text-base leading-7 text-gray-600'>
          Página não encontrada
        </p>
        <div className='mt-10'>
          <Link
            to='/dashboard'
            className='rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
          >
            Voltar ao Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
