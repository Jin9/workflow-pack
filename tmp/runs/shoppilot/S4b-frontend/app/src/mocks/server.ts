import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/* Node request-interception server for vitest (wired in test/setup.ts). */
export const server = setupServer(...handlers);
