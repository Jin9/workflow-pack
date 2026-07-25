# Observability Spec Template

**Parent:** [`../templates.md`](../templates.md)
**Owner role:** [Tech-Lead](../roles.md) · **`template_version`:** 0.1.0

The observability contract every service must satisfy. Authored by Tech-Lead alongside the architecture; validated by Reviewer-L1 (per service) and Reviewer-L2 (cross-component).

**File location:** `<workflow_root>/design/architecture/observability-spec.md`

Local-stack docker-compose snippet shipped at `<workflow_root>/observability/docker-compose.yml` referenced from this spec.

---

## Required sections

1. `## Structured logging` — required field set + redaction list
2. `## Metrics` — Prometheus exposition; standard + per-domain metrics
3. `## Distributed tracing` — OTLP exporter + W3C trace propagation
4. `## Audit log` — taxonomy for compliance-sensitive actions
5. `## Dashboards` — list with intent + key panels
6. `## Alert rules` — Prometheus rule format
7. `## Local stack` — docker-compose snippet pointer (Loki + Tempo + Grafana + Prometheus)
8. `## Per-service obligations` — checklist

---

## File shape

```markdown
# Observability — <Workflow Name>

## Structured logging

All services use `slog` (Go `log/slog`) with JSON handler. Every log event MUST include:

| Field | Source | Example |
|---|---|---|
| `time` | slog default | `2026-05-07T17:48:01.234Z` (RFC 3339) |
| `level` | slog default | `INFO` / `WARN` / `ERROR` |
| `msg` | call site | `"login_attempted"` (kebab-case verb) |
| `service` | env var `SERVICE_NAME` | `identity` |
| `version` | build-time `-ldflags -X` | git short SHA |
| `requestId` | `common/middleware.RequestIDMiddleware` | UUID v7 |
| `userId` | from JWT claims if present | empty for unauthenticated |
| `path` | request path | `/api/v1/identity/auth/login` |
| `method` | HTTP method | `POST` |
| `status` | response status code | `200` / `401` / `500` |
| `latencyMs` | wall-clock from middleware entry to write | float |
| `traceId` | from W3C `traceparent` | hex 32 |
| `spanId` | from W3C `traceparent` | hex 16 |

**Redaction list** (NEVER logged): passwords, password hashes, raw refresh / access JWTs, JWT signing keys, dedup keys (paymentcallback), secrets (HMAC keys, INTERNAL_SHARED_SECRET), customer payment card data (n/a for MVP mock), full request bodies on auth + payment endpoints (log only field names, never values).

Per `common/serror`, errors wrap with source location; the wrap chain is logged via `slog.Error(msg, "err", err)` — slog renders the chain in the `err` field.

## Metrics

Each service exposes `/metrics` on its main port (or a sidecar port `:9090` per K8s convention). Prometheus scrapes every 15s.

Standard metrics (every service):

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | counter | `service, path, method, status` |
| `http_request_duration_seconds` | histogram (le buckets: 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10) | `service, path, method, status` |
| `http_in_flight` | gauge | `service` |
| `db_query_duration_seconds` | histogram | `service, query_kind` |
| `db_connections_in_use` | gauge | `service, pool` |
| `kafka_messages_published_total` | counter | `service, topic, status` |
| `kafka_messages_consumed_total` | counter | `service, topic, status` |
| `outbox_pending_count` | gauge | `service` |

Per-domain metrics (examples; each TD specifies the set):

- `inventory_reservations_total{outcome=created|expired|committed|released}` (counter)
- `inventory_reservation_sweep_batch_size` (histogram)
- `payment_callback_dedup_hits_total{kind=replay|terminal}` (counter)
- `checkout_orchestration_step_duration_seconds{step}` (histogram)
- `order_state_transitions_total{from_status,to_status}` (counter)

## Distributed tracing

- **Propagation:** W3C `traceparent` header on every HTTP request and Kafka message header.
- **Exporter:** OpenTelemetry SDK with OTLP gRPC exporter to Tempo (default endpoint `tempo:4317`).
- **Span boundaries:** every public HTTP handler creates a server span; every downstream HTTP call and Kafka publish is a child span. Database queries are spans only when query duration > 50ms (sampling).
- **Sampling:** parent-based, with 10% probabilistic sampling for traces that originate in the frontend; 100% sampling for traces that originate in error paths.
- **Baggage:** never propagate user PII via baggage.

## Audit log

Audit Service is deferred for the MVP run. When re-enabled, every admin-initiated mutation emits an audit event with this taxonomy:

| Field | Required | Example |
|---|---|---|
| `event_id` | Yes | UUID v7 |
| `actor_user_id` | Yes | claims.sub of admin |
| `actor_role` | Yes | `ADMIN` |
| `action` | Yes (enum) | `CREATE_PRODUCT` / `UPDATE_STOCK` / `CHANGE_ORDER_STATUS` / `SOFT_DELETE_PRODUCT` / `CANCEL_ORDER` |
| `entity_type` | Yes | `product` / `order` / `stock` |
| `entity_id` | Yes | UUID |
| `before_summary` | Optional | redacted snapshot |
| `after_summary` | Optional | redacted snapshot |
| `correlation_id` | Yes | requestId of the originating request |
| `occurred_at` | Yes | RFC 3339 UTC |

Sensitive fields (passwords, payment data) MUST be redacted in `before_summary` / `after_summary`.

## Dashboards

| Dashboard | Intent | Key panels |
|---|---|---|
| Service Health | per-service overview | request rate, error rate, p95 latency, in-flight, db connections |
| Customer Journey | spine end-to-end | browse→cart→checkout→payment funnel; conversion %; per-step error rate |
| Saga Compensation | catch stuck flows | reservations RESERVED > 5min count; orders PENDING_PAYMENT > 15min count; outbox_pending_count |
| Auth Anomaly | spot abuse | login failures per IP/min; refresh-token rotation rate; AUTH_REVOKED rate |
| Schema Performance | query hotness | top 10 slow queries by p95; index hit ratio; lock wait events |

## Alert rules

```yaml
groups:
  - name: service-health
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) /
              sum(rate(http_requests_total[5m])) by (service) > 0.05
        for: 5m
        labels: { severity: page }
        annotations:
          summary: "{{ $labels.service }} error rate > 5% over 5min"

      - alert: P95LatencyBreach
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels: { severity: warn }

      - alert: SagaInFlightStuck
        expr: |
          inventory_reservations_total{outcome="created"} -
          (inventory_reservations_total{outcome="expired"} +
           inventory_reservations_total{outcome="committed"} +
           inventory_reservations_total{outcome="released"}) > 0
          and time() - timestamp(<...>) > 900   # 15 min
        for: 5m
        labels: { severity: page }

      - alert: OutboxBacklog
        expr: outbox_pending_count > 1000
        for: 10m
        labels: { severity: warn }
```

## Local stack

Reference: `<workflow_root>/observability/docker-compose.yml`. Services:

- `loki` (3100) — log aggregation; `promtail` sidecar tails stdout from each service container.
- `tempo` (3200, 4317 OTLP) — trace storage.
- `prometheus` (9090) — metrics scrape; reads `prometheus.yml` listing all backend service `/metrics` endpoints.
- `grafana` (3000) — dashboards; auto-provisioned from `dashboards/`.

Run: `docker-compose -f observability/docker-compose.yml up -d`.

## Per-service obligations

Each service's Dev output MUST satisfy:

- [ ] `slog` JSON handler wired in `main.go` with required field set.
- [ ] `common/middleware.RequestIDMiddleware` registered (sets `requestId` UUID v7 in context).
- [ ] `common/middleware.AccessLogMiddleware` registered (logs the per-request envelope).
- [ ] `/metrics` endpoint exposed via `promhttp.Handler()` or equivalent.
- [ ] OTLP exporter initialized in `main.go`; spans created via `otelgin` middleware.
- [ ] Per-domain counters declared in `app/<domain>/metrics.go`.
- [ ] Redaction list enforced in `common/logger`'s replacer (or per-handler when fields are first received).
```

---

## Negative examples

### Negative #1 — Logging passwords in error path

```go
slog.Error("login failed", "email", email, "password", pw, "err", err)
```

What Reviewer-L1 catches:

1. `password` field present in log → `code_security_issue` (high) → Dev. Redaction list violation.
2. Even logging `email` is borderline (PII); contextually allowed for auth-failure-investigation, but should respect a redaction toggle for production.

### Negative #2 — `/metrics` endpoint requires auth

```go
router.POST("/metrics", middleware.JWT, promhttp.Handler())
```

What's wrong:

1. `/metrics` MUST be unauthenticated (or behind a network ACL); Prometheus does not have JWT credentials. Tag: `code_quality_issue` (medium).
2. Method should be GET.
