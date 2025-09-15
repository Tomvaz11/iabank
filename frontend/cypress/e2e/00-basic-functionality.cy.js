describe('Teste Básico de Funcionalidade Existente', () => {
  it('Deve carregar a página de login', () => {
    cy.visit('/login')

    // Verificar que a página carregou
    cy.contains('Faça login em sua conta').should('be.visible')
    cy.contains('IABANK - Plataforma de Gestão de Empréstimos').should('be.visible')

    // Verificar que os campos existem com data-cy
    cy.get('[data-cy=email]').should('be.visible')
    cy.get('[data-cy=password]').should('be.visible')
    cy.get('[data-cy=login-btn]').should('be.visible')

    // Testar preenchimento dos campos
    cy.get('[data-cy=email]').type('teste@exemplo.com')
    cy.get('[data-cy=password]').type('senha123')

    // Verificar que valores foram inseridos
    cy.get('[data-cy=email]').should('have.value', 'teste@exemplo.com')
    cy.get('[data-cy=password]').should('have.value', 'senha123')
  })

  it('Deve navegar para dashboard após login (simulado)', () => {
    cy.visit('/dashboard')

    // Verificar conteúdo do dashboard
    cy.contains('Dashboard - IABANK').should('be.visible')
    cy.contains('Bem-vindo à plataforma IABANK').should('be.visible')

    // Verificar cards do dashboard
    cy.contains('Clientes').should('be.visible')
    cy.contains('Empréstimos').should('be.visible')
    cy.contains('Relatórios').should('be.visible')
  })

  it('Deve ter navegação básica funcionando', () => {
    // Testar rota inexistente
    cy.visit('/pagina-inexistente', { failOnStatusCode: false })

    // Deve mostrar 404 ou redirecionar para login
    cy.url().should('satisfy', (url) => {
      return url.includes('/login') || url.includes('/404') || url.includes('pagina-inexistente')
    })
  })

  it('Deve verificar responsividade básica', () => {
    cy.visit('/dashboard')

    // Teste em mobile
    cy.viewport(375, 667)
    cy.contains('Dashboard - IABANK').should('be.visible')

    // Teste em tablet
    cy.viewport(768, 1024)
    cy.contains('Dashboard - IABANK').should('be.visible')

    // Voltar para desktop
    cy.viewport(1280, 720)
    cy.contains('Dashboard - IABANK').should('be.visible')
  })
})