describe('Fluxo Processamento de Pagamento', () => {
  beforeEach(() => {
    // Mock de dados para teste de pagamento
    cy.intercept('POST', '**/test/setup*', { statusCode: 200, body: { status: 'success' } })
    cy.intercept('POST', '**/create-overdue-loan*', { statusCode: 200, body: { loan_id: 1 } })
    cy.intercept('GET', '**/loans*', { statusCode: 200, body: [{ id: 1, status: 'overdue' }] })
    cy.intercept('POST', '**/payments*', { statusCode: 201, body: { id: 1, status: 'completed' } })
  })

  it('Deve processar pagamento e atualizar status', () => {
    // Setup: criar empréstimo com parcela vencida
    cy.createOverdueLoan()

    // 1. Login e navegação
    cy.loginAs('collector@test.com')
    cy.visit('/payments')

    // 2. Localizar parcela em atraso
    cy.get('[data-cy=overdue-filter]').click()
    cy.waitForElement('[data-cy=payment-row]')
    cy.get('[data-cy=payment-row]').should('have.length.at.least', 1)

    // Verificar informações da parcela em atraso
    cy.get('[data-cy=payment-row]').first().within(() => {
      cy.get('[data-cy=customer-name]').should('contain', 'João Silva')
      cy.get('[data-cy=installment-status]').should('contain', 'Em atraso')
      cy.get('[data-cy=days-overdue]').should('contain', '5 dias')
      cy.get('[data-cy=overdue-fee]').should('be.visible')
    })

    cy.get('[data-cy=payment-row]').first().click()

    // 3. Registrar pagamento
    cy.url().should('include', '/payments/installment/')

    // Verificar detalhes da parcela
    cy.get('[data-cy=installment-details]').within(() => {
      cy.get('[data-cy=original-amount]').should('be.visible')
      cy.get('[data-cy=overdue-fee]').should('be.visible')
      cy.get('[data-cy=total-amount]').should('be.visible')
    })

    // Registrar pagamento total
    cy.get('[data-cy=payment-amount]').type('956.78')
    cy.get('[data-cy=payment-date]').type('2025-09-14')
    cy.get('[data-cy=payment-method]').select('PIX')
    cy.get('[data-cy=payment-notes]').type('Pagamento via PIX - Cliente João Silva')

    cy.get('[data-cy=register-payment]').click()

    // 4. Verificação de confirmação
    cy.get('[data-cy=payment-success]').should('be.visible')
    cy.get('[data-cy=payment-success]').should('contain', 'Pagamento registrado com sucesso')

    // Verificar atualização do status
    cy.get('[data-cy=installment-status]').should('contain', 'Pago')
    cy.get('[data-cy=payment-history]').should('be.visible')

    // Verificar histórico de pagamentos
    cy.get('[data-cy=payment-history]').within(() => {
      cy.get('[data-cy=payment-item]').should('have.length', 1)
      cy.get('[data-cy=payment-item]').first().within(() => {
        cy.get('[data-cy=payment-amount]').should('contain', 'R$ 956,78')
        cy.get('[data-cy=payment-method]').should('contain', 'PIX')
        cy.get('[data-cy=payment-date]').should('contain', '14/09/2025')
      })
    })

    // 5. Verificar atualização no dashboard
    cy.visit('/dashboard')
    cy.waitForElement('[data-cy=payments-today]')
    cy.get('[data-cy=payments-today]').should('contain', '1')

    // Verificar métricas atualizadas
    cy.get('[data-cy=total-received-today]').should('contain', 'R$ 956,78')
    cy.get('[data-cy=overdue-count]').should('not.contain', 'João Silva') // Removido da lista de atrasos
  })

  it('Deve processar pagamento parcial', () => {
    cy.createOverdueLoan()
    cy.loginAs('collector@test.com')
    cy.visit('/payments')

    // Localizar parcela e abrir detalhes
    cy.get('[data-cy=overdue-filter]').click()
    cy.get('[data-cy=payment-row]').first().click()

    // Registrar pagamento parcial
    cy.get('[data-cy=payment-amount]').type('500.00') // Menos que o valor total
    cy.get('[data-cy=payment-date]').type('2025-09-14')
    cy.get('[data-cy=payment-method]').select('Dinheiro')
    cy.get('[data-cy=payment-notes]').type('Pagamento parcial - primeira parte')

    cy.get('[data-cy=register-payment]').click()

    // Verificar que parcela continua em aberto
    cy.get('[data-cy=payment-success]').should('be.visible')
    cy.get('[data-cy=installment-status]').should('contain', 'Parcial')

    // Verificar saldo devedor atualizado
    cy.get('[data-cy=remaining-amount]').should('be.visible')
    cy.get('[data-cy=remaining-amount]').then(($el) => {
      const remainingText = $el.text()
      const remainingValue = parseFloat(remainingText.replace(/[^0-9,]/g, '').replace(',', '.'))
      expect(remainingValue).to.be.lessThan(956.78) // Menor que o valor original
      expect(remainingValue).to.be.greaterThan(400) // Mas ainda há saldo
    })

    // Registrar segundo pagamento
    cy.get('[data-cy=payment-amount]').clear().type('456.78') // Complemento
    cy.get('[data-cy=payment-method]').select('Transferência')
    cy.get('[data-cy=payment-notes]').clear().type('Pagamento final - quitação')

    cy.get('[data-cy=register-payment]').click()

    // Verificar quitação completa
    cy.get('[data-cy=payment-success]').should('be.visible')
    cy.get('[data-cy=installment-status]').should('contain', 'Pago')
    cy.get('[data-cy=remaining-amount]').should('contain', 'R$ 0,00')

    // Verificar histórico com 2 pagamentos
    cy.get('[data-cy=payment-history]').within(() => {
      cy.get('[data-cy=payment-item]').should('have.length', 2)
    })
  })

  it('Deve validar formulário de pagamento', () => {
    cy.createOverdueLoan()
    cy.loginAs('collector@test.com')
    cy.visit('/payments')

    // Abrir detalhes da parcela
    cy.get('[data-cy=overdue-filter]').click()
    cy.get('[data-cy=payment-row]').first().click()

    // Tentar registrar sem valor
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=amount-error]').should('contain', 'Valor é obrigatório')

    // Tentar com valor inválido
    cy.get('[data-cy=payment-amount]').type('0')
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=amount-error]').should('contain', 'Valor deve ser maior que zero')

    // Tentar com valor maior que o saldo devedor
    cy.get('[data-cy=payment-amount]').clear().type('2000.00') // Muito alto
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=amount-error]').should('contain', 'Valor não pode ser maior')

    // Tentar sem selecionar método de pagamento
    cy.get('[data-cy=payment-amount]').clear().type('500.00')
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=method-error]').should('contain', 'Método de pagamento é obrigatório')

    // Tentar com data futura
    cy.get('[data-cy=payment-method]').select('PIX')
    cy.get('[data-cy=payment-date]').type('2025-12-31') // Data futura
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=date-error]').should('contain', 'Data não pode ser futura')
  })

  it('Deve permitir estornar pagamento', () => {
    // Primeiro registrar um pagamento
    cy.createOverdueLoan()
    cy.loginAs('collector@test.com')
    cy.visit('/payments')

    cy.get('[data-cy=overdue-filter]').click()
    cy.get('[data-cy=payment-row]').first().click()

    // Registrar pagamento
    cy.get('[data-cy=payment-amount]').type('956.78')
    cy.get('[data-cy=payment-date]').type('2025-09-14')
    cy.get('[data-cy=payment-method]').select('PIX')
    cy.get('[data-cy=register-payment]').click()
    cy.get('[data-cy=payment-success]').should('be.visible')

    // Agora estornar o pagamento
    cy.get('[data-cy=payment-history]').within(() => {
      cy.get('[data-cy=payment-item]').first().within(() => {
        cy.get('[data-cy=reverse-payment]').click()
      })
    })

    // Confirmar estorno
    cy.get('[data-cy=reverse-modal]').should('be.visible')
    cy.get('[data-cy=reverse-reason]').type('Erro no registro - valor incorreto')
    cy.get('[data-cy=confirm-reverse]').click()

    // Verificar estorno
    cy.get('[data-cy=reverse-success]').should('be.visible')
    cy.get('[data-cy=installment-status]').should('contain', 'Em atraso') // Volta ao status anterior

    // Verificar histórico com pagamento estornado
    cy.get('[data-cy=payment-history]').within(() => {
      cy.get('[data-cy=payment-item]').should('have.length', 2) // Original + estorno
      cy.get('[data-cy=payment-item]').last().within(() => {
        cy.get('[data-cy=payment-type]').should('contain', 'Estorno')
        cy.get('[data-cy=payment-amount]').should('contain', '- R$ 956,78')
      })
    })
  })
})