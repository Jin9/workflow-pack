import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { createElement, type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { server } from '../mocks/server';
import { generateIdempotencyKey, useIdempotentConfirm } from './useIdempotentConfirm';

const UUID_V4 =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function wrapper({ children }: { children: ReactNode }): ReactNode {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false }, queries: { retry: false } },
  });
  return createElement(QueryClientProvider, { client: queryClient }, children);
}

describe('useIdempotentConfirm', () => {
  beforeEach(() => {
    server.resetHandlers();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('generates a UUIDv4 idempotency key', () => {
    const { result } = renderHook(() => useIdempotentConfirm(), { wrapper });
    expect(result.current.idempotencyKey).toMatch(UUID_V4);
  });

  it('reuses the SAME idempotency key on retry after a network error and does not auto-resubmit', async () => {
    const seen: Array<string | null> = [];
    let shouldFail = true;
    server.use(
      http.post('/api/checkout/confirm', ({ request }) => {
        seen.push(request.headers.get('Idempotency-Key'));
        if (shouldFail) {
          // Simulate a network/transport error.
          return HttpResponse.error();
        }
        return HttpResponse.json({
          order: {
            order_no: 'SP-TEST-1',
            status: 'AWAITING_PAYMENT',
            total: { amount_minor: 1000, currency: 'THB' },
          },
        });
      }),
    );

    const { result } = renderHook(() => useIdempotentConfirm(), { wrapper });
    const keyAtStart = result.current.idempotencyKey;

    act(() => {
      result.current.submit({ cart_id: 'cart_1', address: 'addr' });
    });

    await waitFor(() => expect(result.current.error).toBeDefined());
    expect(result.current.error?.failureMode).toBe('network_error');

    // Exactly one request so far — the hook did NOT auto-resubmit.
    expect(seen).toHaveLength(1);

    // Now allow success and retry manually.
    shouldFail = false;
    act(() => {
      result.current.retry();
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // A second request only after the explicit retry().
    expect(seen).toHaveLength(2);
    // Same key on both attempts.
    expect(seen[0]).toBe(keyAtStart);
    expect(seen[1]).toBe(keyAtStart);
    expect(seen[0]).toBe(seen[1]);
  });

  it('disables a second submit while a request is in flight (no double fire)', async () => {
    let calls = 0;
    let resolveGate: () => void = () => {};
    const gate = new Promise<void>((resolve) => {
      resolveGate = resolve;
    });
    server.use(
      http.post('/api/checkout/confirm', async () => {
        calls += 1;
        await gate;
        return HttpResponse.json({
          order: {
            order_no: 'SP-TEST-2',
            status: 'AWAITING_PAYMENT',
            total: { amount_minor: 1000, currency: 'THB' },
          },
        });
      }),
    );

    const { result } = renderHook(() => useIdempotentConfirm(), { wrapper });

    act(() => {
      result.current.submit({ cart_id: 'cart_1', address: 'addr' });
    });
    await waitFor(() => expect(result.current.isSubmitting).toBe(true));

    // Second submit while in-flight must be ignored.
    act(() => {
      result.current.submit({ cart_id: 'cart_1', address: 'addr' });
    });
    expect(calls).toBe(1);

    act(() => {
      resolveGate();
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(calls).toBe(1);
  });

  it('reset() mints a NEW idempotency key and clears the prior result', async () => {
    server.use(
      http.post('/api/checkout/confirm', () =>
        HttpResponse.json({
          order: {
            order_no: 'SP-TEST-R',
            status: 'AWAITING_PAYMENT',
            total: { amount_minor: 1000, currency: 'THB' },
          },
        }),
      ),
    );

    const { result } = renderHook(() => useIdempotentConfirm(), { wrapper });
    const firstKey = result.current.idempotencyKey;

    act(() => {
      result.current.submit({ cart_id: 'cart_1', address: 'addr', coupon: 'SAVE10' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    act(() => {
      result.current.reset();
    });

    await waitFor(() => expect(result.current.idempotencyKey).not.toBe(firstKey));
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.order).toBeUndefined();
    // retry() before any submit is a safe no-op.
    act(() => {
      result.current.retry();
    });
    expect(result.current.isSubmitting).toBe(false);
  });

  it('generateIdempotencyKey always returns a UUIDv4', () => {
    for (let i = 0; i < 5; i += 1) {
      expect(generateIdempotencyKey()).toMatch(UUID_V4);
    }
  });
});
