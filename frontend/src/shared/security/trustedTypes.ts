type TrustedTypesDisposition = 'report-only' | 'enforce';

const REPORT_ONLY_WINDOW_MS = 30 * 24 * 60 * 60 * 1000;

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

export type { TrustedTypesDisposition };
