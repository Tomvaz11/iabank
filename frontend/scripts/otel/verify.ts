import { randomUUID } from 'node:crypto';
import process from 'node:process';
import { pathToFileURL } from 'node:url';

import { context, propagation, trace } from '@opentelemetry/api';
import type { ExportResult } from '@opentelemetry/core';
import { ExportResultCode } from '@opentelemetry/core';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import {
  BasicTracerProvider,
  ReadableSpan,
  SimpleSpanProcessor,
  SpanExporter,
} from '@opentelemetry/sdk-trace-base';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

import {
  sanitizeTelemetryAttributes,
  piiRedactionToken,
} from '../../src/shared/lib/telemetry/masking';

const DEFAULT_FEATURE_SLUG = 'foundation-otel-verify';
const DEFAULT_SAMPLE_PII = {
  'user.email': 'observability@iabank.com',
  'user.phone': '+55 11 91234-5678',
  'user.cpf': '123.456.789-09',
};
const SPAN_NAME = 'FOUNDATION-TENANT-BOOTSTRAP';

const PII_PATTERNS: RegExp[] = [
  /\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/,
  /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/i,
  /\+?\d{1,3}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b/,
];

export type VerifyTelemetryOptions = {
  tenantId: string;
  featureSlug: string;
  endpoint: string;
  serviceName: string;
  resourceAttributes: Record<string, string>;
  additionalAttributes?: Record<string, unknown>;
  dryRun?: boolean;
};

export type VerificationReport = {
  spanName: string;
  attributes: Record<string, unknown>;
  maskedKeys: string[];
  baggage: Record<string, string>;
  exportedSpans: number;
  dryRun: boolean;
  errors: string[];
};

class VerificationExporter implements SpanExporter {
  private readonly stored: ReadableSpan[] = [];

  constructor(private readonly delegate?: SpanExporter) {}

  export(spans: ReadableSpan[], resultCallback: (result: ExportResult) => void): void {
    this.stored.push(...spans);

    if (this.delegate) {
      this.delegate.export(spans, resultCallback);
      return;
    }

    resultCallback({ code: ExportResultCode.SUCCESS });
  }

  async shutdown(): Promise<void> {
    if (this.delegate?.shutdown) {
      await this.delegate.shutdown();
    }
  }

  async forceFlush(): Promise<void> {
    if (typeof this.delegate?.forceFlush === 'function') {
      await this.delegate.forceFlush();
    }
  }

  get spans(): ReadableSpan[] {
    return this.stored;
  }
}

const ensureNonEmpty = (value: string | undefined, message: string): string => {
  if (!value || value.trim().length === 0) {
    throw new Error(message);
  }

  return value;
};

const parseResourceAttributes = (value: string | undefined): Record<string, string> => {
  if (!value) {
    return {};
  }

  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((attributes, entry) => {
      const [key, raw] = entry.split('=');
      if (key && raw) {
        attributes[key.trim()] = raw.trim();
      }
      return attributes;
    }, {});
};

const flattenAttributes = (
  attributes: Record<string, unknown>,
  prefix = '',
): Record<string, unknown> => {
  return Object.entries(attributes).reduce<Record<string, unknown>>((acc, [key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;

    if (value == null || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      acc[path] = value;
      return acc;
    }

    if (Array.isArray(value)) {
      acc[path] = value.map((item) => {
        if (item == null || typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') {
          return item;
        }
        return JSON.stringify(item);
      });
      return acc;
    }

    if (value instanceof Date) {
      acc[path] = value.toISOString();
      return acc;
    }

    acc = { ...acc, ...flattenAttributes(value as Record<string, unknown>, path) };
    return acc;
  }, {});
};

const collectMaskedKeys = (attributes: Record<string, unknown>): string[] => {
  const masked: string[] = [];

  Object.entries(attributes).forEach(([key, value]) => {
    if (value === piiRedactionToken) {
      masked.push(key);
      return;
    }

    if (Array.isArray(value) && value.some((item) => item === piiRedactionToken)) {
      masked.push(key);
    }
  });

  return masked;
};

const detectResidualPii = (attributes: Record<string, unknown>): string[] => {
  const offenders: string[] = [];

  Object.entries(attributes).forEach(([key, value]) => {
    if (typeof value === 'string') {
      if (value !== piiRedactionToken && PII_PATTERNS.some((pattern) => pattern.test(value))) {
        offenders.push(key);
      }
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item, index) => {
        if (typeof item === 'string' && item !== piiRedactionToken && PII_PATTERNS.some((pattern) => pattern.test(item))) {
          offenders.push(`${key}[${index}]`);
        }
      });
    }
  });

  return offenders;
};

export const verifyTelemetry = async (options: VerifyTelemetryOptions): Promise<VerificationReport> => {
  const tenantId = ensureNonEmpty(options.tenantId, 'Informe --tenant ou variável FOUNDATION_TENANT_ID.');
  const featureSlug = ensureNonEmpty(options.featureSlug ?? DEFAULT_FEATURE_SLUG, 'Informe um feature slug válido.');
  const endpoint = ensureNonEmpty(options.endpoint, 'Informe --endpoint ou variável OTEL_EXPORTER_OTLP_ENDPOINT.');
  const serviceName = ensureNonEmpty(options.serviceName, 'Informe --service ou variável OTEL_SERVICE_NAME.');
  const resourceAttributes = options.resourceAttributes;

  if (!resourceAttributes || Object.keys(resourceAttributes).length === 0) {
    throw new Error('Informe atributos de resource (ex.: service.namespace=iabank). Use --resource ou OTEL_RESOURCE_ATTRIBUTES.');
  }

  const provider = new BasicTracerProvider({
    resource: new Resource({
      ...resourceAttributes,
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
    }),
  });

  const delegate = options.dryRun ? undefined : new OTLPTraceExporter({ url: endpoint });
  const exporter = new VerificationExporter(delegate);
  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  provider.register();

  const tracer = trace.getTracer(serviceName);

  const verificationId = randomUUID();
  const timestamp = new Date().toISOString();

  const rawAttributes: Record<string, unknown> = {
    'app.tenant_id': tenantId,
    'app.feature_slug': featureSlug,
    'app.verification_id': verificationId,
    'app.verification_timestamp': timestamp,
    ...DEFAULT_SAMPLE_PII,
    ...options.additionalAttributes,
  };

  const sanitizedAttributes = sanitizeTelemetryAttributes(rawAttributes);
  const flattened = flattenAttributes(sanitizedAttributes);
  const cleanAttributes = Object.fromEntries(
    Object.entries(flattened).filter(([, value]) => value !== undefined),
  );
  const maskedKeys = collectMaskedKeys(cleanAttributes);
  const residualPii = detectResidualPii(cleanAttributes);

  const baggageEntries = propagation.createBaggage({
    'tenant.id': { value: tenantId },
    'feature.slug': { value: featureSlug },
    'verification.mode': { value: options.dryRun ? 'dry-run' : 'export' },
  });

  const contextWithBaggage = propagation.setBaggage(context.active(), baggageEntries);

  await context.with(contextWithBaggage, async () => {
    await tracer.startActiveSpan(
      SPAN_NAME,
      (span) => {
        span.setAttributes(cleanAttributes);
        span.addEvent('foundation.otel.verify', cleanAttributes);
        span.end();
      },
    );
  });

  await provider.forceFlush();
  await exporter.forceFlush();
  await provider.shutdown();
  await exporter.shutdown();

  const report: VerificationReport = {
    spanName: SPAN_NAME,
    attributes: cleanAttributes,
    maskedKeys,
    baggage: Object.fromEntries(
      baggageEntries.getAllEntries().map(([key, entry]) => [key, entry.value]),
    ),
    exportedSpans: exporter.spans.length,
    dryRun: Boolean(options.dryRun),
    errors: residualPii.map(
      (key) => `Atributo "${key}" ainda contém dados sensíveis após sanitização.`,
    ),
  };

  return report;
};

type CliOptions = {
  tenantId?: string;
  featureSlug?: string;
  endpoint?: string;
  serviceName?: string;
  resource?: string;
  dryRun?: boolean;
};

const parseCliOptions = (args: string[]): CliOptions => {
  const options: CliOptions = {};

  for (let index = 0; index < args.length; index += 1) {
    const token = args[index];

    if (token === '--dry-run') {
      options.dryRun = true;
      continue;
    }

    if (!token.startsWith('--')) {
      throw new Error(`Argumento inválido: ${token}`);
    }

    const value = args[index + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Argumento ${token} requer um valor.`);
    }

    const key = token.slice(2);
    switch (key) {
      case 'tenant':
      case 'tenant-id':
        options.tenantId = value;
        break;
      case 'feature':
        options.featureSlug = value;
        break;
      case 'endpoint':
        options.endpoint = value;
        break;
      case 'service':
        options.serviceName = value;
        break;
      case 'resource':
        options.resource = value;
        break;
      default:
        throw new Error(`Argumento desconhecido: ${token}`);
    }

    index += 1;
  }

  return options;
};

const resolveOptions = (cli: CliOptions): VerifyTelemetryOptions => {
  const tenantId =
    cli.tenantId ??
    process.env.FOUNDATION_TENANT_ID ??
    process.env.TENANT_ID ??
    process.env.VITE_TENANT_DEFAULT ??
    '';

  const featureSlug =
    cli.featureSlug ??
    process.env.FOUNDATION_FEATURE_SLUG ??
    DEFAULT_FEATURE_SLUG;

  const endpoint =
    cli.endpoint ??
    process.env.OTEL_EXPORTER_OTLP_ENDPOINT ??
    '';

  const serviceName =
    cli.serviceName ??
    process.env.OTEL_SERVICE_NAME ??
    'frontend-foundation';

  const resourceAttributes = parseResourceAttributes(
    cli.resource ?? process.env.OTEL_RESOURCE_ATTRIBUTES,
  );

  return {
    tenantId,
    featureSlug,
    endpoint,
    serviceName,
    resourceAttributes,
    dryRun: cli.dryRun ?? false,
  };
};

const runCli = async (argv: string[] = process.argv.slice(2)): Promise<void> => {
  const args = argv[0] === 'verify' ? argv.slice(1) : argv;
  const cliOptions = parseCliOptions(args);
  const options = resolveOptions(cliOptions);
  const report = await verifyTelemetry(options);

  const output = {
    spanName: report.spanName,
    baggage: report.baggage,
    maskedKeys: report.maskedKeys,
    exportedSpans: report.exportedSpans,
    dryRun: report.dryRun,
    errors: report.errors,
  };

  console.log(JSON.stringify(output, null, 2));

  if (report.errors.length > 0) {
    console.error(report.errors.join('\n'));
    process.exitCode = 1;
  }
};

const isCli = (): boolean => {
  const expected = pathToFileURL(process.argv[1] ?? '').href;
  return import.meta.url === expected;
};

if (isCli()) {
  runCli().catch((error) => {
    const message = error instanceof Error ? error.message : String(error);
    console.error(message);
    process.exitCode = 1;
  });
}

export { parseResourceAttributes, runCli as runVerifyCli };
