'use strict'

module.exports = {
  env: {
    production: {
      plugins: ['babel-plugin-styled-components', 'babel-plugin-unassert'],
    },
    development: {
      plugins: ['babel-plugin-styled-components'],
    },
    test: {
      plugins: [
        ['babel-plugin-styled-components', { ssr: false, displayName: false }],
      ],
    },
  },
}
