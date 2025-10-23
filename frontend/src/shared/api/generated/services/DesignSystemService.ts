/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DesignSystemStoryPage } from '../models/DesignSystemStoryPage';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DesignSystemService {
    /**
     * Listar stories multi-tenant com status de acessibilidade
     * Disponibiliza stories publicados para consumo por Chromatic/Storybook, com metadados de cobertura visual e auditoria axe-core. Utiliza ETag e paginação.
     *
     * @returns DesignSystemStoryPage Lista de stories.
     * @throws ApiError
     */
    public static listDesignSystemStories({
        xTenantId,
        page = 1,
        perPage = 25,
        componentId,
        tag,
        traceparent,
        tracestate,
    }: {
        /**
         * Tenant solicitado; se omitido usa o tenant default do subdomínio. Em desenvolvimento/local sem subdomínio, o fallback é `tenant-default` (configuração de ambiente). Em staging/prod, o subdomínio prevalece e o header é apenas filtro/otimização.
         *
         */
        xTenantId?: string,
        /**
         * Página solicitada (1-indexed).
         */
        page?: number,
        /**
         * Tamanho da página.
         */
        perPage?: number,
        /**
         * Filtrar por componente (`shared/ui/button`).
         */
        componentId?: string,
        /**
         * Filtrar por tag (ex.: `critical`).
         */
        tag?: string,
        /**
         * Cabeçalho W3C Trace Context.
         */
        traceparent?: string,
        /**
         * Cabeçalho W3C Trace Context state.
         */
        tracestate?: string,
    }): CancelablePromise<DesignSystemStoryPage> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/design-system/stories',
            headers: {
                'X-Tenant-Id': xTenantId,
                'traceparent': traceparent,
                'tracestate': tracestate,
            },
            query: {
                'page': page,
                'per_page': perPage,
                'componentId': componentId,
                'tag': tag,
            },
            errors: {
                429: `Rate limiting atingido.`,
            },
        });
    }
}
