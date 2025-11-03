const path = require('node:path');

const LAYERS = ['shared', 'entities', 'features', 'pages', 'app'];
const LAYER_ORDER = LAYERS.reduce((acc, layer, index) => {
  acc[layer] = index;
  return acc;
}, Object.create(null));

const ALIAS_TO_LAYER = {
  '@shared': 'shared',
  '@entities': 'entities',
  '@features': 'features',
  '@pages': 'pages',
  '@app': 'app',
  '@tests': 'tests'
};

const PUBLIC_API_LAYERS = new Set(['features', 'entities', 'pages']);
const CROSS_FEATURE_LAYERS = new Set(['features']);

const isWorkspaceFile = (filename) =>
  filename !== '<input>' && filename.includes(`${path.sep}src${path.sep}`);

const getLayerInfo = (filename) => {
  const normalized = path.normalize(filename);
  const segments = normalized.split(path.sep);
  const srcIndex = segments.lastIndexOf('src');
  if (srcIndex === -1) {
    return { layer: null, slice: null, rest: [] };
  }

  const candidate = segments[srcIndex + 1];
  if (!candidate) {
    return { layer: 'app', slice: null, rest: [] };
  }

  if (candidate === 'tests') {
    return { layer: 'tests', slice: null, rest: [] };
  }

  const layer = LAYERS.includes(candidate) ? candidate : 'app';
  const afterLayer = segments.slice(srcIndex + 2);
  const first = afterLayer[0] ?? null;
  const isFile = typeof first === 'string' && first.includes('.');
  const slice = isFile ? null : first ?? null;
  const rest = slice ? afterLayer.slice(1) : afterLayer;

  return { layer, slice, rest };
};

const resolveImportInfo = (fromFilename, rawSource) => {
  if (typeof rawSource !== 'string') {
    return null;
  }

  if (ALIAS_TO_LAYER[rawSource]) {
    return {
      layer: ALIAS_TO_LAYER[rawSource],
      slice: null,
      subpath: [],
      importKind: 'alias',
      raw: rawSource
    };
  }

  for (const [alias, layer] of Object.entries(ALIAS_TO_LAYER)) {
    if (rawSource === alias) {
      return { layer, slice: null, subpath: [], importKind: 'alias', raw: rawSource, alias };
    }

    if (rawSource.startsWith(`${alias}/`)) {
      const remainder = rawSource.slice(alias.length + 1);
      const parts = remainder.split(/[\\/]/).filter(Boolean);
      const slice = parts[0] ?? null;
      const subpath = parts.slice(1);
      return {
        layer,
        slice,
        subpath,
        importKind: 'alias',
        raw: rawSource,
        alias
      };
    }
  }

  if (rawSource.startsWith('.') || rawSource.startsWith('..')) {
    const resolved = path.resolve(path.dirname(fromFilename), rawSource);
    const info = getLayerInfo(resolved);
    return {
      layer: info.layer,
      slice: info.slice,
      subpath: info.rest,
      importKind: 'relative',
      raw: rawSource,
      resolvedPath: resolved
    };
  }

  return {
    layer: null,
    slice: null,
    subpath: [],
    importKind: 'external',
    raw: rawSource
  };
};

const shouldReportPrivateImport = (fromInfo, importInfo) => {
  if (!importInfo.slice) {
    return false;
  }

  if (!PUBLIC_API_LAYERS.has(importInfo.layer)) {
    return false;
  }

  const isSameSlice =
    fromInfo.layer === importInfo.layer &&
    Boolean(fromInfo.slice) &&
    fromInfo.slice === importInfo.slice;

  if (importInfo.importKind === 'alias') {
    if (importInfo.subpath.length === 0) {
      return false;
    }

    if (importInfo.subpath.length === 1 && importInfo.subpath[0] === 'index') {
      return false;
    }

    if (isSameSlice && importInfo.subpath.length === 0) {
      return false;
    }

    return true;
  }

  if (importInfo.importKind === 'relative') {
    if (isSameSlice) {
      return false;
    }

    return true;
  }

  return false;
};

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Enforce Feature-Sliced Design layer boundaries',
      recommended: true
    },
    schema: [
      {
        type: 'object',
        properties: {
          allow: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                from: { type: 'string' },
                to: { type: 'string' }
              },
              required: ['from', 'to'],
              additionalProperties: false
            }
          }
        },
        additionalProperties: false
      }
    ],
    messages: {
      forbiddenImport:
        'A camada "{{fromLayer}}" não pode importar da camada "{{toLayer}}" segundo a FSD.',
      crossFeatureImport:
        'Features devem depender apenas da própria fatia; "{{fromSlice}}" não pode importar "{{targetSlice}}".',
      privateImport:
        'Imports diretos para arquivos internos de "{{layer}}/{{slice}}" violam a API pública (use o index.ts exposto).'
    }
  },
  create(context) {
    const filename = context.getFilename();

    if (!isWorkspaceFile(filename)) {
      return {};
    }

    const allowMatrix = new Set(
      (context.options[0]?.allow ?? []).map(
        ({ from, to }) => `${from.toLowerCase()}->${to.toLowerCase()}`,
      ),
    );

    const fromInfo = getLayerInfo(filename);
    const fromLayer = fromInfo.layer;

    if (!fromLayer || fromLayer === 'tests') {
      return {};
    }

    return {
      ImportDeclaration(node) {
        const importInfo = resolveImportInfo(filename, node.source?.value);
        const targetLayer = importInfo?.layer;

        if (!targetLayer || targetLayer === 'tests') {
          return;
        }

        if (!LAYERS.includes(targetLayer)) {
          return;
        }

        const isExplicitlyAllowed = allowMatrix.has(`${fromLayer}->${targetLayer}`);
        if (isExplicitlyAllowed) {
          return;
        }

        if (
          CROSS_FEATURE_LAYERS.has(fromLayer) &&
          targetLayer === fromLayer &&
          fromInfo.slice &&
          importInfo.slice &&
          fromInfo.slice !== importInfo.slice
        ) {
          context.report({
            node: node.source,
            messageId: 'crossFeatureImport',
            data: {
              fromSlice: fromInfo.slice,
              targetSlice: importInfo.slice
            }
          });
          return;
        }

        if (importInfo.slice && shouldReportPrivateImport(fromInfo, importInfo)) {
          context.report({
            node: node.source,
            messageId: 'privateImport',
            data: {
              layer: targetLayer,
              slice: importInfo.slice
            }
          });
          return;
        }

        const fromOrder = LAYER_ORDER[fromLayer];
        const toOrder = LAYER_ORDER[targetLayer];

        if (typeof fromOrder === 'undefined' || typeof toOrder === 'undefined') {
          return;
        }

        if (toOrder > fromOrder) {
          context.report({
            node: node.source,
            messageId: 'forbiddenImport',
            data: {
              fromLayer,
              toLayer: targetLayer
            }
          });
        }
      }
    };
  }
};
