import '@testing-library/jest-dom/vitest';
import { afterAll, afterEach, beforeAll, expect } from 'vitest';
import { cleanup } from '@testing-library/react';
import { toHaveNoViolations } from 'jest-axe';
import { server } from '../mocks/server';

// Register the jest-axe matcher (toHaveNoViolations) on vitest's expect.
// `toHaveNoViolations` is already a { toHaveNoViolations } matcher map.
expect.extend(toHaveNoViolations);

// Wire the MSW node server for the whole test run.
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  // Unmount React trees between tests so the jsdom body never accumulates
  // (RTL auto-cleanup is not guaranteed under every vitest pool config).
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());
