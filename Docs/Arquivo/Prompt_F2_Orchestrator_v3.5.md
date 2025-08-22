# AGV Prompt: OrchestratorHelper v3.5 (Granularidade Máxima)

**Tarefa Principal:** Analisar o `@Blueprint_Arquitetural.md`, que é a fonte única da verdade sobre a arquitetura. Suas responsabilidades são: (1) Derivar uma ordem de implementação lógica e (2) Gerar cenários chave para os Testes de Integração.

**Input Principal (Blueprint Arquitetural):**

## --- Conteúdo do Blueprint Arquitetural ---

# Blueprint Arquitetural: IABANK v1.0

Este documento serve como a fonte única da verdade para a arquitetura técnica e de produto do sistema IABANK. Ele define a estrutura, componentes, contratos de serviço e a experiência do usuário, guiando o desenvolvimento de forma coesa e profissional.

## 1. Visão Geral da Arquitetura

A arquitetura do IABANK será um **Monólito Modular com Fronteiras Claras**, implementado em um **Monorepo**.

- **Abordagem Arquitetural (Backend):** Adotaremos uma variação da **Arquitetura em Camadas (Layered Architecture)**, inspirada na Clean Architecture. Isso promove uma forte separação de responsabilidades, isolando a lógica de negócio do framework e da infraestrutura. As camadas principais serão:

  1.  **Domínio (Domain):** O coração do sistema. Contém os modelos de dados (Django Models), lógica de negócio pura e as `choices` de status. É agnóstico de frameworks.
  2.  **Aplicação (Application):** Orquestra os casos de uso. Contém os `Services` que executam a lógica de negócio, utilizam os modelos do domínio e interagem com a camada de infraestrutura através de abstrações.
  3.  **Apresentação (Presentation):** O ponto de entrada do sistema. Para o IABANK, esta camada é a **API RESTful**, construída com Django REST Framework (DRF). Ela lida com requisições HTTP, serialização de dados (DTOs) e autenticação/autorização.
  4.  **Infraestrutura (Infrastructure):** Contém as implementações concretas de acesso a recursos externos: banco de dados (gerenciado pelo Django ORM), cache (Redis), filas de tarefas (Celery), e integrações futuras.

- **Abordagem Arquitetural (Frontend):** A aplicação React será estruturada seguindo o padrão **Feature-Based (Baseado em Funcionalidades)**. Em vez de agrupar o código por tipo (ex: `components/`, `hooks/`), nós o organizaremos por funcionalidade de negócio (ex: `features/loans/`, `features/customers/`), promovendo alta coesão e baixo acoplamento.

- **Organização do Código-Fonte (Monorepo):** O backend (Django) e o frontend (React) coexistirão no mesmo repositório Git.
  - **Justificativa:** Para a fase inicial do projeto com uma equipe coesa, um monorepo simplifica drasticamente a gestão de dependências, o build e os testes de integração. Garante que uma única versão do código-fonte representa um estado funcional do sistema como um todo, facilitando a coordenação e a implementação de features que abrangem ambas as frentes.

## 2. Diagramas da Arquitetura (Modelo C4)

### 2.1. Nível 1: Diagrama de Contexto do Sistema (C1)

Este diagrama mostra o IABANK no seu ambiente, interagindo com usuários e, no futuro, com sistemas externos.

```mermaid
graph TD
    subgraph "Ecossistema IABANK"
        Gestor[Gestor / Administrador]
        Consultor[Consultor / Cobrador]
        ClienteFinal[Cliente Final (Futuro)]

        style Gestor fill:#28a745,color:#fff
        style Consultor fill:#ffc107,color:#000

        subgraph "Sistema IABANK"
            IABANK_System[Plataforma Web SaaS<br/><strong>IABANK</strong><br/>Gestão de Empréstimos End-to-End]
        end

        Gestor -- "Gerencia a operação via" --> IABANK_System
        Consultor -- "Executa cobranças e gestão em campo via" --> IABANK_System
        ClienteFinal -.-> |Self-service via Portal do Cliente (Futuro)| IABANK_System

        IABANK_System -.->|Consulta de Crédito (Futuro)| BureauCredito[Bureaus de Crédito<br/>(ex: Serasa, SPC)]
        IABANK_System -.->|Transações Financeiras (Futuro)| OpenFinance[Sistemas Bancários<br/>(Open Finance, Pix)]
        IABANK_System -.->|Notificações e Chat (Futuro)| WhatsApp[Plataformas de Comunicação<br/>(ex: WhatsApp)]
    end
```

### 2.2. Nível 2: Diagrama de Containers (C2)

Este diagrama detalha os principais blocos tecnológicos que compõem o sistema IABANK.

```mermaid
graph TD
    Usuario[Usuário (Gestor/Consultor)] -->|HTTPS no Navegador| Frontend[Frontend SPA<br/><strong>React / TypeScript</strong><br/>Painel de Gestão Web]

    subgraph "Infraestrutura na Cloud (Ex: AWS, GCP)"
        Frontend -->|API REST (JSON/HTTPS)| Backend[Backend API<br/><strong>Django / DRF</strong><br/>Lógica de Negócio e Serviços]
        Backend -->|Leitura/Escrita (TCP/IP)| Database[(Banco de Dados<br/><strong>PostgreSQL</strong><br/>Persistência de Dados)]
        Backend -->|Tarefas Assíncronas| TaskQueue[Fila de Tarefas<br/><strong>Celery</strong>]
        TaskQueue -->|Armazenamento de Tarefas| Broker[(Message Broker<br/><strong>Redis</strong>)]
        Backend -->|Cache de Sessão/Dados| Broker
    end

    style Frontend fill:#61DAFB,color:#000
    style Backend fill:#092E20,color:#fff
    style Database fill:#336791,color:#fff
    style TaskQueue fill:#A43735,color:#fff
    style Broker fill:#D82C20,color:#fff
    style Usuario fill:#28a745,color:#fff
```

### 2.3. Nível 3: Diagrama de Componentes (C3) - Backend API

Um zoom no container do Backend para mostrar seus principais componentes internos.

```mermaid
graph TD
    subgraph "Container: Backend API (Django)"
        direction TB
        Presentation[<br><strong>Camada de Apresentação (DRF)</strong><br>Views, Serializers, Routers<br><em>Lida com HTTP e traduz dados</em>]
        Application[<br><strong>Camada de Aplicação</strong><br>Services, DTOs<br><em>Orquestra casos de uso</em>]
        Domain[<br><strong>Camada de Domínio</strong><br>Models, Lógica de Negócio Pura<br><em>O coração do sistema</em>]
        Infrastructure[<br><strong>Camada de Infraestrutura</strong><br>Django ORM, Celery Tasks, Wrappers<br><em>Implementações de acesso externo</em>]
    end

    Presentation -->|Usa| Application
    Application -->|Manipula| Domain
    Application -->|Depende de Interfaces| Infrastructure

    APIGateway[Cliente Externo (Frontend)] --> Presentation
```

## 3. Descrição dos Componentes, Interfaces e Modelos de Domínio

### 3.1. Consistência dos Modelos de Dados (SSOT do Domínio)

Esta seção é a Fonte Única da Verdade para todas as entidades de dados do IABANK, implementadas como Modelos Django. **Nenhuma chave estrangeira aponta para um modelo não definido.**

#### Módulo Core/Tenancy

```python
# iabank/core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Tenant(models.Model):
    """Representa uma instância isolada do sistema (uma empresa/cliente SaaS)."""
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    """Usuário customizado que pertence a um Tenant."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")
    # Campos adicionais como 'phone', 'avatar' podem ser adicionados aqui.

class AuditLog(models.Model):
    """Modelo para Logs de Atividade e Auditoria."""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255) # Ex: "Criou Cliente", "Excluiu Empréstimo"
    target_object_id = models.PositiveIntegerField()
    target_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    details = models.JSONField(default=dict) # Armazena o 'diff' de dados
    timestamp = models.DateTimeField(auto_now_add=True)

# Outros modelos de administração...
class Holiday(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    date = models.DateField(unique=True)
    name = models.CharField(max_length=100)
```

#### Módulo Operacional (Loans, Customers, etc.)

```python
# iabank/operations/models.py
from django.db import models
from django.db.models import TextChoices

class Customer(models.Model):
    """Modelo para Clientes."""
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=18) # CPF/CNPJ
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # Endereço
    zip_code = models.CharField(max_length=9, null=True, blank=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=20, null=True, blank=True)
    complement = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)

    # Info Profissional
    profession = models.CharField(max_length=100, null=True, blank=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'document_number')

class Consultant(models.Model):
    """Modelo para Consultores/Cobradores."""
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    user = models.OneToOneField('core.User', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    # Outras configurações específicas do app...

class Loan(models.Model):
    """Modelo central para Empréstimos."""
    class Status(TextChoices):
        PENDING = 'PENDING', 'Pendente'
        ACTIVE = 'ACTIVE', 'Em Andamento'
        IN_ARREARS = 'IN_ARREARS', 'Em Atraso'
        IN_COLLECTION = 'IN_COLLECTION', 'Em Cobrança'
        PAID_OFF = 'PAID_OFF', 'Finalizado'
        CANCELED = 'CANCELED', 'Cancelado'

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="loans")
    consultant = models.ForeignKey(Consultant, on_delete=models.SET_NULL, null=True, blank=True, related_name="loans")

    principal_amount = models.DecimalField(max_digits=12, decimal_places=2) # Valor Principal
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2) # Taxa de juros mensal %
    iof_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    origination_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    number_of_installments = models.PositiveSmallIntegerField()
    start_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)

class Installment(models.Model):
    """Parcela de um empréstimo."""
    class Status(TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Paga'
        OVERDUE = 'OVERDUE', 'Vencida'

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="installments")
    installment_number = models.PositiveSmallIntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

class CollectionLog(models.Model):
    """Registro de interações de cobrança."""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="collection_logs")
    user = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    interaction_type = models.CharField(max_length=50) # Ex: "Ligação", "WhatsApp", "Visita"
    notes = models.TextField()
    next_action_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class PromissoryNoteHolder(models.Model):
    """Credor Promissória."""
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=18) # CPF/CNPJ
    address = models.CharField(max_length=255)
```

#### Módulo Financeiro (Finance)

```python
# iabank/finance/models.py
from django.db import models
from django.db.models import TextChoices

# Cadastros de Apoio ao Financeiro
class BankAccount(models.Model):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100) # Ex: "Conta Principal Bradesco"
    bank_code = models.CharField(max_length=10, null=True, blank=True)
    agency_number = models.CharField(max_length=10, null=True, blank=True)
    account_number = models.CharField(max_length=20)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

class PaymentCategory(models.Model):
    class Type(TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=Type.choices)

class CostCenter(models.Model):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

class Supplier(models.Model):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    document_number = models.CharField(max_length=18, null=True, blank=True)

class FinancialTransaction(models.Model):
    """Modelo unificado para Contas a Pagar e a Receber."""
    class Type(TextChoices):
        INCOME = 'INCOME', 'Receita'
        EXPENSE = 'EXPENSE', 'Despesa'
        TRANSFER = 'TRANSFER', 'Transferência'

    class Status(TextChoices):
        PENDING = 'PENDING', 'Pendente'
        PAID = 'PAID', 'Pago'
        CANCELED = 'CANCELED', 'Cancelado'

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=Type.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)

    category = models.ForeignKey(PaymentCategory, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)

    # Relações polimórficas (pode estar ligado a uma Parcela, um Fornecedor, etc.)
    related_object_id = models.PositiveIntegerField(null=True)
    related_content_type = models.ForeignKey(
        'contenttypes.ContentType', on_delete=models.SET_NULL, null=True
    )

    # Para transferências
    transfer_to_account = models.ForeignKey(
        BankAccount,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name="transfers_in"
    )

class PeriodClosing(models.Model):
    """Registro de um Fechamento de Período."""
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_income = models.DecimalField(max_digits=12, decimal_places=2)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2)
    net_result = models.DecimalField(max_digits=12, decimal_places=2)
    closed_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True)
    closed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField() # Snapshot dos dados no momento do fechamento
```

### 3.1.1. Detalhamento dos DTOs e Casos de Uso (Pydantic)

Esses DTOs definem os contratos de dados para a API, garantindo validação e clareza.

```python
# iabank/operations/dtos.py
import pydantic
from datetime import date

class CustomerCreateDTO(pydantic.BaseModel):
    full_name: str
    document_number: str
    birth_date: date | None = None
    email: pydantic.EmailStr | None = None
    phone_number: str | None = None
    zip_code: str | None = None
    # ... outros campos de endereço e profissionais

class CustomerUpdateDTO(pydantic.BaseModel):
    full_name: str | None = None
    email: pydantic.EmailStr | None = None
    phone_number: str | None = None
    # ... etc. campos que podem ser atualizados

class LoanCreateDTO(pydantic.BaseModel):
    customer_id: int
    consultant_id: int | None = None
    principal_amount: pydantic.condecimal(gt=0, decimal_places=2)
    interest_rate: pydantic.condecimal(gt=0, decimal_places=2)
    number_of_installments: pydantic.conint(gt=0)
    start_date: date
```

### 3.2. Contratos de Dados da View (ViewModel - TypeScript)

Estes são os contratos que o Frontend espera receber da API para popular suas telas de listagem.

#### **ViewModel para Tela `Operacional > Empréstimos`**

```typescript
// frontend/src/features/loans/types/index.ts

export type LoanStatus =
  | "ACTIVE"
  | "IN_ARREARS"
  | "IN_COLLECTION"
  | "PAID_OFF"
  | "CANCELED";

export interface LoanListItemViewModel {
  id: number;
  customerName: string;
  customerDocument: string;
  principalAmountFormatted: string; // "R$ 5.000,00"
  installmentsProgress: string; // "3/12"
  nextDueDate: string; // "25/08/2024"
  status: LoanStatus;
  statusLabel: string; // "Em Andamento"
  consultantName?: string;
}
```

**Mapeamento de Origem:** Este ViewModel é montado no backend pelo `LoanListSerializer` do DRF. Ele combina dados do modelo `Loan` (id, status), `Customer` relacionado (`full_name`, `document_number`), e calcula campos derivados como `principalAmountFormatted` e `installmentsProgress` (contando as parcelas pagas vs. totais).

#### **ViewModel para Tela `Operacional > Clientes`**

```typescript
// frontend/src/features/customers/types/index.ts

export interface CustomerListItemViewModel {
  id: number;
  fullName: string;
  documentNumber: string;
  cityState: string; // "São Paulo - SP"
  phoneNumberFormatted: string; // "(11) 99999-9999"
  activeLoansCount: number;
  createdAtFormatted: string; // "15/07/2024"
}
```

**Mapeamento de Origem:** Derivado do modelo `Customer`. O `CustomerListSerializer` formata `cityState` e `phoneNumber`, e realiza uma anotação na query para contar os empréstimos ativos (`activeLoansCount`).

## 4. Descrição Detalhada da Arquitetura Frontend

A arquitetura do frontend foi projetada para ser escalável, manutenível e fácil de dar manutenção.

- **Padrão Arquitetural:** **Feature-Sliced Design (FSD)**. É uma abordagem que organiza o código por escopo de negócio, dividindo a aplicação em camadas e fatias (features). Isso garante baixo acoplamento e alta coesão.

- **Estrutura de Diretórios Proposta (`frontend/src`):**

  ```
  src/
  ├── app/                # Lógica central da aplicação (providers, router, store)
  ├── pages/              # Componentes de página, montam as telas usando features e widgets
  ├── widgets/            # Blocos compostos de UI (ex: Header, Sidebar, LoanListTable)
  ├── features/           # Funcionalidades de negócio (ex: criar-empréstimo, filtrar-clientes)
  ├── entities/           # Entidades de negócio (ex: componentes de card de Cliente, modelo de dados de Empréstimo)
  └── shared/             # Código reutilizável e agnóstico de negócio
      ├── ui/             # Componentes de UI puros (Button, Input, Table, Badge)
      ├── api/            # Configuração do cliente Axios/fetch e definições de endpoints
      ├── lib/            # Funções utilitárias, hooks genéricos (useDebounce)
      └── assets/         # Imagens, fontes, etc.
  ```

- **Estratégia de Gerenciamento de Estado:**

  - **Estado do Servidor (Server State):** **TanStack Query (React Query)** será a fonte única da verdade para todos os dados que vêm da API. Ele gerenciará o fetching, caching, sincronização e atualização de dados de forma automática, eliminando a necessidade de gerenciar estados de `loading`, `error` e `data` manualmente.
  - **Estado Global do Cliente (Global Client State):** **Zustand**. Utilizado para estados globais síncronos e de baixo volume, como informações do usuário autenticado, estado do menu lateral (aberto/fechado), tema da UI. Sua API minimalista e baseada em hooks é ideal para isso.
  - **Estado Local do Componente (Local Component State):** O estado nativo do React (`useState`, `useReducer`) será usado para dados efêmeros e que não precisam ser compartilhados, como o estado de um formulário ou a visibilidade de um modal.

- **Fluxo de Dados Típico (Ex: Listagem de Empréstimos):**
  1.  O usuário navega para a página `/operacional/emprestimos`.
  2.  O componente da página `LoansPage` é renderizado.
  3.  Dentro dele, o widget `LoanListTable` usa o hook `useLoans` (que encapsula o `useQuery` do TanStack Query).
  4.  TanStack Query faz a chamada à API para `GET /api/v1/loans/`.
  5.  A API retorna o JSON com os dados (no formato `LoanListItemViewModel`).
  6.  TanStack Query armazena os dados em cache e os disponibiliza para o componente.
  7.  O `LoanListTable` renderiza a tabela com os dados. O estado de `isLoading` é usado para exibir um spinner durante o carregamento.

## 5. Definição das Interfaces Principais

Definimos interfaces (usando `typing.Protocol` em Python) para desacoplar a camada de aplicação da infraestrutura.

```python
# iabank/operations/services.py
from typing import Protocol
from .dtos import LoanCreateDTO
from .models import Loan

class LoanCreatorInterface(Protocol):
    def create_loan(self, data: LoanCreateDTO) -> Loan:
        """
        Cria um novo empréstimo, suas parcelas e as transações financeiras associadas.
        Garante a atomicidade da operação.
        """
        ...

# Exemplo de implementação em um serviço
class LoanService:
    # A configuração (dependências) é injetada no construtor
    def __init__(self, some_dependency: SomeInterface):
        self.dependency = some_dependency

    def create_loan(self, data: LoanCreateDTO) -> Loan:
        # 1. Validação de regras de negócio complexas
        # 2. Inicia uma transação de banco de dados
        # 3. Cria o objeto Loan
        # 4. Gera as Installments
        # 5. Gera as FinancialTransactions correspondentes (saída do valor, taxas)
        # 6. Comita a transação
        # 7. Dispara uma tarefa assíncrona (ex: gerar contrato)
        ...
```

## 6. Gerenciamento de Dados

- **Persistência e Acesso:** O **Django ORM** será a ferramenta exclusiva para toda a interação com o banco de dados PostgreSQL. O padrão Repository não será implementado explicitamente, pois os Managers e QuerySets do Django já fornecem uma abstração eficaz.
- **Gerenciamento de Schema:** As migrações de banco de dados serão gerenciadas pelo sistema nativo do Django (`makemigrations`, `migrate`), garantindo a evolução consistente e versionada do schema.
- **Seed de Dados:** Para o ambiente de desenvolvimento, utilizaremos a biblioteca **`factory-boy`** em conjunto com um comando de gestão customizado do Django (`management command`). Isso permitirá popular o banco de dados com dados fictícios, realistas e consistentes para testes manuais e desenvolvimento.

## 7. Estrutura de Diretórios Proposta

A estrutura do monorepo será organizada para máxima clareza e separação.

```
iabank-monorepo/
├── .github/                # Configurações de CI/CD (GitHub Actions)
│   └── workflows/
│       └── main.yml
├── backend/
│   ├── src/
│   │   └── iabank/
│   │       ├── __init__.py
│   │       ├── asgi.py
│   │       ├── wsgi.py
│   │       ├── settings.py
│   │       ├── urls.py
│   │       ├── core/           # Módulo para Tenant, User, AuditLog
│   │       ├── operations/     # Módulo para Loans, Customers, etc.
│   │       ├── finance/        # Módulo para Contas a Pagar/Receber, etc.
│   │       └── ...             # Outros módulos de negócio
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/                  # Estrutura detalhada na Seção 4
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── .docker-compose.yml       # Orquestra os serviços em desenvolvimento
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore
├── .pre-commit-config.yaml   # Configuração para hooks de pre-commit
├── LICENSE
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## 8. Arquivo `.gitignore` Proposto

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# PEP 582; __pypackages__
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak
venv.bak

# IDEs
.idea/
.vscode/
*.swp
*.swo

# Docker
.dockerignore
docker-compose.override.yml

# Node.js / Frontend
node_modules/
dist/
.npm/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-store/
.yarn/

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
```

## 9. Arquivo `README.md` Proposto

````markdown
# IABANK - Sistema de Gestão de Empréstimos

[![Status](https://img.shields.io/badge/status-em_desenvolvimento-yellow)](https://github.com/your-org/iabank-monorepo)
[![CI/CD](https://img.shields.io/github/actions/workflow/status/your-org/iabank-monorepo/main.yml?branch=main)](https://github.com/your-org/iabank-monorepo/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

## Sobre o Projeto

**IABANK** é uma plataforma Web SaaS robusta e segura, desenvolvida em Python, projetada para a gestão completa de empréstimos (end-to-end). Foi concebida para ser escalável, intuitiva e adaptável às necessidades de financeiras, fintechs, bancos e qualquer organização cujo modelo de negócio dependa do ciclo de emprestar, cobrar e reinvestir.

## Stack Tecnológica

- **Backend:** Python, Django, Django REST Framework, Celery, PostgreSQL, Redis
- **Frontend:** TypeScript, React, Vite, TanStack Query, Tailwind CSS, Zod
- **Infraestrutura:** Docker, Nginx

## Como Começar

Siga estas instruções para obter uma cópia do projeto em execução na sua máquina local para fins de desenvolvimento e teste.

### Pré-requisitos

- Docker e Docker Compose
- Node.js e npm/yarn (para hooks de pre-commit)

### Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/your-org/iabank-monorepo.git
    cd iabank-monorepo
    ```
2.  Crie o arquivo de ambiente a partir do exemplo:
    ```bash
    cp .env.example .env
    ```
3.  Suba os contêineres Docker:
    ```bash
    docker-compose up --build
    ```
4.  O backend estará disponível em `http://localhost:8000` e o frontend em `http://localhost:3000`.

5.  Para criar as tabelas do banco e um superusuário (em outro terminal):
    ```bash
    docker-compose exec backend python src/manage.py migrate
    docker-compose exec backend python src/manage.py createsuperuser
    ```

## Como Executar os Testes

Para executar a suíte de testes do backend:

```bash
docker-compose exec backend pytest
```
````

## Estrutura do Projeto

O projeto é um monorepo contendo:

- `backend/`: O código da API Django.
- `frontend/`: O código da SPA React.
- `docker-compose.yml`: Arquivo para orquestrar os serviços em ambiente de desenvolvimento.

Consulte o `Blueprint Arquitetural` para um detalhamento completo da estrutura interna de cada aplicação.

```

## 10. Arquivo `LICENSE` Proposto
A licença **MIT** é uma excelente escolha padrão, pois é permissiva e amplamente compatível.

```

MIT License

Copyright (c) 2024 Your Name or Your Company Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT of OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

````

## 11. Arquivo `CONTRIBUTING.md` Proposto
```markdown
# Como Contribuir para o IABANK

Agradecemos o seu interesse em contribuir para o IABANK! Para garantir a qualidade e a consistência do projeto, pedimos que siga estas diretrizes.

## Processo de Desenvolvimento

1.  **Siga o Blueprint:** Todas as contribuições devem estar alinhadas com o `Blueprint Arquitetural` do projeto. Grandes mudanças na arquitetura devem ser discutidas e aprovadas antes da implementação.
2.  **Crie uma Branch:** Não faça commit diretamente na `main`. Crie uma branch a partir da `main` com um nome descritivo (ex: `feature/loan-creation-wizard`).
3.  **Desenvolva e Teste:** Escreva seu código e adicione testes unitários e de integração que cubram as novas funcionalidades e corrijam os bugs.
4.  **Garanta a Qualidade do Código:** Antes de fazer o commit, rode as ferramentas de qualidade.
5.  **Abra um Pull Request:** Envie um Pull Request para a branch `main`. Descreva claramente as mudanças e o motivo delas.

## Qualidade de Código

Utilizamos ferramentas para manter um padrão de código limpo e consistente. A maioria delas é executada automaticamente antes de cada commit através de hooks de pre-commit.

### Pré-requisitos

Instale o `pre-commit`:
```bash
pip install pre-commit
pre-commit install
````

### Ferramentas Utilizadas

- **Backend (Python):**
  - `Ruff`: Linter e formatador extremamente rápido.
  - `Black`: Formatador de código opinativo.
- **Frontend (TypeScript/React):**
  - `ESLint`: Análise de código para encontrar problemas.
  - `Prettier`: Formatador de código.

A configuração está no arquivo `.pre-commit-config.yaml`.

## Documentação de Código

- **Docstrings:** Todas as funções públicas, classes e métodos devem ter docstrings no estilo Google.

  ```python
  def minha_funcao(param1: int, param2: str) -> bool:
      """Descrição concisa da função.

      Args:
          param1: Descrição do primeiro parâmetro.
          param2: Descrição do segundo parâmetro.

      Returns:
          True se for bem-sucedido, False caso contrário.
      """
      ...
  ```

````

## 12. Estrutura do `CHANGELOG.md`
```markdown
# Changelog

Todos as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-   ...

### Changed
-   ...

### Removed
-   ...

## [0.1.0] - 2024-08-15

### Added
-   Estrutura inicial do projeto e configuração do Blueprint Arquitetural.
-   Módulos de autenticação, tenancy e CRUD básico de clientes.
````

## 13. Estratégia de Configuração e Ambientes

Utilizaremos a biblioteca **`django-environ`**.

- **Desenvolvimento:** As configurações serão lidas de um arquivo `.env` na raiz do projeto (`backend/`). Este arquivo **não** será versionado no Git.
- **Homologação/Produção:** As configurações serão injetadas como **variáveis de ambiente** no ambiente de execução (ex: nos contêineres Docker, segredos do Kubernetes, configurações do serviço de PaaS).
- Isso garante que segredos (chaves de API, senhas de banco) nunca sejam codificados diretamente no código-fonte. O arquivo `settings.py` será configurado para ler essas variáveis, com valores padrão seguros para desenvolvimento.

## 14. Estratégia de Observabilidade Completa

- **Logging Estruturado:** Utilizaremos `structlog` com Django. Todos os logs serão emitidos em formato **JSON**. Em desenvolvimento, os logs podem ser formatados para serem legíveis no console. Em produção, o formato JSON permite a ingestão direta por serviços como Sentry, Datadog ou a stack ELK (Elasticsearch, Logstash, Kibana) para busca e análise.
- **Métricas de Negócio:** Usaremos `django-prometheus` para expor um endpoint `/metrics`. Coletaremos métricas chave como:
  - `loans_created_total`: Número total de empréstimos criados.
  - `payments_received_total`: Volume financeiro de pagamentos recebidos.
  - `active_users_gauge`: Número de usuários ativos.
  - `api_request_latency_seconds`: Histograma da latência das requisições da API.
    Estas métricas serão coletadas por um servidor Prometheus e visualizadas em dashboards no Grafana.
- **Distributed Tracing:** Embora seja um monólito, a base para tracing será estabelecida com a biblioteca **OpenTelemetry**. Ela instrumentará requisições Django e chamadas ao banco, permitindo visualizar o tempo gasto em cada parte do sistema. Isso é crucial para a futura transição para microsserviços ou integração com agentes de IA.
- **Health Checks e SLIs/SLOs:** Será criado um endpoint `/health/` que verifica a conectividade com o banco de dados e o Redis.
  - **SLI (Indicador):** Latência da API do endpoint `/api/v1/loans/`. Disponibilidade do endpoint `/health/`.
  - **SLO (Objetivo):** 99.5% das requisições ao `/api/v1/loans/` devem responder em menos de 500ms. O sistema deve ter 99.9% de uptime.
- **Alerting Inteligente:** Alertas serão configurados no Alertmanager (do Prometheus) ou Datadog, focando em:
  - **Taxa de erro:** Aumento súbito na taxa de erros 5xx na API.
  - **Saturação:** Uso de CPU ou memória consistentemente acima de 85%.
  - **Anomalias de Negócio:** Queda abrupta no número de empréstimos criados por hora (comparado com a mesma hora em dias anteriores).

## 15. Estratégia de Testes Detalhada

- **Tipos de Testes:**

  - **Testes Unitários:** Focam em uma única unidade de código (uma função, um método) de forma isolada. Serão usados para testar a lógica de negócio nos `Services` e funções utilitárias. `pytest` com `unittest.mock` será a ferramenta principal.
  - **Testes de Integração:** Testam a interação entre múltiplos componentes. No nosso caso, testarão principalmente os endpoints da API, verificando todo o fluxo desde a requisição HTTP até a resposta, incluindo a interação com o banco de dados. Utilizaremos o `APIClient` do DRF.
  - **Testes End-to-End (E2E):** (Fase posterior) Testam o fluxo completo do usuário através da UI. Ferramentas como Cypress ou Playwright podem ser usadas.

- **Estrutura e Convenção de Nomenclatura:**

  - Os testes residirão em uma pasta `tests/` dentro de cada app Django (ex: `iabank/operations/tests/`).
  - Os arquivos seguirão a convenção `test_<nome_do_modulo>.py`, por exemplo: `test_models.py`, `test_services.py`, `test_api.py`.
  - Funções de teste começarão com `test_`.

- **Padrões de Teste de Integração:**

  - **Uso de Factories:** A biblioteca `factory-boy` será utilizada para criar objetos de modelo (`Customer`, `Loan`, etc.) de forma programática e reutilizável. Isso evita a repetição de código e torna os testes mais legíveis.

    ```python
    # iabank/operations/tests/factories.py
    import factory
    from iabank.operations.models import Customer

    class CustomerFactory(factory.django.DjangoModelFactory):
        class Meta:
            model = Customer

        full_name = factory.Faker('name')
        document_number = factory.Faker('cpf')
    ```

  - **Simulação de Autenticação:** Para testar endpoints protegidos, utilizaremos o método `force_authenticate` do `APIClient` do DRF. Isso autentica a requisição diretamente, sem a necessidade de simular o fluxo de login em cada teste.
  - **Escopo de Teste:** Cada teste de API focará em validar um único endpoint ou fluxo. A criação de dados pré-requisito (como o Tenant e o Usuário) será feita no `setUp` do teste usando as factories, garantindo isolamento e rapidez. O multi-tenancy será validado garantindo que um usuário de um tenant não consiga acessar dados de outro.

## 16. Estratégia de CI/CD (Integração e Implantação Contínuas)

- **Ferramenta:** **GitHub Actions**. O workflow será definido em `.github/workflows/main.yml`.
- **Gatilhos:** O pipeline será acionado em cada `push` para a branch `main` e em cada abertura/atualização de `Pull Request`.
- **Estágios do Pipeline:**
  1.  **CI - Validação (em Pull Requests):**
      - **Setup:** Checkout do código e setup do ambiente Python/Node.
      - **Lint & Format:** Roda `ruff`, `black`, `eslint` e `prettier` para garantir a qualidade do código.
      - **Testes:** Executa a suíte completa de testes unitários e de integração do backend.
      - **Build:** Constrói as imagens Docker do backend e frontend para garantir que não há erros de build.
  2.  **CD - Implantação (em merge para `main`):**
      - Todos os passos do CI são executados novamente.
      - **Build & Push:** Constrói as imagens Docker de produção, tagueia com o hash do commit e envia para um registro de contêineres (ex: Docker Hub, AWS ECR, GCP Artifact Registry).
      - **Deploy (Staging):** Aciona um webhook ou usa uma action para implantar as novas imagens no ambiente de homologação (staging).
      - **Deploy (Produção) - Manual Trigger:** Após a validação em staging, um gatilho manual no GitHub Actions inicia a implantação em produção, seguindo uma estratégia de **Blue/Green** ou **Rolling Update** para garantir zero downtime.
  - **Rollback:** O rollback será feito reimplantando a tag da imagem Docker da versão estável anterior.

## 17. Estratégia de Versionamento da API

A API será versionada via URL. Todas as rotas serão prefixadas com a versão, ex: `/api/v1/`.

- **Exemplo:** `https://api.iabank.com/api/v1/loans/`, `https://api.iabank.com/api/v1/customers/`.
- **Justificativa:** Esta é a abordagem mais clara e explícita, facilitando o roteamento e o cache. Quando uma mudança que quebra a compatibilidade for necessária (ex: remover um campo de um endpoint), uma nova versão (`v2`) será criada, permitindo que o frontend atual e outros clientes continuem usando a `v1` enquanto migram.

## 18. Padrão de Resposta da API e Tratamento de Erros

- **Resposta de Sucesso (2xx):**
  - Para listagens, a resposta será encapsulada com dados de paginação:
    ```json
    {
      "count": 120,
      "next": "http://api.example.org/accounts/?page=3",
      "previous": "http://api.example.org/accounts/?page=1",
      "results": [{ "id": 1, "customerName": "..." }]
    }
    ```
  - Para criação/detalhe de um único objeto:
    ```json
    {
      "id": 1,
      "customerName": "...",
      "principalAmountFormatted": "R$ 5.000,00"
    }
    ```
- **Resposta de Erro (4xx, 5xx):**
  - Utilizaremos um `custom_exception_handler` no DRF para padronizar todas as respostas de erro em um formato consistente.
  - **Erro de Validação (400):**
    ```json
    {
      "errors": {
        "principal_amount": ["Este campo não pode ser nulo."],
        "start_date": ["A data deve ser no futuro."]
      }
    }
    ```
  - **Não Encontrado (404) ou Permissão Negada (403):**
    ```json
    {
      "errors": {
        "detail": "O recurso solicitado não foi encontrado."
      }
    }
    ```

## 19. Estratégia de Segurança Abrangente

- **Threat Modeling Básico:**
  - **Ameaça:** Acesso não autorizado aos dados de um tenant por um usuário de outro tenant.
    - **Mitigação:** Implementar uma camada de `middleware` ou um `Manager` customizado no Django que **filtre automaticamente todas as queries pelo `tenant_id` do usuário autenticado**. Testes de integração rigorosos validarão este isolamento.
  - **Ameaça:** Injeção de SQL (SQL Injection).
    - **Mitigação:** Uso exclusivo do Django ORM, que parametriza todas as queries, eliminando esta classe de vulnerabilidade.
  - **Ameaça:** Vazamento de dados sensíveis do cliente (documentos, renda).
    - **Mitigação:** Controle de acesso granular (RBAC) no backend, garantindo que apenas usuários com a permissão correta possam acessar dados sensíveis. Criptografia em trânsito (HTTPS obrigatório) e em repouso (para uploads de documentos em storage S3/GCS).
- **Secrets Management:**
  - **Desenvolvimento:** Variáveis de ambiente via `.env` (não versionado).
  - **Produção:** Uso de um serviço de gerenciamento de segredos como **AWS Secrets Manager** ou **HashiCorp Vault**. A aplicação receberá as credenciais no momento do boot, injetadas pelo orquestrador de contêineres.
- **Compliance Framework (LGPD):**
  - A arquitetura já suporta os princípios da LGPD através do `tenant_id` e `customer_id` em todos os dados.
  - A trilha de auditoria (`AuditLog`) é essencial para compliance.
  - Futuramente, funcionalidades para anonimização de dados e gestão de consentimento podem ser construídas sobre esta base.
- **Security by Design:**
  - **Validação:** Validação de todos os dados de entrada na camada de API (Serializers do DRF e DTOs Pydantic) e na camada de domínio para regras de negócio.
  - **Menor Privilégio:** Usuários terão o conjunto mínimo de permissões necessárias para suas funções, configurado no módulo de "Usuários e Permissões".
  - **Dependências:** Uso de ferramentas como `Dependabot` (GitHub) ou `Snyk` para monitorar e alertar sobre vulnerabilidades nas dependências do projeto.

## 20. Justificativas e Trade-offs

- **Monólito Modular vs. Microsserviços:** Para a fase inicial do IABANK, um monólito é a escolha correta. Ele reduz a complexidade operacional (deploy, monitoramento, comunicação entre serviços) e acelera o desenvolvimento. A arquitetura modular em camadas garante que, se necessário no futuro, módulos como `finance` ou `operations` possam ser extraídos para microsserviços com refatoração mínima, pois suas fronteiras já estão bem definidas.
- **Monorepo vs. Multi-repo:** A escolha do monorepo simplifica a gestão do projeto nesta fase. O trade-off é um pipeline de CI/CD potencialmente mais lento, pois mudanças em qualquer parte do repo podem acioná-lo. Isso pode ser otimizado no futuro para rodar apenas os testes e builds relevantes para o código que mudou.

## 21. Exemplo de Bootstrapping/Inicialização (Conceitual)

Em Django, a inicialização é gerenciada pelo framework. O exemplo abaixo mostra como os serviços seriam usados dentro de uma `APIView` do DRF, demonstrando a injeção de dependências conceitual.

```python
# iabank/operations/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .services import LoanService # Nossa camada de aplicação
from .dtos import LoanCreateDTO

class LoanCreateAPIView(APIView):
    # A injeção de dependência pode ser feita no __init__ da View,
    # ou usando um container de DI como `django-injector`.
    # Para simplicidade, instanciamos aqui.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loan_service = LoanService() # Em um sistema real, as dependências do serviço seriam injetadas aqui.

    def post(self, request, *args, **kwargs):
        # 1. Validação de dados de entrada usando o DTO
        try:
            loan_data = LoanCreateDTO.model_validate(request.data)
        except pydantic.ValidationError as e:
            return Response(e.errors(), status=400)

        # 2. Chama o serviço da camada de aplicação para executar o caso de uso
        # O serviço é responsável por toda a lógica de negócio complexa.
        new_loan = self.loan_service.create_loan(data=loan_data)

        # 3. Retorna uma resposta (usando um Serializer para formatar a saída)
        serializer = LoanDetailSerializer(new_loan)
        return Response(serializer.data, status=201)
```

## 22. Estratégia de Evolução do Blueprint

- **Versionamento Semântico:** Este Blueprint será versionado (ex: `v1.0.0`). Mudanças que adicionam funcionalidades sem quebrar a arquitetura existente incrementam a versão `MINOR` (ex: `v1.1.0`). Mudanças que quebram a arquitetura (ex: mudar de Monólito para Microsserviços) incrementam a versão `MAJOR` (ex: `v2.0.0`).
- **Processo de Evolução:** Mudanças significativas devem ser propostas através de **ADRs (Architecture Decision Records)**. Um ADR é um documento curto em Markdown, versionado no repositório, que descreve o contexto, a decisão tomada e as consequências. Isso cria um registro histórico das decisões arquiteturais.
- **Compatibilidade:** Ao introduzir mudanças breaking, a política será manter a versão anterior da arquitetura/API funcionando por um período de depreciação definido, garantindo uma migração suave.

## 23. Métricas de Qualidade e Quality Gates

- **Métricas de Cobertura de Código:**
  - **Meta Global:** 85% de cobertura de testes.
  - **Módulos Críticos (ex: `finance`):** Meta de 95% de cobertura.
  - A medição será feita com `pytest-cov`.
- **Métricas de Complexidade:**
  - **Complexidade Ciclomática:** Máximo de **10** por função/método.
  - Medido com ferramentas como `radon` ou plugins de IDE.
- **Quality Gates Automatizados (no CI):**
  - Um Pull Request **só poderá ser mesclado** se todos os seguintes gates passarem:
    1.  Todos os testes unitários e de integração passam.
    2.  A cobertura de código não diminui em mais de 1% e se mantém acima do limite de 85%.
    3.  Nenhuma vulnerabilidade de segurança de severidade `HIGH` ou `CRITICAL` é detectada pelo Snyk/Dependabot.
    4.  O linter (`ruff`, `eslint`) não reporta erros.

## 24. Análise de Riscos e Plano de Mitigação

| Categoria       | Risco Identificado                                                            | Probabilidade (1-5) | Impacto (1-5) | Score (P×I) | Estratégia de Mitigação                                                                                                                                                                                                                                                                                                                          |
| --------------- | ----------------------------------------------------------------------------- | :-----------------: | :-----------: | :---------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Segurança**   | **Violação do isolamento de dados entre Tenants (Data Leak)**                 |          3          |       5       |   **15**    | Implementar um middleware obrigatório de Tenant Scoping no Django que filtra TODAS as queries. Criar testes de integração específicos para tentar acessar dados de outro tenant e garantir que eles falhem com erro 404/403. Realizar revisões de código focadas em segurança em todos os novos endpoints.                                       |
| **Técnico**     | Dificuldade de escalar o banco de dados sob alta carga de transações          |          2          |       4       |      8      | Desde o início, otimizar queries complexas e relatórios usando `select_related`, `prefetch_related` e índices de banco de dados. Utilizar Celery para processar tarefas pesadas de forma assíncrona. Projetar o schema para permitir sharding futuro por `tenant_id` se necessário.                                                              |
| **Negócio**     | A plataforma não atende às necessidades regulatórias financeiras (Compliance) |          3          |       4       |   **12**    | Manter uma trilha de auditoria (`AuditLog`) completa para todas as operações críticas. Construir a plataforma com os princípios da LGPD em mente. Engajar consultoria especializada em compliance financeiro para validar a arquitetura e os fluxos antes do lançamento em larga escala.                                                         |
| **Performance** | Lentidão na UI ao carregar grandes volumes de dados (listagens, relatórios)   |          4          |       3       |   **12**    | Implementar paginação server-side em todas as APIs de listagem. Utilizar TanStack Query no frontend para cacheamento inteligente. Para relatórios, pré-calcular dados agregados em tarefas noturnas (via Celery) e materializar os resultados em tabelas de sumarização. Usar `debounce` nos campos de busca para evitar requisições excessivas. |

---

**Diretrizes Essenciais:**

1. **Análise de Dependências com Decomposição Máxima:** A ordem de implementação deve ser determinada pelo princípio de **responsabilidade única por alvo**. Siga estas regras de decomposição:

   a. **Ordem de Módulos Transversais:** Os módulos que fornecem funcionalidades transversais **DEVEM** ser implementados primeiro. A ordem de implementação e validação entre eles deve seguir a lógica de dependência: **Autenticação > Gestão de Usuários e Autorização > Multi-Tenancy**.

   b. **Decomposição Obrigatória por Tipo (Backend):** Para cada módulo de negócio (ex: `iabank.users`, `iabank.loans`), você **DEVE** criar alvos de implementação separados e sequenciais para cada camada lógica, na seguinte ordem:

   1. **Modelos:** Apenas os arquivos `models.py`.
   2. **Repositórios/Infraestrutura:** Apenas a lógica de acesso a dados.
   3. **Serviços de Aplicação:** Apenas a lógica de negócio dos casos de uso.
   4. **Serializers:** Apenas os arquivos `serializers.py` da API.
   5. **Views/URLs:** Apenas os endpoints `views.py` e o roteamento `urls.py`.

   c. **Regra Especial para `users`:** O módulo de usuários **DEVE** ser decomposto em duas fases funcionais distintas, cada uma com sua própria parada de testes:

   1. **Fase 1: Autenticação JWT.** Implemente apenas os modelos, serializers e views necessários para os endpoints de obtenção e refresh de token (ex: `/token/`).
   2. **Fase 2: Gestão de Usuários e Autorização.** Após validar a autenticação, implemente os endpoints de CRUD de usuários (ex: `/users/`, `/users/me/`) e a lógica de permissões/perfis (RBAC).

2. **Criação do "Alvo 0":** Sua primeira tarefa é SEMPRE gerar um item inicial na ordem de implementação chamado **"Alvo 0: Setup do Projeto Profissional"**. Os detalhes do que este alvo implica estão definidos no prompt do Implementador (`F4`).

3. **Geração da Ordem Sequencial e Pontos de Teste:** Crie uma lista numerada de "Alvos de Implementação".

   - **Formato do Alvo:** Cada item da lista deve seguir o formato `**Alvo X:** <Módulo>: <Responsabilidade Única>` (ex: `**Alvo 2:** iabank.users: Modelos e Migrações`).
   - **Identificação de Paradas de Teste:** Insira um ponto de verificação após **um grupo de 2 a 4 alvos** que, juntos, completam uma funcionalidade vertical mínima (ex: após implementar modelos, serializers e views de um CRUD básico).
   - **Formato da Parada de Teste:** O ponto de verificação deve seguir o formato exato:
     `>>> **PARADA DE TESTES DE INTEGRAÇÃO T<Número>** (Nome da Funcionalidade Validada) <<<`
     O `<Número>` deve ser sequencial, começando em 1.

4. **Decomposição Granular Obrigatória da UI:** Ao definir os alvos para a Camada de Apresentação (UI), você **DEVE** criar alvos de implementação separados para cada camada lógica da arquitetura frontend, na seguinte ordem estrita:

   a. **Alvo UI-1:** Camada `shared/ui` (Biblioteca de componentes puros e reutilizáveis).
   b. **Alvo UI-2:** Camada `shared/api` e `shared/lib` (Configuração do cliente HTTP, utilitários e hooks genéricos).
   c. **Alvo UI-3:** Camada `entities` (Componentes, tipos e hooks relacionados a entidades de negócio).
   d. **Alvo UI-4:** Camada `features` (Implementação das lógicas de interação do usuário).
   e. **Alvo UI-5:** Camada `app` e `pages` (Configuração global, roteamento e composição final das telas).

   **Crie paradas de teste intermediárias para validar a UI, por exemplo, uma após a implementação das camadas `shared` e `entities` (para testar os componentes), e outra no final (para testar o fluxo completo).**

5. **Geração de Cenários de Teste de Integração:**

   - Para cada `>>> PARADA ... <<<` criada, você **DEVE** gerar uma seção detalhada logo abaixo dela.
   - Esta seção deve conter:
     - **Módulos no Grupo:** Liste os módulos principais implementados desde a última parada.
     - **Objetivo do Teste:** Descreva em uma frase clara o que se espera validar com a integração deste grupo, baseando-se nas responsabilidades combinadas dos módulos conforme o Blueprint.
     - **Cenários Chave:** Liste de 2 a 4 cenários de teste específicos e acionáveis que verifiquem as interações mais críticas. Para paradas que dependem de etapas anteriores (ex: testar uma funcionalidade que requer autenticação), os cenários devem mencionar o uso de simulação de pré-condições (ex: "Usando um usuário autenticado simulado...") em vez de repetir o fluxo completo.

6. **Simplicidade do Output:** O resultado final deve ser um documento Markdown contendo apenas a lista numerada da "Ordem de Implementação" com os "Alvos" e as "Paradas de Teste" detalhadas. **Não inclua justificativas ou descrições adicionais; foque apenas no plano de ação.**

**Resultado Esperado:**

Um documento Markdown (`Output_Ordem_e_Testes.md`) contendo a ordem de implementação e, para cada ponto de TI, os detalhes (Módulos, Objetivo, Cenários) para guiar a próxima fase de testes.
