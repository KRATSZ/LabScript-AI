/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string
  readonly VITE_EMBED_PARENT_ORIGINS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
