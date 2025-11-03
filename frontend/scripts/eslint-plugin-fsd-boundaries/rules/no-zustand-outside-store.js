const path = require('node:path');

const ALLOWED_SEGMENTS = [
  `${path.sep}src${path.sep}app${path.sep}store`,
  `${path.sep}src${path.sep}shared${path.sep}store`
];

const isWorkspaceFile = (filename) =>
  filename !== '<input>' && filename.includes(`${path.sep}src${path.sep}`);

const isAllowedFile = (filename) => ALLOWED_SEGMENTS.some((segment) => filename.includes(segment));

const isZustandImport = (value) =>
  value === 'zustand' || value.startsWith('zustand/') || value.startsWith('zustand\\');

module.exports = {
  meta: {
    type: 'problem',
    docs: {
      description: 'Restringe uso de Zustand a stores globais autorizados',
      recommended: true
    },
    schema: [],
    messages: {
      restrictedUsage:
        'Zustand só pode ser importado em stores globais (src/app/store ou src/shared/store).'
    }
  },
  create(context) {
    const filename = context.getFilename();

    if (!isWorkspaceFile(filename) || isAllowedFile(filename)) {
      return {};
    }

    const reportIfNeeded = (node, sourceValue) => {
      if (typeof sourceValue !== 'string') {
        return;
      }

      if (!isZustandImport(sourceValue)) {
        return;
      }

      context.report({
        node,
        messageId: 'restrictedUsage'
      });
    };

    return {
      ImportDeclaration(node) {
        reportIfNeeded(node.source, node.source.value);
      },
      CallExpression(node) {
        if (
          node.callee.type === 'Identifier' &&
          node.callee.name === 'require' &&
          node.arguments.length === 1 &&
          node.arguments[0].type === 'Literal'
        ) {
          reportIfNeeded(node.arguments[0], node.arguments[0].value);
        }
      }
    };
  }
};
