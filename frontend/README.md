# IABANK Frontend

Frontend React com TypeScript para a plataforma SaaS de gestão de empréstimos IABANK.

## Arquitetura

### Feature-Sliced Design (FSD)

O projeto segue a metodologia Feature-Sliced Design com as seguintes camadas:

```
src/
├── app/           # Configuração global da aplicação
├── pages/         # Páginas da aplicação
├── features/      # Funcionalidades de negócio
├── entities/      # Entidades de domínio
├── widgets/       # Componentes compostos
└── shared/        # Código compartilhado
```

### Stack Tecnológica

- **React 18+** - Biblioteca de interface
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **TanStack Query** - Gerenciamento de estado servidor
- **Zustand** - Gerenciamento de estado cliente
- **React Router** - Roteamento
- **Tailwind CSS** - Estilos utilitários
- **Vitest** - Framework de testes
- **ESLint + Prettier** - Linting e formatação

## Scripts Disponíveis

```bash
# Desenvolvimento
npm run dev          # Inicia servidor de desenvolvimento na porta 3000

# Build
npm run build        # Gera build de produção
npm run preview      # Preview do build de produção

# Testes
npm test             # Executa testes em modo watch
npm run test:ui      # Executa testes com interface visual
npm run test:coverage # Executa testes com relatório de cobertura

# Qualidade de Código
npm run lint         # Executa ESLint
npm run lint:fix     # Corrige automaticamente problemas de lint
npm run format       # Formata código com Prettier
npm run format:check # Verifica formatação sem modificar
npm run type-check   # Verifica tipagem TypeScript

# API Types
npm run gen:api-types # Gera tipos TypeScript a partir do schema OpenAPI
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env.local` baseado nos arquivos `.env.development` e `.env.production`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=IABANK
VITE_APP_VERSION=1.0.0
```

### Desenvolvimento

1. Instale as dependências:
   ```bash
   npm install
   ```

2. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

3. Acesse http://localhost:3000

### Integração com Backend

O frontend está configurado para fazer proxy das chamadas `/api/*` para `http://localhost:8000` durante o desenvolvimento.

Para gerar tipos TypeScript a partir do schema OpenAPI do backend:
```bash
npm run gen:api-types
```

## Estrutura de Funcionalidades

### Páginas Implementadas

- **Dashboard** (`/dashboard`) - Página principal com overview
- **Login** (`/login`) - Autenticação de usuários
- **404** (`/*`) - Página não encontrada

### Funcionalidades Planejadas

- **Auth** - Sistema de autenticação
- **Customers** - Gestão de clientes
- **Loans** - Gestão de empréstimos
- **Payments** - Processamento de pagamentos
- **Reports** - Relatórios financeiros

## Padrões de Desenvolvimento

### Importações

Use os aliases configurados no TypeScript:

```typescript
import { config } from '@/shared/config'
import { DashboardPage } from '@/pages/Dashboard'
import { AuthFeature } from '@/features/auth'
import { Customer } from '@/entities/customer'
```

### Componentes

Componentes seguem a convenção de nomenclatura PascalCase e são exportados como named exports:

```typescript
export function CustomerCard() {
  return <div>...</div>
}
```

### Tipos

Tipos são definidos em `@/shared/types/` e seguem a convenção PascalCase:

```typescript
interface Customer extends TenantEntity {
  cpf: string
  full_name: string
  // ...
}
```

## Qualidade de Código

### Cobertura de Testes

Mínimo exigido: **85%** de cobertura em todas as métricas (branches, functions, lines, statements).

### Regras de Linting

- TypeScript strict mode habilitado
- Proibição de `any` explícito
- Preferência por optional chaining e nullish coalescing
- Variáveis não utilizadas são tratadas como erro

### Formatação

- Single quotes para strings
- Sem pontos e vírgulas
- Trailing commas em ES5
- 80 caracteres por linha

## Comandos Úteis

```bash
# Verifica todo o pipeline de qualidade
npm run type-check && npm run lint && npm run format:check && npm test

# Corrige problemas automaticamente
npm run lint:fix && npm run format

# Build completo com verificações
npm run build
```

## Integração com IABANK Backend

Este frontend está projetado para integrar com o backend Django do IABANK. Certifique-se de que o backend esteja rodando em `http://localhost:8000` para funcionalidade completa.

Para mais informações sobre o backend, consulte `../backend/README.md`.