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

const isWorkspaceFile = (filename) =>
  filename !== '<input>' && filename.includes(`${path.sep}src${path.sep}`);

const findLayerFromPath = (filename) => {
  const normalized = path.normalize(filename);
  const segments = normalized.split(path.sep);
  const srcIndex = segments.lastIndexOf('src');
  if (srcIndex === -1) {
    return null;
  }

  const candidate = segments[srcIndex + 1];
  if (!candidate) {
    return 'app';
  }

  if (candidate === 'tests') {
    return 'tests';
  }

  if (LAYERS.includes(candidate)) {
    return candidate;
  }

  return 'app';
};

const resolveImportLayer = (context, node, fromFilename) => {
  const sourceValue = node.source.value;

  if (typeof sourceValue !== 'string') {
    return null;
  }

  if (ALIAS_TO_LAYER[sourceValue]) {
    return ALIAS_TO_LAYER[sourceValue];
  }

  for (const [alias, layer] of Object.entries(ALIAS_TO_LAYER)) {
    if (sourceValue.startsWith(`${alias}/`)) {
      return layer;
    }
  }

  if (sourceValue.startsWith('.') || sourceValue.startsWith('..')) {
    const resolved = path.resolve(path.dirname(fromFilename), sourceValue);
    return findLayerFromPath(resolved);
  }

  return null;
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
        'A camada "{{fromLayer}}" não pode importar da camada "{{toLayer}}" segundo a FSD.'
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

    const fromLayer = findLayerFromPath(filename);

    if (!fromLayer || fromLayer === 'tests') {
      return {};
    }

    return {
      ImportDeclaration(node) {
        const targetLayer = resolveImportLayer(context, node, filename);

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
