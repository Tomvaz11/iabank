# Processo ADR do IABANK

## Quando criar ADR

- Mudanças na arquitetura fundamental
- Escolha de tecnologias principais
- Padrões de desenvolvimento obrigatórios
- Decisões que afetam múltiplos módulos
- Decisões com impacto significativo no negócio ou na infraestrutura
- Alterações em padrões de segurança ou compliance

## Processo

1. **Identificar necessidade de decisão arquitetural**
   - Questão surge durante desenvolvimento ou planejamento
   - Impacto identificado como significativo
   - Múltiplas alternativas viáveis existem

2. **Criar ADR draft com status "Proposed"**
   - Usar template 0000-template.md
   - Incluir contexto completo
   - Listar alternativas consideradas
   - Detalhar consequências esperadas

3. **Discutir em reunião de arquitetura**
   - Apresentar proposta para equipe
   - Discutir alternativas e trade-offs
   - Identificar riscos e mitigações
   - Buscar consenso técnico

4. **Implementar feedback e revisar**
   - Incorporar sugestões da equipe
   - Refinar texto e justificativas
   - Adicionar detalhes técnicos se necessário
   - Revisar impactos nas decisões existentes

5. **Aprovar e marcar como "Accepted"**
   - Aprovação formal da decisão
   - Atualizar status no arquivo
   - Comunicar decisão para toda equipe
   - Adicionar ao índice do README.md

6. **Implementar decisão**
   - Seguir as diretrizes definidas no ADR
   - Documentar implementação se necessário
   - Criar tasks específicas se aplicável

7. **Atualizar documentação relevante**
   - Atualizar CLAUDE.md se aplicável
   - Modificar documentação técnica
   - Incluir em onboarding materials

## Review

ADRs devem ser revisados trimestralmente para verificar se ainda são válidos.

### Processo de Review

1. **Revisão trimestral**: Verificar se decisões ainda fazem sentido
2. **Identificar superseded**: Marcar ADRs que foram substituídos
3. **Atualizar consequências**: Se impactos mudaram, documentar
4. **Criar novos ADRs**: Se contexto mudou significativamente

## Responsabilidades

### Tech Lead / Arquiteto
- Identificar necessidade de ADRs
- Facilitar discussões arquiteturais
- Garantir qualidade dos documentos
- Conduzir reviews trimestrais

### Desenvolvedores
- Propor ADRs quando necessário
- Participar de discussões
- Seguir diretrizes estabelecidas
- Questionar decisões quando apropriado

## Templates e Convenções

### Numeração
- Usar numeração sequencial (0001, 0002, etc.)
- Não reutilizar números mesmo para ADRs rejeitados
- Manter ordem cronológica

### Status Possíveis
- **Proposed**: Em discussão
- **Accepted**: Aprovado e em uso
- **Rejected**: Rejeitado com justificativa
- **Superseded**: Substituído por ADR mais recente

### Formato do Título
- Usar imperativo: "Usar PostgreSQL para persistência"
- Ser específico e descritivo
- Evitar jargões desnecessários