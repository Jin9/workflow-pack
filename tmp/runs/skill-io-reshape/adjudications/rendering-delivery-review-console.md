# Adjudication — rendering-delivery-review-console (tooling, no pipeline stage)

Source: codex/rendering-delivery-review-console.md · exit=0. Verified: build() writes out_path directly
(no collision guard vs consumed artifacts, no atomic replace, no marker check — `-o INDEX.json` would
destroy the run record); gate rollup tracks worst-of ONLY over gates WITH evidence → 1 green + 11 pending
renders unqualified GREEN; _discover_gate_files checks gates/ first (canonical-first already true) but
the recursive fallback silently first-picks among duplicate filenames; audit_index is built from rendered
section envelopes ("skill": payload.skill or sec.kind → renderer kinds like `design` leak as skill
names); read_json collapses missing AND malformed to None; S1/S1.5/S2 menus return (None, []) with no
pending card while S0/S3–S7 use _pending_menu; drawio transcode failures `continue` silently;
generated_from embeds the absolute path when run_dir is absolute.

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT-MODIFIED** | Guards: output must end .html; realpath(out) must differ from every file READ during assembly (tracked set) and lie outside the skill dir; temp-sibling + atomic os.replace. MODIFIED: the script is non-interactive — instead of "require confirmation", refuse (exit 2) to overwrite an existing file that is neither the default RUN_DIR/delivery-review.html nor carries the console marker string; no prompt path. |
| F2 | major | **ACCEPT** | House-v2 prose Input/Output contracts: required = one existing readable run dir; optional output_path (default RUN_DIR/delivery-review.html); stage artifacts optional; stop conditions enumerated; states NO skill/boundary schema, NO YAML pin, NO adapter payload/injected keys; output = exactly one HTML + stdout summary. |
| F3 | major | **ACCEPT** | audit_index rebuilt from AUTHORITATIVE artifacts (fixed map: S1b INDEX + S4a/S4b artifacts+reviews + S4c qa-plan + S5 evidence + S6 receipt + 12 gates), stage-dir → bare producer skill name from a static table mirroring the YAML; envelope scan kept as fallback; status optional; doc: IDs are copied verbatim producer-stamped provenance, never generated here, never equated with events.jsonl attempt ids. |
| F4 | major | **ACCEPT** | `present` defined as "recognized artifact parsed as a JSON object" (never schema validity — only `validate-run --strict` establishes conformance); absent vs unreadable-or-malformed distinguished (read_json returns a tagged miss); S1/S1.5/S2/S2.5 get honest pending cards like S0/S3–S7; failed drawio transcodes surface as a visible diagnostic card instead of a silent skip. |
| F5 | major | **ACCEPT** | Board payload += expected_count:12, evidence_count, missing_gates[], evidence_complete; rollup renders INCOMPLETE whenever evidence_count < 12 (worst-observed value preserved alongside for continuity); unqualified GREEN only with complete evidence. Output contract states the board is presentation-only — proves neither a release barrier nor production readiness. Corpus (12/12) stays GREEN + complete. |
| F6 | major | **ACCEPT** | Input-contract precondition: artifacts pre-redacted/secret-free (placeholder form PII:REDACTED:CLASS=...); suspected sensitive values ⇒ stop + request redacted copy; doc: bare_host() strips URL schemes only, the HTML inherits embedded-story/gate sensitivity, the renderer is NOT a sanitizer. |
| F7 | major | **ACCEPT** | Commands rewritten to `python3 "$SKILL_DIR/scripts/build_review_console.py" "$RUN_DIR"`; RUN_DIR/output resolve from the working directory. |
| F8 | minor | **ACCEPT** | Renderer envelope {renderer_skill, renderer_version, pack_schema_version} added to run header; run.schemaVersion/produced_by documented as S1b-INDEX-sourced; generated_from normalized to the run id (basename) — never an absolute workstation path; determinism defined over (normalized source bytes, options, template, renderer version). |
| F9 | minor | **ACCEPT** | Canonical gates/<file> declared authoritative (already scanned first); recursive fallback only when canonical absent; >1 distinct fallback candidates ⇒ exit 2 with an ambiguity diagnostic naming the candidates (fail closed — ambiguous gate evidence is a run-integrity problem), never silent first-pick. |

Version: nested `metadata:` flattened → top-level `version: 1.2.0` (minor: additive payload fields +
guards; CLI unchanged). No pins/boundary/corpus-schema impact. The checked-in ShopPilot
delivery-review.html is REGENERATED in the same commit so the corpus artifact matches the new renderer.
