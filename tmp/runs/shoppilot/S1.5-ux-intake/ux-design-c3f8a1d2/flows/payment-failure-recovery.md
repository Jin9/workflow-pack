---
flow_id: payment-failure-recovery
related_epics: [EPIC-CHECKOUT, EPIC-INVENTORY]
related_stories: [STORY-CHECKOUT-02, STORY-INVENTORY-01]
---

# Flow — Payment Failure / Timeout Recovery

Mock payment fails or times out → reserved stock released → retry or cancel.

```mermaid
sequenceDiagram
    actor C as Customer
    participant Pay as /checkout/payment
    participant API as Payment/Stock API
    C->>Pay: pay now
    Pay->>API: mock provider capture
    alt failure or timeout
        API-->>Pay: payment-failed / payment-timeout
        API->>API: release reserved stock back to available (STORY-INVENTORY-01)
        Pay-->>C: error + Try again / Cancel
    end
    C->>Pay: retry
    Pay->>API: capture again (new attempt)
    API-->>Pay: success → order PAID
    Note over Pay,API: duplicate provider callback applies once (STORY-CHECKOUT-02)
```

## Screen-by-screen
1. **`/checkout/payment` (error)** — `error.payment-declined` or `error.payment-timeout`; `common.action.retry` + `common.action.cancel`.
2. **Retry** — re-attempts capture; on success → `/orders/:orderNo` (PAID).
3. **Cancel / abandon** — reservation already released; order ends payment-failed/timeout; stock available again.

## Edge cases
- TTL (30m) elapses with no payment → reservation auto-releases (STORY-INVENTORY-01).
- Duplicate/late provider callback after retry → applied once; no double settle, no double stock decrement.
- Network drop mid-capture → `error.network`; safe to retry (idempotent on provider event id).

## Cross-references
- Screens: `../screens/EPIC-CHECKOUT/stories/STORY-2-mock-payment-capture-provider-replay-safety.md`
- Happy path: `customer-checkout.md`
- States: `../screen-states.md` (`/checkout/payment`)
