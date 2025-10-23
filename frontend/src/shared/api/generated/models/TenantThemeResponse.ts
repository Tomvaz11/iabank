/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type TenantThemeResponse = {
    tenantId: string;
    version: string;
    generatedAt: string;
    /**
     * Tokens agrupados (`foundation`, `semantic`, `component`).
     */
    categories: Record<string, Record<string, any>>;
    /**
     * Resumo das medições WCAG (contraste, status).
     */
    wcagReport?: Record<string, any>;
};

