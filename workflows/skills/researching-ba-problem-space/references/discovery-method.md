# BA discovery method — framing, opportunities, risks, regulatory

Grounded in the ResearchVault: product discovery decides "whether you are
building the right thing" before requirements are elaborated — investigating the
problem space, framing opportunities, and surfacing assumptions and risks
(Cagan's four risks; Torres' opportunity-solution-tree) — and the durable
pattern is "AI-as-first-drafter, human-as-decider": a synthesized research
artifact seeding a human review gate. See
`[[literature/product-requirements/product-discovery-with-ai]]`. In THIS
pipeline's composite S1, discovery runs AFTER S0 has normalized the request and
BEFORE `ba-research` elaborates the brief: S0 intake → s1-discovery → human gate
→ ba-research. See `[[literature/product-requirements/ai-assisted-ba-workflow]]`.

## Frame the problem (not the solution)

State the problem, the affected users/segment, and why now. Resist proposing a
build; discovery is about the opportunity.

## Opportunity-solution-tree

Map the desired outcome → candidate opportunities → (later) possible solutions.
Keep opportunities distinct from solutions so the squad does not over-commit.

## The four risks (Cagan)

For each material assumption, classify the risk and say how to de-risk it:
- **value** — will anyone want it? (interviews, demand signal)
- **usability** — can they use it? (prototype tests)
- **feasibility** — can we build it on the stack? (spike — hand to technical-feasibility)
- **viability** — does it work for the business/regulator? (cost, compliance)

## Regulatory-regime mapping (banking)

Identify regimes in play — KYC, AML, sanctions screening, PCI-DSS, data
residency — and flag any that gate the initiative. A hard regulatory blocker
escalates to a human governance gate; never auto-clear it.

## AI drafts, human decides; then hand off

Produce the discovery artifact and a proceed / needs-work / do-not-build
recommendation, but the **named human decides** at the review gate — only
`proceed` releases the brief node (`ba-research`, skill
`breaking-down-ba-scope`), which structures the requirement. This skill does
not write stories or architecture.

## Typed handoff to the brief node (composite S1)

On `recommendation: proceed` (top-level AND nested — allOf-guarded), optionally
emit the `handoff_to_intake` block. The engine delivers it to the brief node
nested inside `input.discovery` (see the real payload below).

| `handoff_to_intake` field | Meaning | How intake uses it (advisory only) |
|---|---|---|
| `audit_id` | Same id as the top-level `audit_id` | Stamped into the brief's `frontmatter.upstream_refs.discovery_audit_id` — proves the chain |
| `recommendation` | Always `proceed` here (allOf-guarded) | Surfaces a P2 open question downstream if it were ever not `proceed` |
| `tier_signal` | Discovery's T1/T2/T3 read | A **floor** only: intake takes `max(inferred, tier_hint, tier_signal)`; never lowers a tier |
| `stakeholder_hints[]` | Absent-but-implied roles | Seed intake's absent-stakeholder enumeration; never discharge a Legal-absence gate |
| `opportunity_detail[]` | Richer opportunities + regimes | Scope leads only; never satisfy a regulator citation |

**The real payload (engine NESTED_HANDOFF — no flattening, no merge).** The
YAML picks exactly `problem_framing`, `regulatory_regimes`, `recommendation`,
`audit_id`, and `handoff_to_intake` from this stage, and the engine
(`engine/mapping.py`) nests them under one `discovery` key in the brief node's
input: `discovery.problem_framing`, …, `discovery.handoff_to_intake.*`.
`opportunities` and `assumptions` are NOT transferred (the YAML never picks
them). The payload is delivered only after the human review gate clears
`proceed`; an absent `discovery` (or absent handoff) is byte-identical to the
pre-handoff brief behaviour.

**Failure shapes.** A blocked/failed discovery (RB-01 unusable input, RB-02
regulatory hard-blocker, RB-03 insufficient context) still emits the required
top-level fields plus `failure_state` (`{failure_code, message, remediation}`,
optional `blockers[]`/`open_questions[]`), recommends `needs-work` /
`do-not-build`, and never carries a handoff. There is no "route back to
intake" — S0 has already completed when this stage runs.

The handoff is **advisory**: every field is a lead intake may seed but never use to
suppress one of its own detectors, lower a tier, or satisfy a citation.
