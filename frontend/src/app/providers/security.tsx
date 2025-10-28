import { env } from '../../shared/config/env';

type TrustedTypesPolicy = {
  name: string;
  createHTML: (input: unknown) => string;
  createScript: (input: unknown) => string;
  createScriptURL: (input: unknown) => string;
};

type TrustedTypesPolicyOptions = {
  createHTML?: (input: unknown) => string;
  createScript?: (input: unknown) => string;
  createScriptURL?: (input: unknown) => string;
};

type TrustedTypesApi = {
  getPolicy?: (name: string) => TrustedTypesPolicy | null;
  createPolicy?: (name: string, options: TrustedTypesPolicyOptions) => TrustedTypesPolicy;
};

type TrustedTypesAwareWindow = Window & {
  trustedTypes?: TrustedTypesApi;
};

type Props = {
  children: React.ReactNode;
};

type TrustedTypesDisposition = 'report-only' | 'enforce';

const REPORT_ONLY_WINDOW_MS = 30 * 24 * 60 * 60 * 1000;
const TRUSTED_TYPES_DIRECTIVE = 'trusted-types';

let cachedPolicy: TrustedTypesPolicy | null = null;

const createPolicy = (): TrustedTypesPolicy | null => {
  if (cachedPolicy) {
    return cachedPolicy;
  }

  if (typeof window === 'undefined') {
    return null;
  }

  const trustedTypesApi = (window as TrustedTypesAwareWindow).trustedTypes;
  if (!trustedTypesApi) {
    return null;
  }

  const policyName = env.FOUNDATION_TRUSTED_TYPES_POLICY || 'foundation-ui';

  if (typeof trustedTypesApi.getPolicy === 'function') {
    const existing = trustedTypesApi.getPolicy(policyName);
    if (existing) {
      cachedPolicy = existing;
      return existing;
    }
  }

  if (typeof trustedTypesApi.createPolicy !== 'function') {
    return null;
  }

  if (typeof trustedTypesApi.createPolicy !== 'function') {
    return null;
  }

  cachedPolicy = trustedTypesApi.createPolicy(policyName, {
    createHTML: (input) => String(input),
    createScript: (input) => String(input),
    createScriptURL: (input) => String(input),
  });

  return cachedPolicy;
};

export const ensureTrustedTypesPolicy = (): TrustedTypesPolicy | null => {
  if (cachedPolicy) {
    return cachedPolicy;
  }

  return createPolicy();
};


if (typeof window !== 'undefined') {
  ensureTrustedTypesPolicy();
}
export const resetTrustedTypesPolicy = () => {
  cachedPolicy = null;
};

export const resolveTrustedTypesDisposition = ({
  startedAt,
  now,
}: {
  startedAt: string;
  now: Date;
}): { mode: TrustedTypesDisposition; expiresAt: Date } => {
  const start = Number.isNaN(Date.parse(startedAt)) ? new Date() : new Date(startedAt);
  const expiresAt = new Date(start.getTime() + REPORT_ONLY_WINDOW_MS);
  const mode: TrustedTypesDisposition = now < expiresAt ? 'report-only' : 'enforce';

  return { mode, expiresAt };
};

type ViolationHandler = (event: SecurityPolicyViolationEvent) => void;

type SecurityViolationReporterOptions = {
  mode: TrustedTypesDisposition;
  reportOnlyThreshold: number;
  onReportOnlyViolation: ViolationHandler;
  onEnforcedViolation: ViolationHandler;
};

export const createSecurityViolationReporter = ({
  mode,
  reportOnlyThreshold,
  onReportOnlyViolation,
  onEnforcedViolation,
}: SecurityViolationReporterOptions): ((event: SecurityPolicyViolationEvent) => void) => {
  let reportOnlyCount = 0;

  const isTrustedTypesViolation = (event: SecurityPolicyViolationEvent): boolean => {
    const directive = event.violatedDirective ?? '';
    return directive.toLowerCase().includes(TRUSTED_TYPES_DIRECTIVE);
  };

  return (event: SecurityPolicyViolationEvent): void => {
    if (!event || !isTrustedTypesViolation(event)) {
      return;
    }

    if (mode === 'enforce' || event.disposition === 'enforce') {
      onEnforcedViolation(event);
      return;
    }

    reportOnlyCount += 1;
    onReportOnlyViolation(event);

    if (reportOnlyCount >= reportOnlyThreshold) {
      onEnforcedViolation(event);
    }
  };
};

export const SecurityProvider = ({ children }: Props) => {
  ensureTrustedTypesPolicy();
  return <>{children}</>;
};
