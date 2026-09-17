import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, searchForWorkspaceRoot } from "vite";
import react from "@vitejs/plugin-react";

const webRoot = path.dirname(fileURLToPath(import.meta.url));
const demoRoot = path.resolve(webRoot, "..");
const cloudRoot = path.resolve(demoRoot, "../../../LabscriptAI_cloud");
const defaultSlim = path.join(cloudRoot, "web/opentrons-protocol-visualizer-web-slim");
const hangRoot = process.env.LABSCRIPTAI_VISUALIZER_ROOT
  ? path.resolve(process.env.LABSCRIPTAI_VISUALIZER_ROOT)
  : defaultSlim;
const slimRoot = existsSync(hangRoot) ? hangRoot : "";
const stubRoot = path.join(webRoot, "src", "stubs");
const nm = path.join(demoRoot, "node_modules");
const fromNm = (pkg: string): string => path.join(nm, pkg);

function cloudOrStub(cloudFile: string, stubName: string): string {
  return cloudFile && existsSync(cloudFile) ? cloudFile : path.join(stubRoot, stubName);
}

export default defineConfig({
  root: webRoot,
  plugins: [react()],
  optimizeDeps: {
    exclude: ["lucide-react"],
    include: [
      "@opentrons/protocol-visualization",
      "@opentrons/components",
      "@opentrons/shared-data",
      "@opentrons/step-generation",
    ],
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
      allow: [
        searchForWorkspaceRoot(webRoot),
        ...(existsSync(cloudRoot) ? [cloudRoot] : []),
        ...(slimRoot ? [slimRoot] : []),
      ],
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
      // Official OT replay comes from npm `@opentrons/protocol-visualization`.
      // Do not alias `@opentrons/*` to the ~305MB slim tree.
      // Optional hang: LABSCRIPTAI_VISUALIZER_ROOT or a local LabscriptAI_cloud slim checkout.
      "@visualizer/normalize-analysis": cloudOrStub(
        slimRoot
          ? path.join(slimRoot, "protocol-visualizer-web/client/src/normalizeAnalysisOutput.ts")
          : "",
        "normalize-analysis.ts"
      ),
      "@visualizer/animator": cloudOrStub(
        existsSync(path.join(cloudRoot, "labscriptAI-frontend/src/components/ProtocolOperationAnimator.tsx"))
          ? path.join(cloudRoot, "labscriptAI-frontend/src/components/ProtocolOperationAnimator.tsx")
          : "",
        "animator.tsx"
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
