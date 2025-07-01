import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      "^/api/.*": {
        target: process.env.VITE_API_URL,
        changeOrigin: true,
        secure: false,
        ws: true,
      },
      "^/ws/.*": {
        target: process.env.VITE_WS_URL,
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "assets",
    sourcemap: true,
  },
});
