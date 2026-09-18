import type { Plugin } from 'vite'

/** Prevent CSS modules from being tree-shaken out of the bundle. */
export const cssModuleSideEffect = (): Plugin => {
  return {
    name: 'css-module-side-effectful',
    enforce: 'post',
    transform(_: string, id: string) {
      if (id.includes('.module.')) {
        return { moduleSideEffects: 'no-treeshake' }
      }
    },
  }
}
