"""
Configuracoes compartilhadas de retencao WORM.

Especificacao: 30 dias legais + 5 anos adicionais (30 + 5 * 365 = 1855 dias).
"""

MIN_WORM_RETENTION_DAYS = 30 + (5 * 365)
