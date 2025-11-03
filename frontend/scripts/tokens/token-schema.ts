import { z } from 'zod';

const TOKEN_KEY_PATTERN = /^[a-z0-9]+(?:[.-][a-z0-9]+)*$/i;

const tokenValueSchema = z
  .string({
    required_error: 'Valor de token obrigatório.',
    invalid_type_error: 'Valor de token deve ser string.',
  })
  .min(1, 'Valor de token não pode ser vazio.');

const tokenKeySchema = z
  .string({
    required_error: 'Chave de token obrigatória.',
    invalid_type_error: 'Chave de token deve ser string.',
  })
  .regex(TOKEN_KEY_PATTERN, 'Chave de token fora do padrão esperado.');

const tokenCategorySchema = z.record(tokenKeySchema, tokenValueSchema);

export const TokenSchema = z
  .object({
    foundation: tokenCategorySchema,
    semantic: tokenCategorySchema,
    component: tokenCategorySchema,
  })
  .strict();

export const WcagReportSchema = z
  .record(z.string(), z.record(z.string(), z.unknown()))
  .optional()
  .nullable();

const semverPattern = /^\d+\.\d+\.\d+$/;

export const TenantThemeResponseSchema = z.object({
  tenantId: z.string().uuid('tenantId deve ser um UUID válido.'),
  version: z.string().regex(semverPattern, 'version deve seguir o padrão SemVer (ex.: 1.2.3).'),
  generatedAt: z.string().datetime({
    message: 'generatedAt deve estar em formato ISO 8601.',
  }),
  categories: TokenSchema,
  wcagReport: WcagReportSchema,
});

export type TokenCategories = z.infer<typeof TokenSchema>;
export type TenantThemePayload = z.infer<typeof TenantThemeResponseSchema>;

export const tokenSchemaJson = {
  type: 'object',
  additionalProperties: false,
  required: ['foundation', 'semantic', 'component'],
  properties: {
    foundation: {
      type: 'object',
      additionalProperties: {
        type: 'string',
        minLength: 1,
      },
      propertyNames: {
        type: 'string',
        pattern: TOKEN_KEY_PATTERN.source,
      },
    },
    semantic: {
      type: 'object',
      additionalProperties: {
        type: 'string',
        minLength: 1,
      },
      propertyNames: {
        type: 'string',
        pattern: TOKEN_KEY_PATTERN.source,
      },
    },
    component: {
      type: 'object',
      additionalProperties: {
        type: 'string',
        minLength: 1,
      },
      propertyNames: {
        type: 'string',
        pattern: TOKEN_KEY_PATTERN.source,
      },
    },
  },
} as const;

export const tenantThemeSchemaJson = {
  type: 'object',
  additionalProperties: false,
  required: ['tenantId', 'version', 'generatedAt', 'categories'],
  properties: {
    tenantId: {
      type: 'string',
      format: 'uuid',
    },
    version: {
      type: 'string',
      pattern: semverPattern.source,
    },
    generatedAt: {
      type: 'string',
      format: 'date-time',
    },
    categories: tokenSchemaJson,
    wcagReport: {
      type: 'object',
      additionalProperties: {
        type: 'object',
      },
      nullable: true,
    },
  },
} as const;
