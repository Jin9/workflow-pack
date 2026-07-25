# Infra Topology — ShopPilot

```
                         ┌──────────────┐
            ┌───────────▶│   web (SSR)  │ Next.js / React+TS
            │            └──────┬───────┘
            │      sync HTTP    │  (auth.login/refresh, checkout.confirm/capture,
            │                   │   order.get/transition, inventory.adjust)
   ┌────────┴────┐  ┌──────────┼───────────┬───────────────┐
   ▼             ▼  ▼          ▼            ▼               ▼
┌──────┐   ┌──────────┐  ┌──────────┐  ┌────────┐    (admin)
│ auth │   │inventory │◀─│ checkout │─▶│ order  │     calls
│ svc  │   │  svc     │  │  svc     │  │  svc   │
└──┬───┘   └────┬─────┘  └────┬─────┘  └───┬────┘
   │redis       │mysql        │mysql       │mysql        ┌──────────┐
   │mysql       │             │  ─sync─▶ mock-psp        │  Kafka   │
   └────────────┴─────────────┴────────────┴───outbox───▶│ (audit_id│
                                              ◀──consume──│  keyed)  │
                                                          └──────────┘
   order svc ─sync─▶ mock-courier (tracking)
```

- `checkout-service` is the only synchronous orchestrator of the reserve→create path (sync calls to `inventory.reserve` + `order.create`); all cross-service state propagation otherwise is async via the outbox→Kafka (ADR-008).
- One ASCII block, one screen (house rule).
