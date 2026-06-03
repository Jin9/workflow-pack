# BA discovery method — framing, opportunities, risks, regulatory

Grounded in the ResearchVault: product discovery is the upstream stage that
decides "whether you are building the right thing" BEFORE engineering/intake —
investigating the problem space, framing opportunities, and surfacing assumptions
and risks (Cagan's four risks; Torres' opportunity-solution-tree) — and the
durable pattern is "AI-as-first-drafter, human-as-decider": a synthesized
research artifact seeding a human review gate. See
`[[literature/product-requirements/product-discovery-with-ai]]`. The BA value
chain then runs elicit → refine → specify → trace → delivery, i.e. intake begins
one step downstream of discovery. See
`[[literature/product-requirements/ai-assisted-ba-workflow]]`.

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
recommendation, but the **named human decides** at the review gate. On "proceed",
hand the framing into intake (`eliciting-banking-brief` / `scoping-ba-intake`),
which structures the requirement. This skill does not write stories or
architecture.

## Typed handoff into intake (composite S1)

On `recommendation: proceed`, emit the `handoff_to_intake` block. It is the typed
contract the composite S1 chain feeds into `eliciting-banking-brief`'s optional
`input.discovery` field. The two shapes are field-for-field compatible.

| `handoff_to_intake` field | Meaning | How intake uses it (advisory only) |
|---|---|---|
| `audit_id` | Same id as the top-level `audit_id` | Stamped into the brief's `frontmatter.upstream_refs.discovery_audit_id` — proves the chain |
| `recommendation` | Always `proceed` here (allOf-guarded) | Surfaces a P2 open question downstream if it were ever not `proceed` |
| `tier_signal` | Discovery's T1/T2/T3 read | A **floor** only: intake takes `max(inferred, tier_hint, tier_signal)`; never lowers a tier |
| `stakeholder_hints[]` | Absent-but-implied roles | Seed intake's absent-stakeholder enumeration; never discharge a Legal-absence gate |
| `opportunity_detail[]` | Richer opportunities + regimes | Scope leads only; never satisfy a regulator citation |

**Orchestrator merge recipe.** The composite S1 builds `eliciting-banking-brief`'s
`input.discovery` by merging the discovery artifact's top-level fields
(`problem_framing`, `opportunities`, `assumptions`, `regulatory_regimes`,
`recommendation`, `audit_id`) with the `handoff_to_intake` extras
(`tier_signal`, `stakeholder_hints`, `opportunity_detail`). The merged object is
passed only after the human review gate clears `proceed`.

**RB-01 short-circuit.** If the S1 input is already a fully-structured requirement,
discovery adds no value: emit the `note` per RB-01, emit **no** `handoff_to_intake`,
and let the composite run `eliciting-banking-brief` standalone with `input.discovery`
omitted — which is the existing, fully-tested intake path.

The handoff is **advisory**: every field is a lead intake may seed but never use to
suppress one of its own detectors, lower a tier, or satisfy a citation.
