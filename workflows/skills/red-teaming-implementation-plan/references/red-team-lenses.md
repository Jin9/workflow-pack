# Red-team lenses, steelman, bias mitigation, verdict policy

Grounded in the ResearchVault: a heterogeneous/stronger critic reliably beats
same-model self-critique, and a plan-level critique belongs at a probabilistic
review gate before the human acceptance gate — see
`[[literature/llm-routing-cost/using-frontier-models-for-review]]` and
`[[literature/agent-orchestration/human-in-the-loop-gates]]`.

## The mandatory steelman (do this first)

Before hunting flaws, write the strongest honest case FOR the plan. This is not
politeness — it directly counters the documented reviewer failure modes
(self-preference bias and the ~38%+ false-negative rejection of correct work). A
finding only counts if it survives after you have argued the plan's best case.

## Attack lenses

Sweep every lens. Emit a finding only when there is evidence in the plan or a
missing requirement in the hydrated `stories` — never on style or taste.

- **requirements** — Does the plan satisfy every story / acceptance criterion?
  Unmapped criteria, scope creep, or silent assumptions.
- **architecture** — God-service / BPM-monolith, missing bounded-context seams,
  an orchestrator deciding "is this correct?" instead of "what's next?".
- **contract** — Vague or missing API/event contracts, no idempotency rule on
  money-moving operations, breaking-change risk, command-vs-event confusion.
- **data** — Dual-write without an outbox, no compensation path, ordering /
  consistency assumptions that the infra cannot honor.
- **security** (handoff) — Auth/authorization boundaries, secret handling, PII
  exposure. Flag for a real security review; do not deep-model here.
- **operability** — No rollback/runbook hook, unobservable failure, no SLO/alert
  consideration, unbounded retries.
- **cost** — Fan-out blast radius, model-tier mismatch, unbounded loops.
- **testability** — Criteria that cannot be tested, no seam for contract/E2E,
  hidden state that blocks deterministic verification.

## Bias mitigation (apply before finalizing)

Re-read each finding and drop or downgrade it if any hold:

- **Hallucinated flaw** — references a file/requirement/CWE not present in the
  inputs. Delete it.
- **Position / verbosity bias** — flagged because it appeared first/last or the
  section was long. Re-judge on substance.
- **Unfalsifiable** — cannot be confirmed or denied from the plan. Convert to an
  open question, not a blocking finding.
- **Self-preference / heterogeneity** — if the reviewer is the same model that
  authored the plan, record it in `bias_checks` and lower `confidence`; prefer a
  different/stronger reviewer.

## Verdict policy

- **Governance preflight (deterministic, runs before the lenses):** any upstream
  governance gap with `severity: P1` or `blocks_tl_handoff: true` produces a
  `high` finding with `category: governance` and forces **BLOCK** — a named
  human clears the gap; the reviewer never resolves or waives it. A `P2` gap
  produces at least a `medium` finding and REVISE unless the plan explicitly
  resolves it.
- **BLOCK** — at least one `high` finding sits on a *required* path (a story the
  release must deliver, or a money/PII/security boundary). Do not fan out.
- **REVISE** — `medium` findings exist but no blocking `high`; the planner should
  address them and re-submit.
- **PROCEED** — only `low` findings remain; record them as advisory.

Set `confidence` lower for thin evidence or missing stories, and cap it at 0.75
while author provenance is unknown (heterogeneity cannot be proven). The skill
stops at the verdict; engine routing (engine/policies.py): REVISE and BLOCK both
loop back to tl-design with the findings threaded (one permitted loop); a
non-proceed verdict after the cap aborts the run.
