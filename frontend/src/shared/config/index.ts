export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'IABANK',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  },
} as const
