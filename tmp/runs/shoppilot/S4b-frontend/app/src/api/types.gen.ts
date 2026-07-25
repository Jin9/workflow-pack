/*
 * GENERATED-EQUIVALENT — hand-authored from S3 markdown contracts
 * (tmp/runs/shoppilot/S3-contracts/be/{auth,checkout,inventory,order}.contract.md);
 * no OpenAPI spec exists in this run; regenerate via openapi-typescript when
 * befe-contract-design emits *.openapi.yaml.
 *
 * This is the single typed API boundary: request/response types + the OrderStatus
 * union + a discriminated ApiError whose failure_mode literal union covers EVERY
 * failure mode enumerated across be/*.contract.md.
 */

/* ------------------------------------------------------------------ *
 * Money. Server-computed only — money.ts never derives totals.
 * ------------------------------------------------------------------ */
export type CurrencyCode = 'THB';

export interface Money {
  /** Integer minor units (satang for THB). Never a float. */
  amount_minor: number;
  currency: CurrencyCode;
}

/* ------------------------------------------------------------------ *
 * Order status — single source of truth for the union (order.contract.md
 * transitions + microcopy order.status.* keys).
 * ------------------------------------------------------------------ */
export type OrderStatus =
  | 'AWAITING_PAYMENT'
  | 'PAID'
  | 'PAYMENT_FAILED'
  | 'PAYMENT_TIMEOUT'
  | 'PACKING'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED';

export const ORDER_STATUS_VALUES: readonly OrderStatus[] = [
  'AWAITING_PAYMENT',
  'PAID',
  'PAYMENT_FAILED',
  'PAYMENT_TIMEOUT',
  'PACKING',
  'SHIPPED',
  'DELIVERED',
  'CANCELLED',
] as const;

/* ------------------------------------------------------------------ *
 * Failure modes — UNION of every failure mode in be/*.contract.md.
 *   auth:      invalid_credentials_generic, rate_limited, expired_token,
 *              replayed_token_family_revoked, invalid_token
 *   checkout:  coupon_expired, out_of_stock, validation_error, auth_required,
 *              payment_declined, payment_timeout, amount_mismatch_rejected
 *   inventory: insufficient_stock, sku_not_found, reservation_not_found,
 *              below_reserved_rejected, missing_reason
 *   order:     invalid_payload, not_owner_denied, not_found,
 *              illegal_backward_rejected, missing_tracking_on_shipped,
 *              not_admin, consumer_lag, dlq_on_poison_message
 *   transport: network_error (client-synthesized; not a server mode)
 * ------------------------------------------------------------------ */
export type FailureMode =
  // auth
  | 'invalid_credentials_generic'
  | 'rate_limited'
  | 'expired_token'
  | 'replayed_token_family_revoked'
  | 'invalid_token'
  // checkout
  | 'coupon_expired'
  | 'out_of_stock'
  | 'validation_error'
  | 'auth_required'
  | 'payment_declined'
  | 'payment_timeout'
  | 'amount_mismatch_rejected'
  // inventory
  | 'insufficient_stock'
  | 'sku_not_found'
  | 'reservation_not_found'
  | 'below_reserved_rejected'
  | 'missing_reason'
  // order
  | 'invalid_payload'
  | 'not_owner_denied'
  | 'not_found'
  | 'illegal_backward_rejected'
  | 'missing_tracking_on_shipped'
  | 'not_admin'
  | 'consumer_lag'
  | 'dlq_on_poison_message'
  // client transport
  | 'network_error';

/** Discriminated API error envelope (the `failure_mode` is the discriminant). */
export interface ApiErrorBody {
  failure_mode: FailureMode;
  message: string;
}

/* ------------------------------------------------------------------ *
 * auth context
 * ------------------------------------------------------------------ */
export interface LoginRequest {
  email: string;
  password: string;
}

export interface SessionUser {
  /** Opaque server id; never the raw email/phone. */
  user_id: string;
  display_name: string;
  /** Masked at the boundary; the raw value is never sent to the client. */
  email_masked: string;
}

export interface LoginResponse {
  user: SessionUser;
}

export interface RefreshResponse {
  user: SessionUser;
}

/* ------------------------------------------------------------------ *
 * checkout context
 * ------------------------------------------------------------------ */
export interface CheckoutConfirmRequest {
  cart_id: string;
  address: string;
  /** Optional coupon; re-validated server-side at confirm. */
  coupon?: string;
  idempotency_key: string;
}

export interface ConfirmedOrder {
  order_no: string;
  status: OrderStatus;
  total: Money;
}

export interface CheckoutConfirmResponse {
  order: ConfirmedOrder;
}

export interface CheckoutCaptureRequest {
  order_id: string;
  provider_event_id: string;
}

export interface CheckoutCaptureResponse {
  order_no: string;
  status: OrderStatus;
}

/* ------------------------------------------------------------------ *
 * server-computed checkout quote (totals the FE renders read-only)
 * ------------------------------------------------------------------ */
export interface CheckoutQuote {
  cart_id: string;
  subtotal: Money;
  discount: Money;
  shipping: Money;
  total: Money;
}

/* ------------------------------------------------------------------ *
 * order context
 * ------------------------------------------------------------------ */
export interface OrderTimelineEntry {
  status: OrderStatus;
  /** ISO-8601 timestamp. */
  at: string;
}

export interface OrderSummaryItem {
  order_no: string;
  status: OrderStatus;
  total: Money;
  placed_at: string;
}

export interface OrderDetail {
  order_no: string;
  status: OrderStatus;
  total: Money;
  placed_at: string;
  /** PII — audit-on-view; never logged. */
  shipping_address: string;
  /** PII — masked for display. */
  customer_email: string;
  /** PII — masked for display. */
  customer_phone: string;
  tracking_no?: string;
  timeline: OrderTimelineEntry[];
}

export interface OrderListResponse {
  orders: OrderSummaryItem[];
}
