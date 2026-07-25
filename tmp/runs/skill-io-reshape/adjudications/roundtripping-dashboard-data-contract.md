# Adjudication — roundtripping-dashboard-data-contract (tooling, no pipeline stage)

Source: codex/roundtripping-dashboard-data-contract.md · exit=0. Verified: extract.py main() writes
--out directly (bundle_io.write_text, no collision guard — `--out` = the HTML would destroy the bundle;
no atomic write), and the SKILL's own validation checklist instructs a DESTRUCTIVE drift check ("re-run
extract.py … deep-equal to the edited dashboard-data.json" — the re-run OVERWRITES the edits);
build.py --verify ALREADY exists (arg line 158) — the safe check was available and undocumented;
events/templates key check is one-way only (⊆ stage ids, build.py:92-97) while the real data satisfies
the full equality (27 stages / 27 events / 27 templates — reverse check safe to enforce); json_only
renders as `new Set(...)` (render_module) → duplicates silently dropped on round-trip; build.py:165
plain json.load (last-writer-wins dupes).

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT-MODIFIED** | Guards: realpath(--out) != realpath(--html) (extract) and realpath(--data) != realpath(--html) (build), both exit 2; ALL writes temp-sibling + atomic os.replace (nonzero exit leaves files unchanged). Checklist rewritten: drift check = `build.py --verify` (already existed), or extract to a SEPARATE candidate path. MODIFIED on "explicit replacement intent": the default checked-in dashboard-data.json stays overwritable (that IS the documented flow; git is the safety net — documented), but an existing NON-default --out requires --force (deterministic, no interactive gate). |
| F2 | major | **ACCEPT** | input_schema + output_schema both → schemas/dashboard-data.schema.json (it governs build input AND extract output); mode-aware Input/Output contract prose (extract/check/verify/build); states: HTML output has byte-level invariants not a JSON schema; NO boundary schema, YAML pin, adapter payload, injected keys, or audit_id. |
| F3 | major | **ACCEPT** | $SKILL_DIR command shape throughout; working dir stays repo root so default dashboard paths resolve. |
| F4 | major | **ACCEPT** | Trust contract: extraction EXECUTES the DATA module (vm.runInContext is not a security boundary) — only the known workspace-owned bundle is accepted; external/untrusted bundle = stop condition; bounded subprocess timeout (120s) + documented non-termination failure. |
| F5 | major | **ACCEPT** | PII/secret precondition: build embeds every value, extract reproduces every value — both outputs inherit source sensitivity; neither script sanitizes; suspected sensitive content ⇒ stop for a redacted input. |
| F6 | major | **ACCEPT** | Reverse-set checks: events and templates keys must EQUAL the stages[].id set (missing entries reported); real data satisfies 27/27/27; Input contract states one event + one template entry per stage. |
| F7 | major | **ACCEPT** | Output contract states "Validation passed" proves schema+key+offline rules ONLY (not workflow parity, skill/version existence, path existence, readiness); procedure adds a read-only comparison vs workflows/delivery-pipeline.yaml + workflows/skills/ for changed stage/test/skillmap entries + a drawio handoff / stale-artifact notice for delivery-pipeline-flow.drawio (archive stays excluded). |
| F8 | major | **ACCEPT** | json_only uniqueItems:true (Set conversion silently deduped — round-trip deep-equal was a false promise on duplicate input). |
| F9 | major | **ACCEPT** | Strict loader: object_pairs_hook dupe rejection + parse_constant NaN/Infinity rejection, clean nonzero diagnostic, no writes (same guard as the other two tooling renderers). |
| F10 | minor | **ACCEPT** | Schema descriptions for top-level + abbreviated fields (p/f/cov/src/cite/caps/reviewDoc); minLength 1 where blank is undefined; empty-string sentinels documented. |

Version: nested `metadata:` flattened → top-level `version: 1.1.0` (minor: additive guards + checks;
CLI compatible — new --force only gates a previously-destructive path). No pins/boundary/corpus.
