import type {
  ApiErrorBody,
  CheckoutCaptureRequest,
  CheckoutCaptureResponse,
  CheckoutConfirmRequest,
  CheckoutConfirmResponse,
  CheckoutQuote,
  FailureMode,
  LoginRequest,
  LoginResponse,
  OrderDetail,
  OrderListResponse,
  RefreshResponse,
} from './types.gen';

/**
 * Typed error carrying the contract `failure_mode`. The body of the app maps
 * `error.failureMode` -> a microcopy key; it never inspects HTTP status codes.
 */
export class ApiError extends Error {
  readonly failureMode: FailureMode;
  readonly status: number;

  constructor(failureMode: FailureMode, message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.failureMode = failureMode;
    this.status = status;
  }
}

const JSON_HEADERS: Readonly<Record<string, string>> = {
  'Content-Type': 'application/json',
  Accept: 'application/json',
};

/**
 * Resolve an app-relative API path to an absolute URL. The browser fetch accepts
 * relative URLs, but Node's global fetch (undici, used by vitest) requires an
 * absolute URL — so we anchor against the document origin when present.
 */
function toUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  const origin =
    typeof globalThis.location !== 'undefined' && globalThis.location.origin.startsWith('http')
      ? globalThis.location.origin
      : 'http://localhost';
  return `${origin}${path.startsWith('/') ? '' : '/'}${path}`;
}

/**
 * Whether this runtime's `fetch` accepts this runtime's `AbortSignal`. In a real
 * browser they are the same native pair (true). Under jsdom + Node's undici fetch
 * they differ — undici rejects the jsdom signal — so we skip forwarding it there
 * rather than synthesizing a false network_error. Computed once at load.
 */
const FETCH_ACCEPTS_SIGNAL: boolean = (() => {
  try {
    const probe = new AbortController();
    // RequestInit validation happens synchronously in the Request constructor.
    new Request('http://localhost/__probe__', { signal: probe.signal });
    return true;
  } catch {
    return false;
  }
})();

interface RequestOptions {
  method?: 'GET' | 'POST';
  body?: unknown;
  /** Sent on money paths (checkout confirm/capture) for replay safety. */
  idempotencyKey?: string;
  signal?: AbortSignal;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === 'object' &&
    value !== null &&
    'failure_mode' in value &&
    typeof (value as { failure_mode: unknown }).failure_mode === 'string'
  );
}

/**
 * Single fetch boundary.
 *  - credentials:'include' => httpOnly-cookie session (NEVER reads web storage).
 *  - Idempotency-Key header on money paths.
 *  - Network failures throw ApiError('network_error'); contract failures throw
 *    ApiError(<failure_mode>); both are typed.
 */
async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { ...JSON_HEADERS };
  if (opts.idempotencyKey !== undefined) {
    headers['Idempotency-Key'] = opts.idempotencyKey;
  }

  let res: Response;
  try {
    const init: RequestInit = {
      method: opts.method ?? 'GET',
      headers,
      credentials: 'include',
    };
    if (opts.body !== undefined) init.body = JSON.stringify(opts.body);
    if (opts.signal !== undefined && FETCH_ACCEPTS_SIGNAL) init.signal = opts.signal;
    res = await fetch(toUrl(path), init);
  } catch {
    // Transport-level failure (offline, DNS, abort-as-network). Synthesized mode.
    throw new ApiError('network_error', 'network request failed', 0);
  }

  let payload: unknown = null;
  const text = await res.text();
  if (text.length > 0) {
    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      payload = null;
    }
  }

  if (!res.ok) {
    if (isApiErrorBody(payload)) {
      throw new ApiError(payload.failure_mode, payload.message, res.status);
    }
    throw new ApiError('network_error', `unexpected error (${res.status})`, res.status);
  }

  return payload as T;
}

/* ----------------------------- auth ----------------------------- */
export function login(body: LoginRequest, signal?: AbortSignal): Promise<LoginResponse> {
  return request<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body,
    ...(signal !== undefined ? { signal } : {}),
  });
}

export function refresh(signal?: AbortSignal): Promise<RefreshResponse> {
  return request<RefreshResponse>('/api/auth/refresh', {
    method: 'POST',
    ...(signal !== undefined ? { signal } : {}),
  });
}

/* --------------------------- checkout --------------------------- */
export function getCheckoutQuote(cartId: string, signal?: AbortSignal): Promise<CheckoutQuote> {
  return request<CheckoutQuote>(`/api/checkout/quote?cart_id=${encodeURIComponent(cartId)}`, {
    ...(signal !== undefined ? { signal } : {}),
  });
}

/** Money path — carries the client idempotency key; replay returns the same order. */
export function confirmCheckout(
  body: CheckoutConfirmRequest,
  signal?: AbortSignal,
): Promise<CheckoutConfirmResponse> {
  return request<CheckoutConfirmResponse>('/api/checkout/confirm', {
    method: 'POST',
    body,
    idempotencyKey: body.idempotency_key,
    ...(signal !== undefined ? { signal } : {}),
  });
}

/** Money path — provider capture; provider-replay-safe. */
export function captureCheckout(
  body: CheckoutCaptureRequest,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<CheckoutCaptureResponse> {
  return request<CheckoutCaptureResponse>('/api/checkout/capture', {
    method: 'POST',
    body,
    idempotencyKey,
    ...(signal !== undefined ? { signal } : {}),
  });
}

/* ---------------------------- orders ---------------------------- */
export function listOrders(signal?: AbortSignal): Promise<OrderListResponse> {
  return request<OrderListResponse>('/api/orders', {
    ...(signal !== undefined ? { signal } : {}),
  });
}

export function getOrder(orderNo: string, signal?: AbortSignal): Promise<OrderDetail> {
  return request<OrderDetail>(`/api/orders/${encodeURIComponent(orderNo)}`, {
    ...(signal !== undefined ? { signal } : {}),
  });
}
