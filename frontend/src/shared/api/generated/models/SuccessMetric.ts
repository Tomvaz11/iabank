/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SuccessMetric = {
    code: SuccessMetric.code;
    value: number;
    collectedAt: string;
    source?: SuccessMetric.source;
};
export namespace SuccessMetric {
    export enum code {
        SC_001 = 'SC-001',
        SC_002 = 'SC-002',
        SC_003 = 'SC-003',
        SC_004 = 'SC-004',
        SC_005 = 'SC-005',
    }
    export enum source {
        CI = 'ci',
        CHROMATIC = 'chromatic',
        LIGHTHOUSE = 'lighthouse',
        MANUAL = 'manual',
    }
}

