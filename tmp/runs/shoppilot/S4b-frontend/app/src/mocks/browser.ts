import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

/* DEV-only service worker (started in main.tsx behind import.meta.env.DEV). */
export const worker = setupWorker(...handlers);
