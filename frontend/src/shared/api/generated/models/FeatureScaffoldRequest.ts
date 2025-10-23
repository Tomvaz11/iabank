/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FeatureScaffoldRequest = {
    featureSlug: string;
    initiatedBy: string;
    slices: Array<{
        slice: 'app' | 'pages' | 'features' | 'entities' | 'shared';
        files: Array<{
            path: string;
            /**
             * SHA-256 do arquivo gerado.
             */
            checksum: string;
        }>;
    }>;
    lintCommitHash: string;
    scReferences: Array<string>;
    durationMs?: number;
    /**
     * Campos adicionais (ex.: versão do CLI).
     */
    metadata?: Record<string, any>;
};

