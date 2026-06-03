# Test Data Design

> Reference for `planning-banking-tests` v1.0.0. Loaded by **SKILL.md Step 8** on every run.

## 1. Purpose

This document defines the rules for generating synthetic test data per PII field declared in the BA brief's `pii_inventory[]`. The skill emits `test_data_specs[]` entries that satisfy Invariant 4 (every PII field has at least one synthetic-data spec) and that respect the masking, retention, and residency rules carried on the BA row.

Hard floor: no real customer PII and no production-derived data ever enters a fixture (AP-Q7). Thai-jurisdiction test data must look Thai (postal codes, sub-district names, phone prefixes, name surface forms) so locale-sensitive bugs surface in test, not in production.

## 2. PII category handling

The output schema's `pii_inventory[].category` enum is `direct | indirect | regulatory | financial`. The skill maps category to a synthesis posture:

| Category | Masking rule | Residency rule | Synthesis approach |
|---|---|---|---|
| `direct` | Honour the per-field `masking` column on the BA row. Default to masked on admin views unless the BA explicitly opens it. | Generate values that look native to the BA's named jurisdiction (Thai postal, Thai mobile, Thai name surface forms). Never use jurisdiction-mixed data. | Pattern-based generator per field (§3). Deterministic given a frozen seed. |
| `indirect` | Mask on cross-customer surfaces; visible on owner-self surfaces and audited admin reads. | Same as direct. | Surrogate identifiers (UUIDs, sequence ids) from a frozen seed. |
| `regulatory` (e.g. `session_token` on the holdout) | Always masked. Value MUST NEVER appear in any visible surface, log, or fixture artifact. | n/a — opaque. | Opaque base64 from a frozen seed; reference by handle only. |
| `financial` (not on holdout, illustrative) | Always masked. PAN truncation per PCI rules where applicable. | Card-network jurisdiction-aware where named. | Test-only PAN ranges from the network's published test set. |

## 3. Per-PII-field synthesis rules (e-commerce holdout)

For each of the ten PII fields in `05-pii-inventory.md`, the skill emits a `test_data_specs[]` entry with the following synthesis rule:

- **`email` (direct)** — pattern `customer+{seq}@shoppilot.test`. The `.test` TLD is reserved (RFC 6761) so no real domain is ever contacted. No real provider name. `{seq}` is a zero-padded integer drawn from the fixture set's seed.
- **`phone` (direct)** — Thai mobile format `0812345{NNN}`. Prefix `081` is in the assigned Thai mobile range and the fixture generator restricts to a published test-safe sub-range. Never use real-customer-derived prefixes.
- **`password` (direct)** — fixture stores an **argon2id hash** of a known seed value. The plaintext is recorded only in a sealed `secrets/test-passwords.yaml` (gitignored) that the test harness reads at run time. The hash representation is what lands in fixture JSON. NEVER write the plaintext into fixture JSON, snapshots, or logs.
- **`name` (direct)** — bilingual surface forms preserved when the BA glossary carries Thai/English pairs. Use the jq examples in `references/v1.1-role-boundaries.md` (the Role 4 — Test Data slice) to source pairs from `04-glossary.md`. When no glossary pair exists, generate a synthetic Thai given-name + family-name plus a romanised transliteration.
- **`shipping_address` (direct)** — Thai postal format with **real sub-district / district / province / postcode tuples** (sourced from the published Thai postal authority list) and **fake house numbers and street lines**. This produces addresses that route correctly through validation but resolve to no real residence.
- **`customer_id` (indirect)** — UUID v4 drawn from a frozen seed. Same seed ⟹ same UUID stream, supporting cross-run determinism.
- **`order_number` (indirect)** — pattern `ORD-{epoch_seed}-{seq:06d}`. `{epoch_seed}` is the fixture set's frozen time anchor expressed as `YYYYMMDD`. `{seq:06d}` is a six-digit zero-padded counter. Mirrors the BA-declared format `ORD-YYYYMMDD-NNNNNN` (4.9) while removing real-time-of-run dependency.
- **`tracking_number` (indirect)** — pattern `TRK-{seq:08d}`. Carrier-agnostic synthetic identifier; never use a real carrier's tracking format that could collide with their namespace.
- **`review_text` (indirect)** — corpus of safe Thai + English strings curated for the fixture. Pulls from a vetted phrasebook; no real customer quotes; no copyrighted text. Include locale-sensitive variants for assertion of bilingual rendering.
- **`session_token` (regulatory)** — opaque base64 string from frozen seed. Recorded as a **handle** in the fixture (e.g. `{token_ref: "fixture://session/customer-001"}`) and resolved at run time by the harness. The value never appears in fixture JSON, never in logs, never in test output.

## 4. Fixture-set definitions

The skill emits the following named fixture sets in `test_data_specs[].fixture_set_id`:

- **`customer-fixture-set`** — N customer records (default N=10), each carrying `email`, `password`, `phone`, `name`, `shipping_address`, `customer_id`. Includes role variants: standard customer, dormant customer, customer-with-multiple-addresses.
- **`admin-fixture-set`** — M admin records (default M=3), each with elevated authz claims used in admin-view tests. No customer PII; admins are themselves synthetic identities.
- **`order-fixture-set`** — Order records spanning every state in the BA order state machine (cart, submitted, paid, shipped, delivered, cancelled, refunded). Each carries `order_number`, `tracking_number` where applicable, and an immutable snapshot of `shipping_address` per BA section 6.8.
- **`coupon-fixture-set`** — Coupon records spanning every state (active, expired, exhausted, customer-restricted). Used by the CART-CHECKOUT epic test cases.
- **`merchant-fixture-set`** — Merchant identity records used by CPA-TH-DISCLOSURE compliance tests. Includes legal name, registered address, contact channel — all synthetic, all Thai-locale-shaped.

Every fixture set declares its `fixture_set_version` (semver) and its `seed` (frozen integer).

## 5. Time-anchored seeds

Every fixture set declares time anchors per scenario to support deterministic state-machine tests:

- **`T0`** — scenario start. Absolute timestamp (e.g. `2026-01-15T09:00:00+07:00`, ICT). The skill never reads the system clock; the anchor is a fixture constant.
- **`T+10min`, `T+1h`, `T+1d`, `T+30d`, `T+90d`, `T+5y`** — derived offsets used by retention tests (PDPA, CCA-TH-LOG-90D, TRC-VAT-7PCT) and by SLA tests (refund window, DSAR response).

Anchors are declared on `test_data_specs[i].time_anchors[]` and referenced by `test_cases[j].time_anchor_ref`. The harness freezes the system clock at the named anchor when executing the test.

## 6. Edge-case data sets

Per BA-declared constraint, the skill emits boundary, race, and empty/null variants:

- **Boundary** — max-length and min-length values for every string field that the BA constrains (e.g. review_text upper bound, name max length). Pulled from BA `acceptance_criteria` or from `processing_metadata.hidden_requirements_sweep` Frame 5 (Boundary) findings.
- **Race** — concurrent-state fixtures: two customers checking out the last unit of a coupon, two admins editing the same order. Time anchors collapsed to identical `T0`.
- **Empty / null variants** — empty review, no second address, no phone (where the BA permits absence). Where the BA forbids absence (e.g. email at signup), emit a negative-case fixture that asserts rejection.

## 7. Bilingual handling

The BA glossary (`04-glossary.md`) carries Thai/English surface-form pairs for product names, address components, error message copy, and status labels. The skill preserves these pairs in fixtures:

- Product names render in both locales where the glossary provides a pair.
- Error messages cover both locales when the BA story shows a customer-facing error surface.
- Address components use the Thai sub-district name with romanised transliteration alongside, supporting both `th-TH` and `en-TH` rendering tests.
- Where a glossary pair is missing, the skill emits a `coverage_gap` of severity P2 with `gap_type: bilingual_pair_missing`.

## 8. Hard rules

- **No real PII ever.** No production data, no log-scraped data, no customer-derived data. AP-Q7 enforced.
- **No production data ever.** Even anonymized production data is forbidden — re-identification risk is non-zero.
- **Jurisdictional fidelity.** Thai test data must look Thai. Mixed-jurisdiction fixtures (e.g. US address with Thai phone) are forbidden unless the BA explicitly names a cross-border flow.
- **Reserved namespaces.** Email uses `.test` (RFC 6761). Phone uses test-safe Thai mobile sub-ranges. Domains never resolve.
- **Secrets sealed.** Plaintext passwords, tokens, and keys live in a gitignored sealed file the harness reads at run time. Fixture JSON carries handles or hashes only.
- **Determinism.** Identical seed ⟹ identical fixture stream. The skill never reads the system clock, the OS random source, or any non-fixture network resource.

## 9. Versioning

Every fixture set records a version in `test_data_specs[].fixture_set_id` (semver, e.g. `customer-fixture-set@1.0.0`). The version increments when:

- The synthesis pattern changes (e.g. phone prefix range adjusted).
- A new field is added to an existing fixture record.
- A constraint shifts (e.g. boundary upper limit raised).

The version is part of the canonical `output.json` and is included in the audit-event payload, allowing downstream consumers to re-derive fixtures deterministically by `(fixture_set_id, version, seed)`.

## 10. References

- `compliance-test-patterns.md` — compliance tests consume these fixtures.
- `nfr-derivation.md` — NFR tests reference the time-anchor and boundary fixtures.
- `anti-patterns.md` — AP-Q7 (real PII in fixtures) and AP-Q8 (clock-dependent fixtures).
- `v1.1-role-boundaries.md` — Role 4 (Test Data) jq examples for sourcing glossary pairs.
- Holdout source: `qa-holdout/e-commerce-v5/output-e5f8b9c2/05-pii-inventory.md` and `04-glossary.md`.
