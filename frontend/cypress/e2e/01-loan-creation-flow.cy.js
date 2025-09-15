describe('Fluxo Criação de Empréstimo Completo', () => {
  beforeEach(() => {
    // Setup data via API
    cy.setupTestData('test-tenant')
  })

  it('Deve completar criação de empréstimo: login → simulação → aprovação', () => {
    // 1. Login
    cy.visit('/login')
    cy.get('[data-cy=email]').type('test@test.com')
    cy.get('[data-cy=password]').type('test123')
    cy.get('[data-cy=login-btn]').click()

    // 2. Navegação para simulação
    cy.url().should('include', '/dashboard')
    cy.get('[data-cy=new-loan-btn]').click()

    // 3. Simulação
    cy.get('[data-cy=customer-select]').select('João Silva')
    cy.get('[data-cy=loan-amount]').type('10000')
    cy.get('[data-cy=installments]').type('12')
    cy.get('[data-cy=simulate-btn]').click()

    // 4. Verificação cálculos
    cy.waitForElement('[data-cy=monthly-payment]')
    cy.get('[data-cy=monthly-payment]').should('contain', 'R$')
    cy.get('[data-cy=total-amount]').should('contain', 'R$')
    cy.get('[data-cy=cet-rate]').should('be.visible')

    // Verificar que os valores calculados fazem sentido
    cy.get('[data-cy=monthly-payment]').then(($el) => {
      const monthlyText = $el.text()
      const monthlyValue = parseFloat(monthlyText.replace(/[^0-9,]/g, '').replace(',', '.'))
      expect(monthlyValue).to.be.greaterThan(800) // Valor mínimo esperado
      expect(monthlyValue).to.be.lessThan(1200) // Valor máximo esperado
    })

    // 5. Aprovação
    cy.get('[data-cy=approve-btn]').click()
    cy.get('[data-cy=confirm-modal]').should('be.visible')

    // Verificar informações no modal de confirmação
    cy.get('[data-cy=confirm-modal]').within(() => {
      cy.get('[data-cy=customer-name]').should('contain', 'João Silva')
      cy.get('[data-cy=loan-amount]').should('contain', 'R$ 10.000,00')
      cy.get('[data-cy=installments-count]').should('contain', '12')
    })

    cy.get('[data-cy=confirm-approve]').click()

    // 6. Verificação final
    cy.url().should('include', '/loans/')
    cy.get('[data-cy=loan-status]').should('contain', 'Aprovado')

    // Verificar que o empréstimo aparece na lista
    cy.get('[data-cy=loan-list]').within(() => {
      cy.get('[data-cy=loan-row]').should('exist')
      cy.get('[data-cy=customer-name]').should('contain', 'João Silva')
      cy.get('[data-cy=loan-amount]').should('contain', 'R$ 10.000,00')
    })

    // 7. Verificar detalhes do empréstimo
    cy.get('[data-cy=loan-row]').first().click()
    cy.url().should('match', /\/loans\/\d+/)

    // Verificar detalhes na página
    cy.get('[data-cy=loan-details]').within(() => {
      cy.get('[data-cy=customer-info]').should('contain', 'João Silva')
      cy.get('[data-cy=principal-amount]').should('contain', 'R$ 10.000,00')
      cy.get('[data-cy=installments-table]').should('be.visible')
    })

    // Verificar parcelas geradas
    cy.get('[data-cy=installments-table]').within(() => {
      cy.get('[data-cy=installment-row]').should('have.length', 12)

      // Verificar primeira parcela
      cy.get('[data-cy=installment-row]').first().within(() => {
        cy.get('[data-cy=installment-number]').should('contain', '1')
        cy.get('[data-cy=installment-status]').should('contain', 'Pendente')
        cy.get('[data-cy=installment-amount]').should('contain', 'R$')
        cy.get('[data-cy=due-date]').should('be.visible')
      })
    })
  })

  it('Deve validar formulário de simulação com dados inválidos', () => {
    cy.loginAs('test@test.com')
    cy.visit('/loans/new')

    // Tentar simular sem selecionar cliente
    cy.get('[data-cy=simulate-btn]').click()
    cy.get('[data-cy=customer-error]').should('contain', 'Selecione um cliente')

    // Selecionar cliente e tentar com valor inválido
    cy.get('[data-cy=customer-select]').select('João Silva')
    cy.get('[data-cy=loan-amount]').type('100') // Valor muito baixo
    cy.get('[data-cy=simulate-btn]').click()
    cy.get('[data-cy=amount-error]').should('contain', 'Valor mínimo')

    // Tentar com valor muito alto
    cy.get('[data-cy=loan-amount]').clear().type('1000000') // 1 milhão
    cy.get('[data-cy=simulate-btn]').click()
    cy.get('[data-cy=amount-error]').should('contain', 'Valor máximo')

    // Tentar com parcelas inválidas
    cy.get('[data-cy=loan-amount]').clear().type('10000')
    cy.get('[data-cy=installments]').clear().type('100') // Muitas parcelas
    cy.get('[data-cy=simulate-btn]').click()
    cy.get('[data-cy=installments-error]').should('contain', 'Máximo')
  })

  it('Deve permitir cancelar aprovação de empréstimo', () => {
    cy.setupTestData('test-tenant')
    cy.loginAs('test@test.com')
    cy.visit('/loans/new')

    // Simular empréstimo
    cy.get('[data-cy=customer-select]').select('João Silva')
    cy.get('[data-cy=loan-amount]').type('5000')
    cy.get('[data-cy=installments]').type('6')
    cy.get('[data-cy=simulate-btn]').click()

    // Aguardar cálculo e tentar aprovar
    cy.waitForElement('[data-cy=approve-btn]')
    cy.get('[data-cy=approve-btn]').click()
    cy.get('[data-cy=confirm-modal]').should('be.visible')

    // Cancelar
    cy.get('[data-cy=cancel-approve]').click()
    cy.get('[data-cy=confirm-modal]').should('not.exist')

    // Verificar que ainda está na simulação
    cy.get('[data-cy=simulation-results]').should('be.visible')
    cy.get('[data-cy=approve-btn]').should('be.visible')
  })
})