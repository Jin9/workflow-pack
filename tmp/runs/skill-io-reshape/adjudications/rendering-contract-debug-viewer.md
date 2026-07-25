# Adjudication — rendering-contract-debug-viewer (tooling, no pipeline stage)

Source: codex/rendering-contract-debug-viewer.md · exit=0. Verified: main() writes `--output` with no
realpath(input)!=realpath(output) guard and non-atomic open("w") (script:284-286 — truncation on
mid-write failure confirmed); check_offline() blanks __DATA__/__TITLE__/__SRC__ before scanning
(script:241 — forbidden tokens in contract data reach the saved file unscanned); OK/WARN/ERRV sets
(script:118-120) lack promote/approve/rollback/hold/conditional; audit chip falls back to
processing_metadata.audit_id as if equivalent (script:166); `--theme light` emits no attr and stored
localStorage wins over the CLI choice (script:244, 183); "View source" is JSON.stringify re-serialization
(script:178).

| F# | Sev | Verdict | Rationale / modified form |
|----|-----|---------|---------------------------|
| F1 | blocker | **ACCEPT** | Real destroy-the-input path. Guard realpath(out)!=realpath(in) → exit 2 before any open; write temp sibling + os.replace (atomic; failed render can't truncate an existing viewer). |
| F2 | blocker | **ACCEPT** | Aligns the viewer with the house offline gate (which scans FINAL bytes). Unicode-escape forbidden lexemes inside the JSON/title blobs (render-identical, byte-deterministic), strip `<>` from src label (already done), then check_offline(final_html) before write; exit 3 = final HTML violates offline contract. |
| F3 | major | **ACCEPT** | House-v2 prose Input/Output contract sections for a schema-less tooling skill: required one readable UTF-8 JSON file; optional output_path/title/theme; stop conditions enumerated; states explicitly NO skill schema, NO pipeline validation, NO idempotency_key injection; output = exactly one HTML + one stdout line. |
| F4 | major | **ACCEPT** | Workspace PII rule made a contract precondition: source must already be redacted; viewer embeds every value so the HTML inherits source sensitivity; stop + request redacted copy, never mutate source. Doc-only. |
| F5 | major | **ACCEPT** | Trigger overlap with rendering-delivery-review-console is real ("run folder" appears in both descriptions). Remove unqualified run-folder trigger; directory allowed only as discovery aid for ONE identified artifact; zero/multiple candidates → stop and ask. |
| F6 | major | **ACCEPT** | Classifier vocab synced to the REAL boundary enums (verified at apply vs workflows/schemas/*.json): +promote/approve/handed_off green · +conditional/hold/loop_back/human-queue/pass-with-caveats/reroute amber · +rollback/hard-fail/ERROR red; recommendation badged only for recognized decision enums; contract-field-map.md synced. |
| F7 | major | **ACCEPT** | audit_id chip reserved for top-level data.audit_id (fleet standard now requires it); processing_metadata.audit_id stays visible at its path, not promoted; doc: viewer never creates/validates audit ids; artifact id ≠ engine attempt id. |
| F8 | major | **ACCEPT** | Command examples rewritten to `python3 "$SKILL_DIR/scripts/render_contract_viewer.py"` (resolve from SKILL.md dir); data paths stay repo-root-relative — both examples executable as written. |
| F9 | minor | **ACCEPT** | Real mismatch: CLI `light` is indistinguishable from `auto` and stored state always wins. Emit FORCE_THEME const; explicit light/dark skips the localStorage read; auto keeps stored-then-matchMedia. Doc: browser pref affects presentation only, never saved bytes. |
| F10 | minor | **ACCEPT-MODIFIED** | Button renamed "View normalized JSON" + transform documented + determinism basis = (input bytes, basename, title, theme, renderer version). MODIFIED: also reject duplicate keys (object_pairs_hook) and NaN/Infinity (parse_constant) with exit 2 — fail-closed doctrine; these never legitimately appear in schema-validated contracts. Original-bytes source view NOT adopted (would double the embedded payload for a debug tool). |

Version: nested `metadata:` flattened (skillify flat rule) → top-level `version: 1.1.0` (minor: additive
guards + classifier/theme/labels; CLI surface unchanged). No pins, no boundary, no corpus.
