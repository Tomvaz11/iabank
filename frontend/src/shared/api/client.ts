/**
 * Cliente HTTP configurado para comunicação com a API do IABANK.
 * 
 * Implementa configuração centralizada do Axios com interceptors
 * para autenticação, tratamento de erros e logging.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor para adicionar token de autenticação
apiClient.interceptors.request.use(
  (config) => {
    // TODO: Implementar lógica de token de autenticação
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor para tratamento global de erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: Implementar tratamento global de erros
    return Promise.reject(error);
  }
);