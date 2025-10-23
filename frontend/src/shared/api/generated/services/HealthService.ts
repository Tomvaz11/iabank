/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HealthService {
    /**
     * Health check
     * Retorna o status de saúde do serviço de fundação frontend.
     * @returns any OK
     * @throws ApiError
     */
    public static getHealthCheck(): CancelablePromise<{
        status?: string;
    }> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health',
        });
    }
}
