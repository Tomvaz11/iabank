/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SuccessMetric } from './SuccessMetric';
export type FeatureScaffoldResponse = {
    scaffoldId: string;
    tenantId: string;
    status: FeatureScaffoldResponse.status;
    recordedAt: string;
    metrics?: Array<SuccessMetric>;
};
export namespace FeatureScaffoldResponse {
    export enum status {
        INITIATED = 'initiated',
        LINTED = 'linted',
        TESTED = 'tested',
        PUBLISHED = 'published',
    }
}

