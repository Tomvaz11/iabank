/**
 * Tipos TypeScript para feature de listagem de empréstimos.
 * 
 * Define interfaces e tipos para empréstimos, filtros
 * e ViewModels conforme especificado no Blueprint.
 */

// Placeholder para tipos da feature loan-list
// A implementação completa será realizada nas próximas fases do projeto

export interface LoanListViewModel {
  id: number;
  customerName: string;
  principalAmountFormatted: string;
  status: "IN_PROGRESS" | "PAID_OFF" | "IN_COLLECTION" | "CANCELED";
  statusLabel: string;
  statusColor: "yellow" | "green" | "red" | "gray";
  contractDateFormatted: string;
  installmentsProgress: string;
}