/**
 * Ponto de entrada principal da aplicação IABANK Frontend.
 * 
 * Configura React, roteamento, providers e inicializa a aplicação
 * com todas as dependências necessárias.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './app/App.tsx'
import './app/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)