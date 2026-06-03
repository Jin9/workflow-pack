# L4 Implementation Spec Template (scaffold-v1.1 §6.3)

**Owner role:** Tech-Lead initially; engineer once implementation starts.
Per-story implementation contract. Volatile (one per story, sprint-lifetime).
**References** the per-service API spec — does NOT duplicate it.

**File location:** `<workflow_root>/design/architecture/contexts/{ctx}/stories/{story-id}-L4-spec.md`

---

## Frontmatter

```yaml
---
artifact_type: tl-l4-implementation-spec
project_id: <PROJECT-ID>
context_id: <ctx>
story_id: EPIC-<...>-<n>
story_title: "<verbatim BA story title>"
brief_id: <EPIC-...>
workload_tier: T1 | T2 | T3
priority: Must | Should | Could | Won't
spec_status: draft | ready-for-implementation
implementation_skill: implement-backend-feature | implement-frontend-feature

# Command declaration (DDD doc §2.1)
command:
  name: <Imperative>            # business intent; MUST NOT match Submit*/Process*/Handle*/Manage*
  target_aggregate: <Aggregate>
  transport: sync_http | async_event
  intent: "<one line>"
  idempotency_required: true | false
  idempotency_key_source: <client_provided_uuid | derived | n/a>

# Event declarations (DDD doc §2.2)
events_emitted:
  - name: <domain>.<subject>.<verb-past>   # past-tense business fact
    type: domain | process
    when: "<condition>"
    schema_ref: schemas/<event>.v1.json
    consumers_known: [<consumer>, ...]
# OR, if no event:
# events_emitted: []
# no_event_rationale: "<why no fact worth recording>"

api_spec_endpoint_ref: ../api-spec.md#endpoint-<...>
api_spec_version_at_authoring: v1.0
ux_design_ref: null
test_plan_ref: null
adrs_referenced: [ADR-NNN]
estimated_complexity: low | medium | high
blocking_oqs: []
created_at: <ISO-8601>
created_by: designing-tech-lead-handoff-<version>
---
```

## Content sections (18)

1. **Story summary** — quote the BA Gherkin happy-path verbatim.
2. **Affected components** — files / packages new and modified.
3. **Command implementation** — restate command name + intent + target
   Aggregate; entry validation rules; Aggregate method invoked; transactional
   boundary; reference to the API-spec endpoint (not duplicated).
4. **Aggregate state transitions** — Mermaid `stateDiagram-v2` excerpt for the
   transitions this story triggers; cross-reference the full Aggregate state
   machine.
5. **Invariants enforced** — the business rules this story's command must
   respect (business correctness lives only in Domain Processors).
6. **Event emission decision** — justify events emitted (what fact occurred) or
   justify none (why no fact worth recording).
7. **Sync / async classification** — command transport; each event emission
   transport (always async via Kafka); sync checkpoint events; cross-context
   calls + transport.
8. **Pseudo-code for non-obvious decisions only** — skip mechanical bits;
   pseudo-code only non-trivial business decisions.
9. **Multi-actor sequence diagram** — Mermaid `sequenceDiagram`, required when
   2+ services or actors; optional for pure single-service stories.
10. **Data model deltas** — SQL DDL, migration filename, indexes.
11. **Idempotency rule** — explicit.
12. **Authorization rule** — explicit.
13. **Concurrency considerations** — within-Aggregate locking, optimistic CAS
    (the Aggregate is the consistency boundary).
14. **Non-functional targets** — restate from nfr/SLO source.
15. **Compliance flags** — regulatory concerns this story touches.
16. **ADRs referenced.**
17. **Implementation hints** — optional.
18. **Definition of Done.**

## Naming discipline (scaffold-v1.1 §6.4 — validated at generation time)

- `command.name` imperative; MUST NOT match `Submit*`, `Process*`, `Handle*`,
  `Manage*`.
- `events_emitted[].name` past-tense `{domain}.{subject}.{verb-past}`; MUST NOT
  contain technical verbs (`*.processed`, `*.handled`, `*.managed`).
- A violation blocks this spec from `spec_status: ready-for-implementation`.
