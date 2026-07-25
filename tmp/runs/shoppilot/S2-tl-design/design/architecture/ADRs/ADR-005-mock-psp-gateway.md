# ADR-005 — Mock PSP behind a gateway interface

**Status:** Accepted

**Context:** MVP uses a mock payment provider but must swap in a real PSP later without re-architecting; PCI scope must stay out (STORY-CHECKOUT-02).

**Decision:** Payment access sits behind a `client_psp.go` gateway interface in checkout-service only. No PAN/CVV collected or stored; the PSP tokenizes. Capture dedupes on provider event id.

**Consequences:** PCI boundary confined to one service; real-PSP swap is a one-adapter change; mock outcomes (success/failure/timeout) are deterministic for tests.
