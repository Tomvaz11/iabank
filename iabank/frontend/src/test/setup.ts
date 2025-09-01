/**
 * Configurações de setup para testes da aplicação IABANK.
 * 
 * Configura ambiente de testes com jsdom, mocks globais
 * e utilitários necessários para testing.
 */

import '@testing-library/jest-dom'

// Mock para matchMedia (usado por alguns componentes)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock para ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock para window.location.reload
Object.defineProperty(window, 'location', {
  writable: true,
  value: {
    ...window.location,
    reload: vi.fn(),
  },
})