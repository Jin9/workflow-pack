# Procedure Detail — Per-Step Expanded Rules

Authoritative expanded rules for the 12 Procedure steps in `SKILL.md`. The
`SKILL.md` body carries each step's imperative action; the binding sub-rules,
thresholds, field names, and AP/FM cross-references live here (no duplication).
Per-FM detection/output/escalation is in `edge-case-catalog.md`; this file covers
the procedural *how* of each step.

## Step 1 — Pre-flight: strip ground-truth + detect source type

Detect the literal heading `## Intentional Issues for R6 to Catch` (or variants
`## Hidden from BA Workflow`, `^## (Intentional|Hidden|Ground[- ]Truth|Audit
Annotation)`); strip everything from that line to EOF as the **first**
preprocessing pass. Strip failure / boundary overlap / multi-block /
substring-survival → **fail closed** (FM-12; `do_not_proceed: true`). After
strip, classify source type (Jira / Slack / meeting / email / doc-fallback)
using header markers; emit `ba_confidence: low` on fallback.

**FM-12 firewall (discovery handoff).** The ground-truth strip operates on
`raw_content` ONLY. The optional `discovery` object is structured input — it is
NEVER scanned for the ground-truth heading and NEVER stripped. Discovery can
neither contaminate the strip pass nor be contaminated by it.

Per-type detection markers:

- **Jira ticket** — bracketed key `[A-Z]+-\d+`; `Project:` / `Type:` /
  `Priority:` headers; `## Description / Acceptance Criteria / Comments / Linked
  Issues` sections.
- **Slack thread** — `#channel — Slack channel` banner; `Name (Role) — Today
  HH:MM`; emoji reactions; `📎 Linked:`.
- **Meeting notes** — `========` banner; `Meeting:` / `Date:` / `Note-taker:` /
  `Attendees:` / `[Apologies: …]` metadata; numbered agenda `## 1. … ## 8.`;
  `(Speaker, N min)`; `[Owner] task — due`.
- **Email** — `From:` / `To:` / `Subject:` / `Date:` quartet; `>` quote
  prefixes; signature `--`.
- **mixed/doc prose** — no canonical markers; generic fallback at reduced
  confidence (`ba_confidence: low`).

## Step 2 — Route to parser + extract structural skeleton

Dispatch the source-specific parser (Jira key:value + section parser; Slack
chronological + pronoun-window; meeting numbered-agenda + apologies; email
quoted-reply inversion). Classify `scope_kind` ∈ {single-story, multi-story,
single-epic, multi-epic, ambiguous, story_within_epic} per workstream count (≥3
distinct workstreams each with ≥2 ACs → multi-epic). Capture `## Parking Lot` /
"separate ticket" / "phase 2" / "out of scope" items as `out_of_scope_deferred`.
Never tech-layer split (AP-7.1).

## Step 3 — Build Domain Glossary + normalize dates + recognize regulator citations

Emit `glossary[]` with `canonical_form`, `surface_form`, `definition`,
`pii_sensitivity`, `regulatory_tie`. Normalize relative dates (`EOW`, `next
sprint`, `Q3`, `tomorrow`) against input metadata date; if ambiguous → emit P3
Open Question, never silent-resolve. Match regex
`[A-Z]{2,}-[A-Z]{2,}-[A-Z0-9-]+` and named regulators
`MAS|OFAC|FATF|FinCEN|PDPA|GDPR|PCI`; classify each as `resolved` (document
attached) or `unresolved` (named but no citation). Unresolved on T1 → block
handoff (FM-04); unresolved on T2 → P1 OQ + auto-action.

## Step 4 — Auto-classify PII + redact PII in input body

Match direct identifiers (NRIC, passport, biometric, fingerprint), indirect
(source of funds, PEP, sanctions match, account number), regulatory-confidential
(SAR filing, tipping-off comm), financial (bank statement, wire). For any actual
PII value in the input body, **never echo** — replace with
`<PII:REDACTED:CLASS=NRIC>` and emit a P1 governance alert (channel may be
non-compliant). Force a `pii_inventory` table for every story; empty inventory
without justification is a handoff block (AP-4.1).

## Step 5 — Extract stakeholders with authority weighting

Distinguish `{owner, sponsor, approver, sme, affected, external, meta}` (never
collapse). Classify SMEs by domain (compliance / engineering / risk / UX / ops /
vendor liaison). Stamp each utterance `authority_mode ∈ {rule, proposal,
preference, estimate, pain}`: rule mode binding (MUST NOT / can't / regulated /
explicit prohibition); proposal negotiable; preference soft; estimate range; pain
framing. Down-weight anonymous + paraphrased content (`attribution_confidence:
paraphrase|anonymous|group`); anonymous + numeric policy parameter → automatic P2
floor (AP-2.3). Detect mentioned-but-not-engaged (≥2 mentions, 0 utterances) —
Legal canonical case (C17). **Enumerate completeness duty**: include stakeholders
absent-but-implied (DPO when PII non-empty; card-network reps when network scope;
Treasury when funds movement) in `stakeholders[]` with `status: absent` (or
`handing-off` per leave) + `engagement_required_for: <reason>`. Scope-out in
`out_explicit` does NOT discharge the enumeration row.

## Step 6 — Surface missing stakeholders (Legal-absence is the highest-leverage gate)

Always emit `legal_status ∈ {present, scheduled, mentioned_only, absent}`. When
status ≠ `present` AND scope touches retention / customer-facing language /
tipping-off / sanctions / biometric / regulator citation / dual approval → emit a
P1 governance gap `legal_absent_on_regulatory`, `blocks_tl_handoff: true`. This
rule fires in 100% of pilot inputs. Also check Privacy/DPO (PII non-empty),
Security Reviewer (biometric / file upload / vendor), SAR Liaison (any SAR
mention), Model Owner (score-threshold-driven routing), Migration Owner (cutover
language). Compliance ≠ Legal (AP-3.2): Compliance describes regulation, Legal
interprets language — never conflate. **Dual write — every absent-implied
stakeholder identified here MUST also appear as a row in `stakeholders[]` (Step
5) with `status: absent` + `engagement_required_for`**, not only in
`governance_gaps[]`. The governance gap names the systemic risk; the stakeholders
row preserves the enumeration audit trail.

## Step 7 — Map structure to scope + emit stories

Split using legitimate axes: **workflow steps** (state machine with ≥2 named
states); **business-rule variations** (data class / customer tier / risk class
diverges); **data variations** (PII vs non-PII; biometric vs identity-doc);
**role boundaries** (customer UI vs agent UI; analyst sole-decider vs dual
approval); **happy vs error paths**; **CRUD**; **spike**. Never tech-layer
(AP-7.1). For multi-epic inputs, emit one epic per workstream; per-epic tier
inference (Step 11). AC density > 7 unsplit → flag (AP-7.3); use
`references/job-story-decision-tree.md` when format choice is ambiguous.

## Step 8 — Per-story banking-grade evaluation (force-fill 7 fields)

For every story, emit `banking_grade_concerns` with all 7 rows non-null:
`{pii_fields, audit_events, idempotency, reversibility, authn_authz, regulatory,
tipping_off}`. Each row: `status ∈ {applies, not_applicable, unknown_p2}` +
`justification` (≥10 chars; cite workflow class on `not_applicable`). Empty row →
schema validation hard fail (FM-11). `reversibility.applies` + irreversible op →
require `compensating_action`. Auto-emit an idempotency-replay scenario for any
state-change / notification op (AP-4.3).

## Step 9 — Detect ambiguities (8 types) with severity + tipping-off scan

Run detectors over each text segment: **lexical** (vague words
`urgent`/`reasonable`/`appropriate` without testable predicate); **syntactic**
(parenthetical aside negates main clause — `replaced (or maybe kept as version?
unclear)`); **pragmatic** (context-dependent reference); **pronominal** (pronoun
across >1 sentence boundary); **quantifier** (`a LOT`/`some`/`several`/`most`
without adjacent numeric — cluster >5 → completeness penalty); **modal**
(`may`/`might`/`could`/`should` in prescriptive sections — compliance speaker
rule-mode elevates "should" → "MUST"); **commitment-conditionality** (`yes/ok/will
… pending|subject to|once|if X` — soft agreements contingent on unmet
preconditions → P2 OQ; never encode as firm scope); **phase-boundary drift**
(Phase 1 / Phase 2 split + deferred items + pressure signals → P2 OQ on
pull-forward risk + P3 assumption on deferred-phase commitment status). Plus
placeholder tokens `(?), TBD, $Xk`. Assign P1/P2/P3 per
`references/ambiguity-patterns.md`. Run `tipping_off_scan` over every
customer-facing string for forbidden terms (sanctions / AML / flagged /
suspicious / regulated / SAR / PEP / adverse media / EDD); on hit → P1 +
safe-phrase mitigation from `references/non-tipping-vocabulary.md` +
`legal_signoff_required: true` + block TL handoff. Anti-patterns compose — never
deduplicate flags across detectors.

## Step 9.5 — Hidden-requirements sweep (frame-driven elicitation-gap detection)

Step 9 catches what the prose says ambiguously; this step catches what the prose
doesn't say at all. Load `references/hidden-requirements-frames.md` and apply the
10 frames: scale & capacity (always), time & timing (always), money & economics
(conditional on monetary content), regulatory & legal (conditional on PII /
payment / regulated activity / named market), operational & organizational
(always), failure & edge cases (always), integration & dependencies (conditional
on external systems), localization & culture (conditional on named market),
lifecycle (always), customer experience (conditional on human-facing surface).
For each activated frame, emit at most the frame's soft cap (5 for most; 7 for
failure; 10 for regulatory) findings ranked by blast radius. **Cap exception:**
mandatory FM-17 sub-topic coverage on Frame 4 takes precedence over the soft cap
of 10; when it does, declare the overshoot in
`processing_metadata.hidden_requirements_sweep.cap_exceptions["4"]` with `{cap,
observed_count, reason (>=8 chars)}` (see `references/version-notes.md` for the
assertion-F-8 maturity timeline). **Each finding lands in `open_questions[]` with
`provenance: hidden_frame_sweep` and `frame: N`**, or — when a defensible default
exists — in `assumptions_made[]` with the same tags plus
`default_revisit_trigger` (a named date, telemetry signal, or event when the
default gets re-evaluated). Severity floors per frame (P1 capacity / regulatory;
P2 most others; P3 lifecycle / CX). Emit
`processing_metadata.hidden_requirements_sweep` recording `frames_applied`,
`frames_skipped` + reasons, `findings_per_frame`, `deferred_findings_count`,
`total_findings`, `coverage_score ∈ {complete, partial, skipped}`. The sweep does
not duplicate Step 9 ambiguity findings or Step 5 stakeholder enumeration — it
covers the gaps neither catches.

## Step 10 — Compose Gherkin acceptance criteria with testability check

Rewrite every prose AC into `Given/When/Then` with concrete values (resolve `EOW`
via Step 3; resolve anonymous `N=3` per AP-2.3; replace `$Xk` with TBD + named
owner). Mandatory scenario types per story: ≥1 **happy** + ≥1 **error/edge_case**
+ ≥1 **banking_grade_*** (idempotency-replay if state-change; audit-emission with
payload `{event, actor, ts, before, after, reason, idem_key}`; tipping-off-safe
if customer-facing). `Given` references concrete state + actor; `When` is a single
trigger (no `and` chains — AP-8.2); `Then` is an observable outcome (state change
/ payload / audit event / UI element — reject `is happy`/`satisfied`/`fast`).
Composite linguistic quality < 5.0 → refuse handoff (FM-01).

## Step 11 — MoSCoW prioritization + tier inference (per epic)

Apply tier rules per epic (NOT per file — multi-epic inputs carry heterogeneous
tiers): regulator-cited → T1; compliance officer + AML/sanctions/EDD/SAR/PEP → T1
candidate; compliance officer + PII high-grade → T2 (T1-shadow); customer-facing +
PII any → T2; no regulator + no compliance + prototype language → T3; else T2 + P2
"tier ambiguous". When inferred tier > `tier_hint` by ≥1 step → emit
`inferred_higher_than_manual: true` + require human override (AP-1.3). MoSCoW per
ba-best-practices §6 — `>70% Must` triggers re-evaluation. Never collapse internal
SLAs into one customer-facing ETA without flag (AP-3.1). **Discovery `tier_signal`
is a FLOOR only**: `effective_tier = max(inferred, tier_hint, tier_signal)` — it can
raise but never lower; if it raises above `tier_hint` by ≥1 step the AP-1.3 override
path fires. If `discovery.recommendation ∈ {needs-work, do-not-build}`, emit a P2 OQ
("upstream discovery did not clear this initiative — confirm intake authorization")
— never auto-block, never silently proceed.

## Step 12 — Failure-mode evaluation + output assembly

Final gates: FM-01 (quality < 5.0), FM-02 (any unresolved P1 in `{compliance,
tipping_off, retention, audit_schema, pii_inventory, regulatory_citation,
dual_approval}`), FM-05 (Legal absent + regulatory), FM-06 (tipping-off
violation), FM-11 (schema validation), FM-12 re-confirmation, FM-13
(post-generation PII echo scan), **FM-14 count consistency** (OQ-table header N ==
row count; stakeholders[] enumeration ⊇ absent rows), **FM-15 sweep-coverage**,
**FM-16 idempotency-replay enforcement** (every story declaring
`bgc.idempotency.status: applies` MUST carry a `banking_grade_idempotency` AC
scenario, enforced by schema if/then AND renderer runtime check), **FM-17 Frame 4
sub-topic coverage** (Frame 4 activated triggers must cover their required
sub-topics per `references/hidden-requirements-frames.md`). See
`references/version-notes.md` for which FMs/behaviors landed in which version.

FM-15 — `coverage_score` is graded as: **`complete`** = every activated frame
produced ≥1 finding AND `frames_applied ∪ frames_skipped == {1..10}` AND every
skipped frame has a non-empty entry in `frames_skipped_reasons`; **`partial`** =
at least one activated frame produced 0 findings (the input is unusually complete
on that frame, OR the sweep was rushed) OR a skipped frame lacks a reason;
**`skipped`** = the sweep was not run (only valid for failure shapes). `complete`
required for `output_type: brief`; `partial` allowed for `blocked_partial_brief`
provided a P2 OQ records the gap.

**Bilingual emission:** when the input requires output in multiple languages
(e.g., Thai team alongside English), set
`processing_metadata.bilingual_output: ["en", "th"]` (or wider) AND populate
per-object `translations[<lang>]` maps for every text-bearing object
(open_questions, assumptions_made, governance_gaps, glossary, pii_inventory,
regulatory_dependencies, epics, stories) per `references/bilingual-emission.md`.
The renderer emits one subtree per language under `output-{idem8}/<LANG_UPPER>/`;
the canonical JSON lives once at the root. Missing per-field translations fall
back to the English source (graceful).

**Emit JSON conforming to `schemas/output.json`** as the canonical artifact, then
invoke `scripts/render_markdown_tree.py` with `--input output.json --output-dir
output-{idem8}/` to deterministically render the Markdown directory tree per
`references/markdown-rendering-spec.md`. The directory tree MUST be emitted
alongside the JSON for all non-failure outputs. For failure shapes
(`needs_clarification`, `preprocessing_failure`, `pii_echo_blocked`,
`schema_validation_failure`, `meta_response`), emit `README.md` + `output.json` +
`FAILURE.md` only (no `epics/` tree). The JSON remains canonical; the Markdown
tree is mechanically derived and carries no contractual weight independent of the
JSON. When a `discovery` handoff was consumed, stamp
`frontmatter.upstream_refs.discovery_audit_id = discovery.audit_id`; FM-14
count-consistency includes any discovery-seeded absent stakeholder rows in its
`stakeholders[] ⊇ absent rows` check.

## Discovery handoff threading (S1 composite — add-only, never suppress)

The optional `discovery` input (a typed handoff from `researching-ba-problem-space`,
supplied after the S1 human review gate) is **advisory** at every step: it may only
*add* findings, rows, or a tier floor — it can NEVER suppress a detector, lower a
tier, satisfy a citation, or replace `raw_content`. This keeps all 17 failure modes
intact (each still fires from `raw_content`) and keeps the brief idempotent: content
is a pure function of `(raw_content, discovery)`.

| Step | What discovery seeds | Hard limit |
|---|---|---|
| 1 | nothing (firewall) | never scanned / stripped (FM-12 firewall above) |
| 3 | `regulatory_regimes[]` → `regulatory_dependencies[]` rows at `citation_status: pending` | leads, not citations — an unresolved citation still blocks T1 (FM-04 / EC-18) |
| 5–6 | `stakeholder_hints[]` → absent-but-implied rows (dual-write `stakeholders[]` + `governance_gaps[]`) | never discharges the Legal-absence gate (FM-05 / AP-5.1 still fire from `raw_content`) |
| 11 | `tier_signal` (floor), `recommendation` (P2 OQ if not `proceed`) | floor only; AP-1.3 override on raise |
| 12 | `audit_id` → `upstream_refs.discovery_audit_id` | provenance only; no content effect |

**Idempotency note.** Because `discovery` is content-bearing input, the idempotency
contract reads "same `idempotency_key` + same `raw_content` + same `discovery` → same
output." An orchestrator/engine cache MUST hash the full input (the squad-engine
`sha256(skill_ref, version, prompt_version, input_hash)` already does); any cache
keyed on `idempotency_key` alone is a bug. When `discovery` is absent (the standalone
path), behavior is byte-identical to v1.4.1. See `references/version-notes.md`.
