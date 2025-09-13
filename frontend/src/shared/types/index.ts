export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
}

export interface TenantEntity extends BaseEntity {
  tenant_id: string
}

export interface User extends TenantEntity {
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  role: 'ADMIN' | 'CONSULTANT' | 'OPERATOR'
}

export interface Customer extends TenantEntity {
  cpf: string
  full_name: string
  birth_date: string
  phone: string
  email: string
  monthly_income: number
  credit_score: number
  status: 'ACTIVE' | 'INACTIVE' | 'BLOCKED'
}

export interface Loan extends TenantEntity {
  customer_id: string
  consultant_id: string
  amount: number
  interest_rate: number
  term_months: number
  purpose: string
  status: 'PENDING' | 'APPROVED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED'
  installment_value: number
  total_amount: number
  iof_amount: number
  cet_rate: number
}

export interface ApiResponse<T> {
  data: T
  meta?: {
    pagination?: {
      page: number
      limit: number
      total: number
      pages: number
    }
  }
}

export interface ApiError {
  errors: Array<{
    status: string
    code: string
    detail: string
    source?: {
      pointer?: string
      parameter?: string
    }
  }>
}
