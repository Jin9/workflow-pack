import { http, HttpResponse } from 'msw';
import type { ApiErrorBody, FailureMode } from '../api/types.gen';
import {
  DEMO_ORDER_DETAIL,
  DEMO_ORDER_NO,
  DEMO_ORDERS,
  DEMO_QUOTE,
  DEMO_USER,
} from './fixtures';

/*
 * MSW handlers — the API the manifest screens call. Deterministic fixtures.
 * Same handlers serve dev (browser worker) and vitest (node server). Tests
 * override individual handlers with server.use(...) for failure paths.
 */
function fail(failure_mode: FailureMode, message: string, status: number): Response {
  return HttpResponse.json<ApiErrorBody>({ failure_mode, message }, { status });
}

export const handlers = [
  // auth.login
  http.post('/api/auth/login', async ({ request }) => {
    const body = (await request.json()) as { email?: string; password?: string };
    if (body.password === 'wrong') {
      return fail('invalid_credentials_generic', 'invalid credentials', 401);
    }
    return HttpResponse.json({ user: DEMO_USER });
  }),

  // auth.refresh — no session by default (unauthenticated demo)
  http.post('/api/auth/refresh', () => {
    return fail('expired_token', 'no active session', 401);
  }),

  // checkout quote (server-computed totals)
  http.get('/api/checkout/quote', () => {
    return HttpResponse.json(DEMO_QUOTE);
  }),

  // checkout.confirm (money path) — echoes Idempotency-Key acceptance
  http.post('/api/checkout/confirm', async ({ request }) => {
    const key = request.headers.get('Idempotency-Key');
    if (key === null || key.length === 0) {
      return fail('validation_error', 'missing idempotency key', 400);
    }
    return HttpResponse.json({
      order: {
        order_no: DEMO_ORDER_NO,
        status: 'AWAITING_PAYMENT',
        total: DEMO_QUOTE.total,
      },
    });
  }),

  // checkout.capture (money path)
  http.post('/api/checkout/capture', async ({ request }) => {
    const body = (await request.json()) as { order_id?: string };
    return HttpResponse.json({
      order_no: body.order_id ?? DEMO_ORDER_NO,
      status: 'PAID',
    });
  }),

  // orders list
  http.get('/api/orders', () => {
    return HttpResponse.json({ orders: DEMO_ORDERS });
  }),

  // order detail
  http.get('/api/orders/:orderNo', ({ params }) => {
    const orderNo = params['orderNo'];
    if (orderNo !== DEMO_ORDER_NO) {
      return fail('not_found', 'order not found', 404);
    }
    return HttpResponse.json(DEMO_ORDER_DETAIL);
  }),
];
