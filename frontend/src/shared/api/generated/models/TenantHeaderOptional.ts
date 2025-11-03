/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Tenant solicitado; se omitido usa o tenant default do subdomínio. Em desenvolvimento/local sem subdomínio, o fallback é `tenant-default` (configuração de ambiente). Em staging/prod, o subdomínio prevalece e o header é apenas filtro/otimização.
 *
 */
export type TenantHeaderOptional = string;
