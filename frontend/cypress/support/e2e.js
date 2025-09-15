// Cypress support file para configuração global
import '@testing-library/cypress/add-commands'

// Comando customizado para login
Cypress.Commands.add('loginAs', (email, password = 'test123') => {
  cy.session([email], () => {
    cy.visit('/login')
    cy.get('[data-cy=email]').type(email)
    cy.get('[data-cy=password]').type(password)
    cy.get('[data-cy=login-btn]').click()
    cy.url().should('include', '/dashboard')
  })
})

// Comando para setup de dados de teste
Cypress.Commands.add('setupTestData', (tenantId = 'test-tenant') => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/test/setup`,
    body: {
      tenant: tenantId,
      user: {
        email: 'test@test.com',
        password: 'test123',
        role: 'admin'
      },
      customer: {
        name: 'João Silva',
        document_number: '12345678901',
        email: 'joao@test.com'
      }
    }
  })
})

// Comando para criar empréstimo em atraso
Cypress.Commands.add('createOverdueLoan', () => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/test/create-overdue-loan`,
    body: {
      customer_id: 1,
      amount: 10000,
      installments: 12,
      overdue_days: 5
    }
  })
})

// Aguardar elementos aparecerem
Cypress.Commands.add('waitForElement', (selector, timeout = 10000) => {
  cy.get(selector, { timeout }).should('be.visible')
})

// Configurações globais
beforeEach(() => {
  // Interceptar chamadas à API para evitar erros de CORS em desenvolvimento
  cy.intercept('GET', '**/health/', { statusCode: 200, body: { status: 'ok' } })
})

// Suprimir erros não capturados que podem aparecer durante os testes
Cypress.on('uncaught:exception', (err, runnable) => {
  // Retorna false para prevenir que o teste falhe em erros específicos
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false
  }
  return true
})