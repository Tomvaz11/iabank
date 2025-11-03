const pkg = require('./package.json');

module.exports = {
  meta: {
    name: 'eslint-plugin-fsd-boundaries',
    version: pkg.version
  },
  rules: {
    'enforce-layer-boundaries': require('./rules/enforce-layer-boundaries'),
    'no-zustand-outside-store': require('./rules/no-zustand-outside-store')
  }
};
