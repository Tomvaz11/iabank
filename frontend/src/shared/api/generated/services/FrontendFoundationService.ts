/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { FeatureScaffoldRequest } from '../models/FeatureScaffoldRequest';
import type { FeatureScaffoldResponse } from '../models/FeatureScaffoldResponse';
import type { TenantMetricPage } from '../models/TenantMetricPage';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FrontendFoundationService {
    /**
     * Registrar scaffolding de uma feature FSD
     * Endpoint idempotente responsável por registrar, validar e auditar o scaffolding de uma nova feature FSD. Requer chave de idempotência, executa validações de lint e propaga métricas SC-001/SC-003.
     *
     * @returns FeatureScaffoldResponse Scaffolding registrado com sucesso.
     * @returns any Scaffolding aceito e em processamento assíncrono.
     * @throws ApiError
     */
    public static registerFeatureScaffold({
        tenantId,
        xTenantId,
        requestBody,
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
        requestBody: FeatureScaffoldRequest,
        /**
         * Cabeçalho W3C Trace Context.
         */
        traceparent?: string,
        /**
         * Cabeçalho W3C Trace Context state.
         */
        tracestate?: string,
    }): CancelablePromise<FeatureScaffoldResponse | any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/tenants/{tenantId}/features/scaffold',
            path: {
                'tenantId': tenantId,
            },
            headers: {
                'X-Tenant-Id': xTenantId,
                'traceparent': traceparent,
                'tracestate': tracestate,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                400: `Requisição inválida (erro de validação).`,
                409: `Recurso já existente ou versão desatualizada (ETag).`,
                422: `Erros semânticos (lint, testes) bloqueando publicação.`,
            },
        });
    }
    /**
     * Consultar métricas SC agregadas por tenant
     * Fornece métricas SC-001 a SC-005 agregadas por tenant, alimentadas pelos pipelines CI/CD (Chromatic, Lighthouse, Pact). Resultados mascaram PII e são paginados para relatórios.
     *
     * @returns TenantMetricPage Página de métricas retornada.
     * @throws ApiError
     */
    public static listTenantSuccessMetrics({
        tenantId,
        xTenantId,
        page = 1,
        perPage = 25,
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
         * Página solicitada (1-indexed).
         */
        page?: number,
        /**
         * Tamanho da página.
         */
        perPage?: number,
        /**
         * Cabeçalho W3C Trace Context.
         */
        traceparent?: string,
        /**
         * Cabeçalho W3C Trace Context state.
         */
        tracestate?: string,
    }): CancelablePromise<TenantMetricPage> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/tenant-metrics/{tenantId}/sc',
            path: {
                'tenantId': tenantId,
            },
            headers: {
                'X-Tenant-Id': xTenantId,
                'traceparent': traceparent,
                'tracestate': tracestate,
            },
            query: {
                'page': page,
                'per_page': perPage,
            },
            errors: {
                404: `Recurso não encontrado.`,
                429: `Rate limiting atingido.`,
            },
        });
    }
}
