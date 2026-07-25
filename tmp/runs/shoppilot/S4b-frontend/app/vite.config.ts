import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// ShopPilot S4b frontend — offline SPA. No external network at build or runtime.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  build: {
    target: 'es2022',
    sourcemap: false,
  },
});
