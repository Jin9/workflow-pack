# Observability Spec — ShopPilot

## Logging
- `log/slog` structured JSON only; **never** log tokens, PAN/CVV, or PII (redact `<PII:REDACTED:CLASS=…>`).
- Every log line carries `audit_id` (the per-run correlation key, same as the Kafka partition key).

## Audit trail (banking-grade, append-only)
- Every state-change writes `{event, actor, ts, before, after, outcome, audit_id}` to the service's append-only audit table AND publishes to the audit topic.
- Immutable; 5-year retention for order/financial (Revenue Code), 1-year for auth/stock.

## Metrics (per service)
- RED (rate/errors/duration) on every sync endpoint.
- Domain SLO metrics: checkout-confirm p95, payment-capture success rate, **stock-mismatch count (target 0)**, **double-charge count (target 0)**, reservation-TTL-release count.

## Tracing
- Distributed trace across web→checkout→inventory/order, trace id == `audit_id` where possible.

## Alerts
- Any `stock < 0` (must never happen) → page.
- Outbox lag > threshold, DLQ depth > 0 → page (event-delivery health, ADR-008).
- Payment capture failure-rate spike → notify.

## SLOs (from S1 success signals)
- Order-confirm p95 latency, order-listing latency — targets `TBD-confirm-with-PM` (S1 §3 named the signals but not numeric thresholds).
