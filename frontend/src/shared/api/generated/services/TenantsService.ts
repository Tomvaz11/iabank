/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TenantThemeResponse } from '../models/TenantThemeResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TenantsService {
    /**
     * Recuperar tokens ativos do tenant corrente
     * Retorna o conjunto de tokens fundacionais, semânticos e de componentes aplicados ao tenant corrente. Respeita RLS (Art. XIII) e mascaramento de PII em logs. Respostas incluem ETag para controle de concorrência em caches front-end.
     *
     * @returns TenantThemeResponse Tokens retornados com sucesso.
     * @throws ApiError
     */
    public static getTenantTheme({
        tenantId,
        xTenantId,
        traceparent,
        tracestate,
    }: {
        /**
         * Identificador do tenant (UUID).
         */
        tenantId: string,
        /**
         * Tenant corrente propagado pelo gateway. Deve coincidir com o `tenantId` da rota.
         *
         */
        xTenantId: string,
        /**
         * Cabeçalho W3C Trace Context.
         */
        traceparent?: string,
        /**
         * Cabeçalho W3C Trace Context state.
         */
        tracestate?: string,
    }): CancelablePromise<TenantThemeResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/tenants/{tenantId}/themes/current',
            path: {
                'tenantId': tenantId,
            },
            headers: {
                'X-Tenant-Id': xTenantId,
                'traceparent': traceparent,
                'tracestate': tracestate,
            },
            errors: {
                304: `Não modificado (comparação via If-None-Match).`,
                404: `Recurso não encontrado.`,
                429: `Rate limiting atingido.`,
            },
        });
    }
}
