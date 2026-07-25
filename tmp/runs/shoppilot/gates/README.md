# T1–T12 · Test & security gates (Quality-Gate Board)

**Status:** ▶ simulated · roll-up **GREEN** (all PASS / promote / pass).

The 12 post-development gate verdicts. The Delivery Review Console (`../delivery-review.html`) discovers these
files by name and rolls them into the **Quality-Gate Board** (worst-of R/A/G). Each validates against both its
gate skill `schemas/output.json` and its boundary `workflows/schemas/<gate>.json`.

| File | Gate | Skill | Verdict |
|---|---|---|---|
| `backend-unit-tests.json` | T1 backend unit | `executing-backend-unit-tests` | PASS (96/96, cov 86%) |
| `sast-gate.json` | T2 SAST | `running-sast-security-gate` | PASS (0 secrets) |
| `frontend-unit-tests.json` | T3 frontend unit | `executing-frontend-unit-tests` | PASS (71/71) |
| `accessibility-tests.json` | T4 a11y (WCAG AA) | `running-accessibility-tests` | PASS (0 violations) |
| `contract-tests.json` | T5 contract (Pact) | `contract-testing-pact` | PASS (can_i_deploy) |
| `integration-tests.json` | T6 integration (SIT) | `executing-integration-tests` | PASS (38/38, teardown ok) |
| `appsec-scan.json` | T7 AppSec (DAST/SCA) | `scanning-appsec-pipeline-gate` | PASS (0 secrets/CVE) |
| `e2e-tests.json` | T8 end-to-end | `authoring-e2e-test-suite` | PASS (3 scenarios) |
| `perf-load-test.json` | T9 perf/load | `running-performance-load-test` | PASS (p95 540ms, within budget) |
| `adversarial-pentest.json` | T10 pentest (human) | `validating-banking-implementation` | pass (advisory) |
| `smoke-tests.json` | T11 smoke | `running-smoke-tests` | PASS (3 probes green) |
| `canary-analysis.json` | T12 canary | `analyzing-canary-rollout` | promote (3 windows) |

> Gate evidence schemas are `additionalProperties:false` (no free-text headline field) — the board synthesizes
> each cell's headline from the gate's own fields (totals, secrets, scenarios, metrics, …).
