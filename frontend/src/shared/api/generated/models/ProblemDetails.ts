/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type ProblemDetails = {
    type: string;
    title: string;
    status: number;
    detail?: string;
    instance?: string;
    traceId: string;
    violations?: Array<{
        field?: string;
        message?: string;
    }>;
};

