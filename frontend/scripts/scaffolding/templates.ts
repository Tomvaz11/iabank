export type ScaffoldSlice = 'app' | 'pages' | 'features' | 'entities' | 'shared';

export type TemplateContext = {
  featureSlug: string;
  featureName: string;
  featureTitle: string;
};

export type TemplateFile = {
  relativePath: string;
  content: string;
};

export type ScaffoldTemplate = {
  slice: ScaffoldSlice;
  files: TemplateFile[];
};

const createAppRoute = ({ featureSlug, featureName, featureTitle }: TemplateContext): TemplateFile => ({
  relativePath: `app/${featureSlug}/route.tsx`,
  content: `import { lazy, Suspense } from 'react';

const ${featureName}Page = lazy(() => import('../../pages/${featureSlug}'));

export const ${featureName}Route = (): JSX.Element => {
  return (
    <Suspense fallback={<div>Carregando scaffolding de ${featureTitle}…</div>}>
      <${featureName}Page />
    </Suspense>
  );
};
`,
});

const createAppIndex = ({ featureSlug, featureName }: TemplateContext): TemplateFile => ({
  relativePath: `app/${featureSlug}/index.ts`,
  content: `export { ${featureName}Route } from './route';
export const FEATURE_ROUTE = '/foundation/${featureSlug}';
`,
});

const createPage = ({ featureSlug, featureTitle, featureName }: TemplateContext): TemplateFile => ({
  relativePath: `pages/${featureSlug}/index.tsx`,
  content: `import { useMemo } from 'react';

import { use${featureName}Summary } from '../../features/${featureSlug}/queries';
import '../../shared/${featureSlug}/styles.css';

export const ${featureName}Page = (): JSX.Element => {
  const { data, status } = use${featureName}Summary();

  const summary = useMemo(() => {
    if (!data) {
      return { feature: '${featureSlug}', tenantId: 'desconhecido' };
    }

    return data;
  }, [data]);

  return (
    <section className="scaffold-page">
      <header>
        <h1>{summary.displayName}</h1>
        <p>Status: {status}</p>
      </header>

      <article>
        <p>Feature: {summary.feature}</p>
        <p>Tenant: {summary.tenantId}</p>
      </article>
    </section>
  );
};

export default ${featureName}Page;
`,
});

const createFeatureQueries = ({ featureSlug, featureTitle, featureName }: TemplateContext): TemplateFile => ({
  relativePath: `features/${featureSlug}/queries.ts`,
  content: `import { useQuery } from '@tanstack/react-query';

import { useAppStore } from '../../app/store';
import { buildTenantQueryKey } from '../../shared/api/queryClient';
import { env } from '../../shared/config/env';
import type { ${featureName}Summary } from '../../entities/${featureSlug}/schema';

export const ${featureName}_QUERY_TAGS = ['critical', '${featureSlug}'] as const;

const buildSummary = (tenantId: string): ${featureName}Summary => ({
  feature: '${featureSlug}',
  displayName: '${featureTitle}',
  tenantId,
  generatedAt: new Date().toISOString(),
});

export const use${featureName}Summary = () => {
  const tenantId = useAppStore((state) => state.tenant.id ?? env.TENANT_DEFAULT);

  return useQuery({
    queryKey: buildTenantQueryKey(tenantId, 'scaffold', '${featureSlug}'),
    queryFn: async () => buildSummary(tenantId),
    gcTime: 10 * 60 * 1000,
    enabled: Boolean(tenantId),
    meta: {
      tags: Array.from(${featureName}_QUERY_TAGS),
    },
  });
};
`,
});

const createEntitySchema = ({ featureSlug, featureName, featureTitle }: TemplateContext): TemplateFile => ({
  relativePath: `entities/${featureSlug}/schema.ts`,
  content: `import { z } from 'zod';

export const ${featureName}Schema = z.object({
  feature: z.literal('${featureSlug}'),
  displayName: z.string().min(1),
  tenantId: z.string().min(1),
  generatedAt: z.string().datetime(),
});

export type ${featureName}Summary = z.infer<typeof ${featureName}Schema>;
`,
});

const createSharedStyles = ({ featureSlug }: TemplateContext): TemplateFile => ({
  relativePath: `shared/${featureSlug}/styles.css`,
  content: `.scaffold-page {
  display: grid;
  gap: 1.5rem;
  padding: 2rem;
  border-radius: 1rem;
  background: var(--foundation-surface, #111827);
  color: var(--foundation-on-surface, #f9fafb);
}

.scaffold-page header h1 {
  font-size: clamp(2rem, 3vw, 3rem);
  margin: 0;
}

.scaffold-page article {
  display: grid;
  gap: 0.5rem;
}
`,
});

const sanitizeName = (value: string): string =>
  value
    .split(/[-_\\s]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');

export const buildTemplateContext = (featureSlug: string): TemplateContext => {
  const featureName = sanitizeName(featureSlug);
  const featureTitle = featureSlug
    .split(/[-_\\s]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

  return {
    featureSlug,
    featureName,
    featureTitle,
  };
};

export const createScaffoldTemplates = (context: TemplateContext): ScaffoldTemplate[] => [
  {
    slice: 'app',
    files: [createAppRoute(context), createAppIndex(context)],
  },
  {
    slice: 'pages',
    files: [createPage(context)],
  },
  {
    slice: 'features',
    files: [createFeatureQueries(context)],
  },
  {
    slice: 'entities',
    files: [createEntitySchema(context)],
  },
  {
    slice: 'shared',
    files: [createSharedStyles(context)],
  },
];
