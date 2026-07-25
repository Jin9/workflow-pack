/*
 * pii.ts — PII field-level treatment (security_review.pii_fields_handled).
 *   customer_email -> mask
 *   customer_phone -> mask
 *   shipping_address -> audit-on-view (record an access event; never logged raw)
 *
 * Nothing here ever console.logs a raw PII value.
 */

/** Mask an email: keep first char + domain, star the rest of the local part. */
export function maskEmail(email: string): string {
  const at = email.indexOf('@');
  if (at <= 0) return '•••';
  const local = email.slice(0, at);
  const domain = email.slice(at + 1);
  const head = local.slice(0, 1);
  const masked = head + '•'.repeat(Math.max(local.length - 1, 1));
  return `${masked}@${domain}`;
}

/** Mask a phone: reveal only the last 4 digits. */
export function maskPhone(phone: string): string {
  const digits = phone.replace(/\D/g, '');
  if (digits.length <= 4) return '•'.repeat(digits.length);
  const tail = digits.slice(-4);
  return `${'•'.repeat(digits.length - 4)}${tail}`;
}

export interface PiiAuditEvent {
  field: 'shipping_address';
  order_no: string;
  /** Stable, monotonic-ish marker; deterministic in tests via injected clock. */
  at: number;
}

type AuditSink = (event: PiiAuditEvent) => void;

let sink: AuditSink = () => {
  /* default no-op; an audit transport is wired by the host app. */
};

/** Wire (or in tests, capture) the audit sink. */
export function setPiiAuditSink(next: AuditSink): void {
  sink = next;
}

/**
 * Record that a sensitive field (shipping address) was viewed. Emits an audit
 * event; returns the value UNCHANGED for display. The raw value is never logged.
 */
export function auditOnView(orderNo: string, address: string, now: number = Date.now()): string {
  sink({ field: 'shipping_address', order_no: orderNo, at: now });
  return address;
}
