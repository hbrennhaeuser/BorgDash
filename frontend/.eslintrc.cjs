/* eslint-env node */
require('@rushstack/eslint-patch/modern-module-resolution')

module.exports = {
  root: true,
  'extends': [
    'plugin:vue/vue3-essential',
    'eslint:recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier/skip-formatting'
  ],
  parserOptions: {
    ecmaVersion: 'latest'
  },
  env: {
    node: true, // For tailwind.config.js and other Node.js files
    browser: true
  },
  rules: {
    'vue/multi-word-component-names': 'off' // Allow single-word component names like "Dashboard", "Login"
  }
}
