/**
 * Configurações de ambiente da aplicação IABANK.
 * 
 * Centraliza variáveis de ambiente e configurações
 * específicas para diferentes ambientes de execução.
 */

export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    timeout: 10000,
  },
  app: {
    name: 'IABANK',
    version: '0.1.0',
    environment: import.meta.env.MODE || 'development',
  },
} as const;