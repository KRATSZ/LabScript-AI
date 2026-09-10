import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, searchForWorkspaceRoot } from "vite";
import react from "@vitejs/plugin-react";

const webRoot = path.dirname(fileURLToPath(import.meta.url));
const demoRoot = path.resolve(webRoot, "..");
const cloudRoot = path.resolve(demoRoot, "../../../LabscriptAI_cloud");
const slimRoot = path.join(cloudRoot, "web/opentrons-protocol-visualizer-web-slim");
const nm = path.join(demoRoot, "node_modules");
const fromNm = (pkg: string): string => path.join(nm, pkg);

export default defineConfig({
  root: webRoot,
  plugins: [react()],
  optimizeDeps: {
    exclude: ["lucide-react"],
  },
  define: {
    global: "globalThis",
    _NODE_ENV_: JSON.stringify(process.env.NODE_ENV),
    process: { env: { NODE_ENV: JSON.stringify(process.env.NODE_ENV) } },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    fs: {
      allow: [searchForWorkspaceRoot(webRoot), cloudRoot],
    },
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8787",
        changeOrigin: false,
      },
    },
  },
  resolve: {
    dedupe: ["react", "react-dom"],
    alias: {
      "@opentrons/components/styles/global": path.join(
        slimRoot,
        "components/src/styles/global.css"
      ),
      "@opentrons/components": path.join(slimRoot, "components/src/index.ts"),
      "@opentrons/shared-data": path.join(slimRoot, "shared-data/js/index.ts"),
      "@opentrons/step-generation": path.join(slimRoot, "step-generation/src/index.ts"),
      "@visualizer/normalize-analysis": path.join(
        slimRoot,
        "protocol-visualizer-web/client/src/normalizeAnalysisOutput.ts"
      ),
      "@visualizer/animator": path.join(
        cloudRoot,
        "labscriptAI-frontend/src/components/ProtocolOperationAnimator.tsx"
      ),
      "@popperjs/core": fromNm("@popperjs/core"),
      "@react-spring/types": fromNm("@react-spring/types"),
      "@react-spring/web": fromNm("@react-spring/web"),
      ajv: fromNm("ajv"),
      classnames: fromNm("classnames"),
      clsx: fromNm("clsx"),
      "core-js": fromNm("core-js"),
      i18next: fromNm("i18next"),
      immer: fromNm("immer"),
      interactjs: fromNm("interactjs"),
      lodash: fromNm("lodash"),
      "path-browserify": fromNm("path-browserify"),
      react: fromNm("react"),
      "react-dom": fromNm("react-dom"),
      "react-i18next": fromNm("react-i18next"),
      "react-markdown": fromNm("react-markdown"),
      "react-popper": fromNm("react-popper"),
      "react-remove-scroll": fromNm("react-remove-scroll"),
      "react-select": fromNm("react-select"),
      "react-viewport-list": fromNm("react-viewport-list"),
      redux: fromNm("redux"),
      "styled-components": fromNm("styled-components"),
      "uuid/v4": path.join(nm, "uuid/v4.js"),
      uuid: fromNm("uuid"),
    },
  },
});
