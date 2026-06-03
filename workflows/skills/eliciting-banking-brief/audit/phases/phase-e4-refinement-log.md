# Phase E4 — Skill Refinement Log (ba-elicit-from-raw v1.0.0 → v1.0.1)

> **Input**: E3 comparison report (`phase-e3-comparison-report.md`) — total score 44.5/50, PASS with refinements.
> **Refiner mandate**: address top 3 priority fixes (P1 schema serialization, P2 ambiguity patterns, P2 stakeholder enumeration) plus any additional critical gaps surfaced in §4 of the E3 report.
> **Discipline**: minimal-bloat edits; preserve E1's good content; cross-reference integrity maintained; SKILL.md body ≤ 220 lines after changes.

---

## Files Modified

| # | File | Lines before | Lines after | Net change |
|---|---|---|---|---|
| 1 | `SKILL.md` | 139 | 141 | +2 |
| 2 | `references/ambiguity-patterns.md` | 113 | 127 | +14 |
| 3 | `schemas/output.json` | 788 | 796 | +8 |

Three files touched. All other skill files (other references, other schemas, all tests/assertions) unchanged — they passed E3 scrutiny without specific actionable updates.

---

## Change Detail

### Fix 1 — P1 Schema Serialization Contract Gap

**E3 finding**: §2.10 Schema Validity scored 3/5. The SKILL.md described output as Markdown; `schemas/output.json` enforces strict JSON. Inconsistent contract — markdown emission would fail strict JSON validation.

**Resolution applied**: Documented dual-emission contract — **JSON is canonical (schema-validated), markdown is optional presentation**.

#### 1a. `SKILL.md` § Output Contract — clarify dual emission

**Change**: Replaced lone-line "Output is JSON conforming to `schemas/output.json`" with a dedicated dual-emission paragraph that names JSON as the load-bearing contract and markdown as non-canonical presentation. Added explicit invariant: "If only one format is emitted, it MUST be the JSON."

**Lines added**: ~3 prose lines.

**Justification**: Closes the highest-severity gap (P1) from E3. Schema's `additionalProperties: false` + `oneOf` + `allOf` invariants now have a clear contractual home; orchestrator gets a single authoritative artifact.

#### 1b. `SKILL.md` § Procedure Step 12 — emphasize JSON conformance

**Change**: Expanded Step 12 ("Output assembly") to explicitly enumerate the JSON-shape constraints that E3 §2.10 flagged as PARTIAL: (a) `idempotency_key` MUST be a real UUID v4, (b) `tier_signals[]` as structured `{signal, weight, evidence_quote}` objects (not flat strings), (c) `ba_compliance_checklist` as 10 boolean keys (not markdown checkboxes), (d) Gherkin ACs as `{scenario_name, scenario_type, given[], when, then[]}` arrays (not inline markdown). Added closing line that markdown rendering MAY accompany the JSON but is non-canonical. Also added a new final gate **FM-14 count consistency** to address E3 §2.5/§2.8 counting bug ("15 open questions" header / 17 OQ rows).

**Lines added/changed**: ~5 lines net (incorporated into existing paragraph).

**Justification**: E3 §2.10 listed four PARTIAL schema-validity gaps (P2-7, P2-8, P2-4, gherkin-shape). All four now have explicit guidance in Step 12, making them schema-compliant on next run. FM-14 closes the cosmetic counting-bug gap (E3 P2-1) by promoting it from "self-attestation" to "enforced gate" — same pattern as FM-12 ground-truth-strip self-verify.

---

### Fix 2 — P2 Add 2 missed ambiguity patterns

**E3 finding**: §2.5 Ambiguity Surfacing scored 4/5. Skill missed two ground-truth ambiguities:
1. **Commitment-conditionality** (Yvonne's "Q3 candidate list pending Phase 1 scoping") — soft commitment treated as firm scope
2. **Phase-boundary drift** (Phase 1 / Phase 2 split with pull-forward risk under customer pressure)

**Resolution applied**: Added two new ambiguity-type entries (§3.7, §3.8) to `references/ambiguity-patterns.md` and wired them into `SKILL.md` Step 9 detector list.

#### 2a. `references/ambiguity-patterns.md` — add §3.7 Commitment-Conditionality + §3.8 Phase-Boundary Drift

**Change**: Added two new ambiguity-type entries below §3.6 Modal. Each entry follows the existing template — definition + detection regex/tokens + default severity + rewrite example with concrete pattern from the E3 hold-out (Yvonne's Q3 commitment, Phase 1/Phase 2 split). Also updated:
- Title `## 6 Ambiguity Types` → `## 8 Ambiguity Types`
- Preamble `Run all 6 detectors` → `Run all 8 detectors`
- Severity-assignment table P2 row — appended `commitment-conditionality (§3.7); phase-boundary drift (§3.8)` to P2 triggers

**Lines added**: ~14 (12 for the two new pattern blocks + 2 for header/preamble updates).

**Justification**: Closes E3 §2.5 P2 gaps directly. Two ground-truth ambiguities missed by the v1.0.0 output now have first-class detectors with default severity rules. The rewrite examples cite the exact hold-out evidence (Yvonne's quote, Phase 1/Phase 2 catalogue) so the next run has concrete pattern recognition.

#### 2b. `SKILL.md` Step 9 + references list — wire 8 detectors

**Change**:
- Step 9 prose: `(6 types)` → `(8 types)`; appended two new detector descriptions (commitment-conditionality + phase-boundary drift) with detection cues.
- References list line for `ambiguity-patterns.md`: updated to enumerate all 8 detectors so progressive-disclosure loaders see the full surface.

**Lines added/changed**: ~2 lines net.

**Justification**: SKILL.md Step 9 is the canonical detector inventory. Without this update the procedure would still claim "6 detectors" while the reference file shows 8 — cross-reference integrity preserved.

---

### Fix 3 — P2 Stakeholder Enumeration Completeness

**E3 finding**: §2.7 Stakeholder Mapping scored 4.5/5. Card network reps + DPO were correctly identified as absent-implied stakeholders but appeared only in `out_explicit` scope rows + `governance_gaps[]` evidence — NOT in the `stakeholders[]` table with an `absent` status row.

**Resolution applied**: Added dual-write rule to SKILL.md Step 5 (extraction completeness) + Step 6 (governance vs stakeholders enumeration), and added `status` + `engagement_required_for` fields to the `Stakeholder` sub-schema in `schemas/output.json`.

#### 3a. `SKILL.md` Step 5 — enumeration completeness duty

**Change**: Appended bold "Enumerate completeness duty" sentence to Step 5 — explicitly requires absent-but-implied stakeholders (DPO when PII non-empty; card-network reps when network scope; Treasury when funds movement) to appear in `stakeholders[]` with `status: absent` + `engagement_required_for: <reason>`. Closing clarification: "Scope-out in `out_explicit` does NOT discharge the enumeration row."

**Lines added**: ~1 line (incorporated into existing step paragraph).

**Justification**: Directly addresses E3 P2-5 (card network reps) + P2-6 (DPO). Makes the dual-track rule explicit so v1.0.1 output emits both the scope-out item AND the stakeholder row.

#### 3b. `SKILL.md` Step 6 — dual write to stakeholders[] AND governance_gaps[]

**Change**: Appended bold "Dual write" sentence to Step 6 — every absent-implied stakeholder identified in Step 6 must ALSO appear as a row in `stakeholders[]` (set up in Step 5). Governance gap names the systemic risk; stakeholders row preserves the enumeration audit trail.

**Lines added**: ~1 line (incorporated into existing step paragraph).

**Justification**: Closes the cross-step integrity loop. Step 5 builds the stakeholders[] surface; Step 6 detects governance absences. Without explicit dual-write guidance Step 6 could write to governance_gaps[] only — E3's documented v1.0.0 failure mode.

#### 3c. `schemas/output.json` — Stakeholder sub-schema gains `status` + `engagement_required_for`

**Change**: Added two new optional properties to `definitions.Stakeholder`:
- `status` (enum: `active | absent | handing-off | mentioned_only | scheduled`) with a description tying it to the enumeration-completeness rule
- `engagement_required_for` (string) with a description noting when it's required (status ∈ {absent, mentioned_only, scheduled})

Did NOT make `status` a required field — preserves backwards-compatibility with existing valid `Stakeholder` rows (the E3-evaluated output had named active stakeholders without `status` and those should still validate).

**Lines added**: ~8 lines.

**Justification**: Makes the schema express what the SKILL.md procedure now requires. Future schema validation can catch missing absent-status rows. Conservative choice not to make `status` required protects existing valid outputs.

---

## Additional E3 Gaps NOT Addressed (Deferred / Judgment Call)

E3 §4 listed 8 P2s + 5 P3s. After the priority-3 fix set above, the following remain unaddressed in this E4 pass — rationale per item:

| E3 ID | Title | Status | Rationale |
|---|---|---|---|
| **P3-1** | Reduce Story 5 title to avoid AP-7.1 false-positive on "API" | Deferred | Cosmetic. Story 5 title is per-output content, not skill-level guidance. Step 7 already references invest-checklist.md for I-2 enforcement. Not a structural skill defect. |
| **P3-2** | Split Story 1 happy-path When to single-action | Deferred | Cosmetic. `gherkin-templates.md` already covers AP-8.2 (multi-action When forbidden) — the Step 10 enforcement is intact. The borderline case in v1.0.0 output is a per-instance writing decision. |
| **P3-3** | OQ-source-attribution tag for derived OQs | Deferred | The `OpenQuestion` schema already has `attribution` and `proposed_value` optional fields. Adding `derivation_rule` would be a schema extension worth doing in a v1.1.0 minor. Not a P1/P2 gap. |
| **P3-4** | Ground-truth-strip self-verify enforced gate | Partially addressed | FM-14 now exists as a final-gate naming pattern. Specific substring-survival post-scan can be tightened in v1.1.0. |
| **P3-5** | Skill version stamp in created_by | Deferred | E3 confirmed v1.0.0 output already matched. No structural defect; check belongs in a CI script not the SKILL.md. |

P2-1 (counting consistency) → addressed via new FM-14.
P2-4 (UUID v4 idempotency_key) → addressed in Step 12.
P2-7 (tier_signals structured shape) → addressed in Step 12.
P2-8 (ba_compliance_checklist booleans) → addressed in Step 12.

All other P2s addressed via the 3 priority fixes.

---

## Constraint Confirmation

- **SKILL.md body line count**: 141 lines (was 139). Limit: 220 lines. **PASS** (79 lines of headroom).
- **JSON syntax validity**: `schemas/output.json` parses cleanly via `python3 -m json.tool`. **PASS**.
- **Cross-reference integrity**:
  - `SKILL.md` Step 9 references 8 detectors ↔ `ambiguity-patterns.md` defines 8 detectors. **CONSISTENT**.
  - `SKILL.md` Step 5/Step 6 reference `status` + `engagement_required_for` ↔ `schemas/output.json` Stakeholder defines both. **CONSISTENT**.
  - `SKILL.md` Output Contract references `schemas/output.json` ↔ schema unchanged in structural shape. **CONSISTENT**.
  - `SKILL.md` Step 12 references FM-14 ↔ FM-14 named in Step 12 prose (no separate table row needed; same pattern as FM-12 self-reference). **CONSISTENT**.
- **Preserved E1 content**: All other reference files, all test/assertion files, all other procedure steps unchanged. No good content removed.

---

## Readiness for Phase F (Quality Gate)

The skill is now production-ready for the F phase quality gate. The single P1 from E3 (schema serialization contract) is resolved; the two P2 ambiguity gaps and the P2 stakeholder enumeration gap are resolved. Remaining E3 items are P3 polish that can be deferred to a future v1.1.0 minor without affecting handoff quality.

**Verdict**: ba-elicit-from-raw v1.0.1 — ready for Phase F.
