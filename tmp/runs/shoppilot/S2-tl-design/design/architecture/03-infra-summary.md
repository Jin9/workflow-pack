# Infra Summary — ShopPilot

- **Compute:** 5 containerized services (web, auth, inventory, checkout, order) on a managed container platform; one deployable per repo (ADR-001).
- **Data:** per-service MySQL (RDS) — `auth`, `inventory`, `checkout`, `order` DBs, no shared schema. Redis for sessions, rate-limit counters, hot reads.
- **Eventing:** Kafka; topics keyed by `audit_id`; idempotent consumers; transactional outbox per producing service (ADR-008).
- **External (mock for MVP):** mock PSP (tokenizes; PCI boundary at checkout-service only), mock courier (tracking).
- **Regions/residency:** ap-southeast (TH/SG) only — PDPA residency (S1 §16).
- **Secrets/config:** platform secret store; no tokens/PII/PAN in env or logs.
- **CI/CD:** Docker + GitLab CI per repo; branch `develop`.
