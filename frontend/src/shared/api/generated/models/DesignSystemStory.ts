/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type DesignSystemStory = {
    id: string;
    tenantId?: string | null;
    componentId: string;
    storyId: string;
    tags?: Array<string>;
    coveragePercent: number;
    axeStatus: DesignSystemStory.axeStatus;
    chromaticBuild: string;
    storybookUrl?: string;
    updatedAt: string;
};
export namespace DesignSystemStory {
    export enum axeStatus {
        PASS = 'pass',
        FAIL = 'fail',
        WARN = 'warn',
    }
}

