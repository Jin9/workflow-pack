import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// HELL FACTORY is a React app rendered into a fixed 1800×1013 stage that is
// scaled to fit the viewport (see index.html). Nothing exotic — the default
// React plugin (classic + automatic runtime) is all we need.
export default defineConfig({
  plugins: [react()],
  // /api proxies to the local pipeline engine (python3 -m engine serve);
  // in prod FastAPI serves dist/ itself, so everything is one origin.
  server: { open: true, proxy: { '/api': 'http://127.0.0.1:8000' } },
});
