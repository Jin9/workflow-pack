# Accessibility testing — WCAG AA, automation limits, manual review

Grounded in the ResearchVault: an accessibility gate scans a built front end
against a declared WCAG conformance level and emits a pass/fail verdict, but
**automation is partial**: rule-based engines decide only the machine-decidable
criteria and flag the rest for a human. The skill consumes the standard rather
than authoring criteria. See
`[[literature/platform-devops/platform-reliability-scorecard]]`.

## Bind the standard

Use `wcag_level` (default AA) as the conformance target. This skill does not
author success criteria; it measures against WCAG 2.1. Scope is the built FE
(pages/components), not the design.

## Automation catches only part of WCAG

Automated engines such as axe-core (Deque) catch on average about **57%** of WCAG
issues; they cannot judge subjective criteria (is alt text meaningful, is focus
order logical, does the page make sense keyboard-only). They return "incomplete"
results that mean *needs human review*, not *pass*. So a clean automated run is
**not** WCAG AA conformance — it is the floor.

## Engine plus browser driver

Run axe-core inside a real browser via a driver (Playwright a11y) so the DOM is
the rendered, scripted state. Read `wcag_violations[]` (rule, impact, WCAG
reference) and the engine's "incomplete" list from the report — never assert a
result the engine did not produce.

## Needs-review and manual checks

Map "incomplete" results to `needs_review[]` and the required human steps to
`manual_checks` — e.g. keyboard-only traversal, visible focus order, meaningful
alternative text, contrast on images-of-text, screen-reader announcement of
dynamic regions. These are surfaced, never silently passed.

## Gate policy (banking default)

- `ERROR` — the build could not render or the engine could not run.
- `FAIL` — any AA automated violation, OR unresolved `needs_review` items
  (uncertain manual items → human follow-up in regulated contexts).
- `PASS` — zero AA automated violations, with `manual_checks` still listed for the
  human reviewer; the verdict never claims full WCAG coverage.

## Boundary

Reports only — a named human resolves the manual checks and signs off; FE fixes
go to the FE fixer. UI/token/layout design is `generate-ux-pack`. The skill runs
in a sandbox and never edits the UI.

## Sources

Vault: [[literature/platform-devops/platform-reliability-scorecard|Platform reliability scorecard]] · [[literature/observability-reliability/slo-sli-design|SLO/SLI design]]

Web: deque.com (axe-core catches ~57% of WCAG issues and flags incomplete items for manual review) · w3.org (WAI / ACT rules) · playwright.dev (accessibility testing)
