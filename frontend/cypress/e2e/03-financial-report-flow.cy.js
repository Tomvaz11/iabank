describe('Fluxo Geração de Relatório Financeiro', () => {
  beforeEach(() => {
    // Setup data via API com transações financeiras
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/test/setup-financial-data`,
      body: {
        tenant: 'test-tenant',
        loans: 5, // Criar 5 empréstimos
        payments: 10, // Criar 10 pagamentos
        expenses: 3 // Criar 3 despesas
      }
    })
  })

  it('Deve gerar relatório com filtros e exportar', () => {
    // 1. Login como manager
    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    // 2. Verificar interface inicial
    cy.get('[data-cy=report-filters]').should('be.visible')
    cy.get('[data-cy=date-from]').should('be.visible')
    cy.get('[data-cy=date-to]').should('be.visible')
    cy.get('[data-cy=report-type]').should('be.visible')

    // 3. Configurar filtros
    cy.get('[data-cy=date-from]').type('2025-09-01')
    cy.get('[data-cy=date-to]').type('2025-09-14')
    cy.get('[data-cy=report-type]').select('financial-summary')

    // Filtros adicionais
    cy.get('[data-cy=consultant-filter]').select('Todos')
    cy.get('[data-cy=status-filter]').select('Ativos')

    cy.get('[data-cy=generate-report]').click()

    // 4. Aguardar carregamento e verificar dados
    cy.get('[data-cy=loading]').should('be.visible')
    cy.get('[data-cy=loading]').should('not.exist', { timeout: 15000 })

    // Verificar métricas principais
    cy.waitForElement('[data-cy=total-revenue]')
    cy.get('[data-cy=total-revenue]').should('be.visible')
    cy.get('[data-cy=total-expenses]').should('be.visible')
    cy.get('[data-cy=net-profit]').should('be.visible')
    cy.get('[data-cy=active-loans]').should('be.visible')

    // Verificar valores fazem sentido
    cy.get('[data-cy=total-revenue]').then(($el) => {
      const revenueText = $el.text()
      expect(revenueText).to.contain('R$')
      const revenueValue = parseFloat(revenueText.replace(/[^0-9,]/g, '').replace(',', '.'))
      expect(revenueValue).to.be.greaterThan(0)
    })

    cy.get('[data-cy=active-loans]').then(($el) => {
      const loansCount = parseInt($el.text())
      expect(loansCount).to.be.greaterThan(0)
      expect(loansCount).to.be.lessThan(20)
    })

    // 5. Verificar gráficos
    cy.get('[data-cy=revenue-chart]').should('be.visible')
    cy.get('[data-cy=loans-chart]').should('be.visible')

    // 6. Verificar tabela detalhada
    cy.get('[data-cy=financial-table]').should('be.visible')
    cy.get('[data-cy=financial-table]').within(() => {
      cy.get('[data-cy=table-header]').should('contain', 'Cliente')
      cy.get('[data-cy=table-header]').should('contain', 'Empréstimo')
      cy.get('[data-cy=table-header]').should('contain', 'Status')
      cy.get('[data-cy=table-header]').should('contain', 'Valor')

      cy.get('[data-cy=table-row]').should('have.length.at.least', 1)
    })

    // 7. Testar paginação se houver muitos registros
    cy.get('[data-cy=pagination]').then(($pagination) => {
      if ($pagination.length > 0) {
        cy.get('[data-cy=next-page]').click()
        cy.get('[data-cy=current-page]').should('contain', '2')
        cy.get('[data-cy=prev-page]').click()
        cy.get('[data-cy=current-page]').should('contain', '1')
      }
    })

    // 8. Exportar relatório
    cy.get('[data-cy=export-btn]').should('be.visible').click()
    cy.get('[data-cy=export-modal]').should('be.visible')

    // Selecionar formato de exportação
    cy.get('[data-cy=export-format]').select('excel')
    cy.get('[data-cy=include-charts]').check()
    cy.get('[data-cy=confirm-export]').click()

    // 9. Verificar processo de exportação
    cy.get('[data-cy=export-progress]').should('be.visible')
    cy.get('[data-cy=export-success]').should('be.visible', { timeout: 10000 })
    cy.get('[data-cy=download-link]').should('be.visible')

    // Verificar link de download
    cy.get('[data-cy=download-link]').should('have.attr', 'href').and('include', '.xlsx')
  })

  it('Deve gerar relatório de inadimplência', () => {
    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    // Configurar para relatório de inadimplência
    cy.get('[data-cy=report-type]').select('overdue-analysis')
    cy.get('[data-cy=date-from]').type('2025-09-01')
    cy.get('[data-cy=date-to]').type('2025-09-14')
    cy.get('[data-cy=generate-report]').click()

    // Aguardar carregamento
    cy.get('[data-cy=loading]').should('not.exist', { timeout: 15000 })

    // Verificar métricas de inadimplência
    cy.get('[data-cy=overdue-count]').should('be.visible')
    cy.get('[data-cy=overdue-amount]').should('be.visible')
    cy.get('[data-cy=overdue-rate]').should('be.visible')

    // Verificar faixas de atraso
    cy.get('[data-cy=overdue-ranges]').should('be.visible')
    cy.get('[data-cy=overdue-ranges]').within(() => {
      cy.get('[data-cy=range-1-30]').should('be.visible')
      cy.get('[data-cy=range-31-60]').should('be.visible')
      cy.get('[data-cy=range-over-60]').should('be.visible')
    })

    // Verificar gráfico de evolução
    cy.get('[data-cy=overdue-evolution-chart]').should('be.visible')

    // Verificar lista de clientes inadimplentes
    cy.get('[data-cy=overdue-customers-table]').should('be.visible')
    cy.get('[data-cy=overdue-customers-table]').within(() => {
      cy.get('[data-cy=table-row]').should('exist')
      cy.get('[data-cy=customer-name]').should('be.visible')
      cy.get('[data-cy=days-overdue]').should('be.visible')
      cy.get('[data-cy=overdue-amount]').should('be.visible')
    })
  })

  it('Deve filtrar relatório por consultor', () => {
    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    // Configurar filtro por consultor específico
    cy.get('[data-cy=report-type]').select('consultant-performance')
    cy.get('[data-cy=consultant-filter]').select('João Vendedor')
    cy.get('[data-cy=date-from]').type('2025-09-01')
    cy.get('[data-cy=date-to]').type('2025-09-14')
    cy.get('[data-cy=generate-report]').click()

    cy.get('[data-cy=loading]').should('not.exist', { timeout: 15000 })

    // Verificar métricas do consultor
    cy.get('[data-cy=consultant-info]').should('contain', 'João Vendedor')
    cy.get('[data-cy=loans-created]').should('be.visible')
    cy.get('[data-cy=total-volume]').should('be.visible')
    cy.get('[data-cy=commission-earned]').should('be.visible')
    cy.get('[data-cy=conversion-rate]').should('be.visible')

    // Verificar que apenas dados do consultor aparecem
    cy.get('[data-cy=consultant-loans-table]').within(() => {
      cy.get('[data-cy=table-row]').each(($row) => {
        cy.wrap($row).find('[data-cy=consultant-name]').should('contain', 'João Vendedor')
      })
    })
  })

  it('Deve validar filtros de data', () => {
    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    // Tentar gerar relatório sem datas
    cy.get('[data-cy=generate-report]').click()
    cy.get('[data-cy=date-error]').should('contain', 'Data inicial é obrigatória')

    // Tentar com data final anterior à inicial
    cy.get('[data-cy=date-from]').type('2025-09-14')
    cy.get('[data-cy=date-to]').type('2025-09-01')
    cy.get('[data-cy=generate-report]').click()
    cy.get('[data-cy=date-error]').should('contain', 'Data final deve ser posterior')

    // Tentar com período muito longo
    cy.get('[data-cy=date-from]').clear().type('2024-01-01')
    cy.get('[data-cy=date-to]').clear().type('2025-12-31')
    cy.get('[data-cy=generate-report]').click()
    cy.get('[data-cy=date-error]').should('contain', 'Período máximo')
  })

  it('Deve permitir salvar filtros como favoritos', () => {
    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    // Configurar filtros
    cy.get('[data-cy=report-type]').select('financial-summary')
    cy.get('[data-cy=date-from]').type('2025-09-01')
    cy.get('[data-cy=date-to]').type('2025-09-14')
    cy.get('[data-cy=consultant-filter]').select('Todos')

    // Salvar como favorito
    cy.get('[data-cy=save-filters]').click()
    cy.get('[data-cy=filter-name]').type('Relatório Mensal Setembro')
    cy.get('[data-cy=confirm-save]').click()

    cy.get('[data-cy=save-success]').should('be.visible')

    // Verificar que aparece na lista de favoritos
    cy.get('[data-cy=saved-filters]').should('contain', 'Relatório Mensal Setembro')

    // Limpar filtros e aplicar favorito
    cy.get('[data-cy=clear-filters]').click()
    cy.get('[data-cy=date-from]').should('have.value', '')

    cy.get('[data-cy=saved-filters]').select('Relatório Mensal Setembro')
    cy.get('[data-cy=load-filters]').click()

    // Verificar que filtros foram carregados
    cy.get('[data-cy=report-type]').should('have.value', 'financial-summary')
    cy.get('[data-cy=date-from]').should('have.value', '2025-09-01')
    cy.get('[data-cy=date-to]').should('have.value', '2025-09-14')
  })

  it('Deve exibir relatório vazio quando não há dados', () => {
    // Setup sem dados
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/test/clear-financial-data`,
      body: { tenant: 'test-tenant' }
    })

    cy.loginAs('manager@test.com')
    cy.visit('/reports')

    cy.get('[data-cy=report-type]').select('financial-summary')
    cy.get('[data-cy=date-from]').type('2025-09-01')
    cy.get('[data-cy=date-to]').type('2025-09-14')
    cy.get('[data-cy=generate-report]').click()

    cy.get('[data-cy=loading]').should('not.exist', { timeout: 15000 })

    // Verificar estado vazio
    cy.get('[data-cy=empty-report]').should('be.visible')
    cy.get('[data-cy=empty-message]').should('contain', 'Nenhum dado encontrado')
    cy.get('[data-cy=empty-suggestions]').should('be.visible')

    // Verificar que botão de exportar está desabilitado
    cy.get('[data-cy=export-btn]').should('be.disabled')
  })
})