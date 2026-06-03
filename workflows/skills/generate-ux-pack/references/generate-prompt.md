# Prompt — Generate `ux-design-{idem8}/` Pack from UX Sources

> **Use this prompt** with Claude Code (or any capable LLM) to produce a full v1.1 UX-design intake pack from a UX team's drop.
> **Inputs needed**: bundled prototype HTML (read for structural reference only), Frontend Spec markdown (the authoritative content source), BA brief directory (epics + stories).
> **Output**: the `ux-design-{idem8}/` directory tree per the v1.1 TL scaffold pack §8 contract.

---

## Prompt to paste

```
You are producing a v1.1 UX-design intake pack — the structured drop the
TL stage consumes downstream. Your inputs are:

1. A frontend prototype HTML (may be Bundler-packed; treat as reference
   only — humans validate against the running prototype, you do not
   extract style data from bundled code).
2. A Frontend Spec markdown file containing brand system, routes,
   components, business logic, recommended stack.
3. A BA brief directory (output-{idem8}/) with epic and story files.
   This is your authoritative source for what stories exist.

Produce the following directory tree at `ux-design-{idem8}/` where
`{idem8}` is the first 8 chars of a UUID v4 (generate one).

```
ux-design-{idem8}/
├── README.md
├── tokens.json
├── route-map.md
├── component-inventory.md
├── microcopy.json
├── screen-states.md
├── form-validation.md
├── responsive-spec.md
├── accessibility-spec.md
├── flows/
│   ├── customer-onboarding.md
│   ├── customer-checkout.md
│   ├── customer-order-tracking.md
│   └── payment-failure-recovery.md
└── screens/
    └── EPIC-{NAME}/        ← One folder per customer-facing BA epic
        ├── EPIC.md
        └── stories/
            └── STORY-N-{slug}.md   ← One file per customer-facing BA story
```

## Per-file rules

### README.md
Frontmatter (YAML):
- artifact_type: ux-design-intake
- project_id: from BA brief frontmatter
- brief_id: from BA brief frontmatter
- idempotency_key: new UUID v4
- created_at: ISO-8601 timestamp
- source_artifacts: list of input paths
- ux_team_contact: TBD-fill-in
- prototype_url: TBD-fill-in or path to HTML
- figma_url: TBD-fill-in
- maturity_level: 0|1|2|3 (per v1.1 §4 audit triage)
- status: draft | ready-for-audit
Content: brief intro, navigation, list of derived vs TBD artifacts.

### tokens.json
Format: W3C Design Tokens draft. Required categories:
- color.brand (primary at minimum; secondary if spec defines)
- color.text (primary, secondary, tertiary, optionally inverse)
- color.background (page, surface, divider)
- color.accent (every accent color from spec)
- color.semantic (success, warning, error, info — derive if not in spec)
- spacing (page-padding, page-padding-compact, card-gap, section-gap,
  plus a base scale like xs/sm/md/lg/xl when derivable)
- typography (font-family-default, font-family-alternates, scale-100
  through scale-900, font-weight-regular/medium/semibold/bold)
- radius (card, pill, button — exact values from spec)
- shadow (when spec mentions; otherwise omit)
- motion.duration (TBD if not in spec; emit as TBD-pending-UX-input)

Every brand color MUST have $extensions.contrast with:
- vs-white: computed ratio (use WCAG formula)
- vs-text-primary: computed ratio
- wcagAA: boolean (≥4.5:1 normal text, ≥3:1 large text or UI)
- wcagAAA: boolean (≥7:1 normal, ≥4.5:1 large)
- usage_note: where this color may/may-not be used at body-text size

Compute contrasts; do not leave as TBD.

### route-map.md
Markdown table with columns: Route | Screen | Auth | Tab? | Implements BA stories | Notes
- Every route from Frontend Spec §3 gets a row.
- Implements column references real BA story IDs (e.g., EPIC-CHECKOUT-1).
- Stories without a UX route AND BA stories without UX coverage both
  surface as findings at the bottom of the file under "## Gaps".
- For internal/non-customer routes (admin, tweaks panel) mark
  "Implements: n/a (internal)" — do not invent BA stories.

### component-inventory.md
One section per atom and composite from Frontend Spec §6. Each section:
- Component name
- Purpose (one sentence)
- Variants (e.g., Btn: brand, dark, light, ghost)
- States (idle, hover, active, focused, disabled, loading)
- Accessibility annotations:
  - ARIA role (implicit or explicit)
  - Keyboard interaction (Tab, Enter, Space, arrows, Escape — what
    each does)
  - Screen-reader label requirement
  - Focus indicator description
- Props/inputs structure (from spec's prop list)
- Used by screens: (cross-reference list)
- Banking-grade flags: contains-PII (yes/no), customer-facing (yes/no)

For icons: enumerate from spec's Icon name list. Each icon needs an
aria-label. If spec doesn't say, mark TBD-needs-UX-input.

### microcopy.json
Skeleton with keys derived from screens. Pattern:
```json
{
  "$schema": "design-tokens/microcopy",
  "version": "1.0.0",
  "locales": ["th", "en"],
  "strings": {
    "common.action.add_to_cart": {
      "th": "TBD-extract-from-prototype",
      "en": "Add to cart",
      "context": "Primary action on product detail page",
      "tipping_off_clean": true,
      "max_length": 24,
      "uses": ["detail.product-detail"]
    }
  }
}
```

For every customer-facing string a screen needs, emit a key. Default
the `en` value if obvious; mark `th` as TBD-extract-from-prototype
since the HTML is bundled and you cannot read it.

Required string categories at minimum:
- common.action.* (add_to_cart, buy_now, checkout, save, cancel,
  confirm, back, close, retry, edit, delete)
- common.status.* (loading, empty, error, success, no_results)
- nav.tab.* (home, search, cart, orders, profile)
- screen.{route}.* (title, subtitle, empty-state, error-state)
- field.{name}.* (label, placeholder, error-{rule})
- order.status.* (PENDING_PAYMENT, PAID, PAYMENT_FAILED, etc. — one
  per state in spec §5)
- error.* (network, server, validation, payment-declined,
  payment-timeout)

Tipping-off scan: every emitted `en` value runs against the financial-
domain forbidden list (flagged, suspicious, AML, sanctions, PEP, EDD,
SAR, adverse media, fraud-flagged, watchlist). Any match = a finding
in README.md§gaps.

### screen-states.md
One section per route from route-map.md. Each section enumerates:
- Idle/default state — what's shown when the screen loads with data
- Empty state — what's shown with zero data (empty cart, no orders,
  no search results)
- Loading state — skeleton, spinner, disabled affordance
- Error state — connection error, server error, validation error
- Success state — confirmation, transition
- Auth-required state (if route requires auth and user is logged out)

Each state references microcopy keys. Each state describes:
- Visual: what components render
- Behavior: what user can do
- Accessibility: announcement strategy for state transitions

### form-validation.md
One section per form across all screens. Each form:
- Form name + location (route)
- Submit action (microcopy key)
- Per field: name, type, required (y/n), validation rules
  (client-side regex / server-side check), error message (microcopy
  key), submit-blocking (y/n)
- Thai-locale rules where applicable:
  - Phone: ^0[0-9]{9}$ format (Thai mobile)
  - Postal code: ^[0-9]{5}$
  - National ID: 13-digit + checksum
  - Address: sub-district / district / province structure

Banking-grade carve-outs:
- Email field: no clipboard-copy block (PII but customer-owned)
- Password field: server-side only (never client-side regex on
  password rules — leaks policy)
- Payment fields: out of scope (PSP-hosted), but reference Frontend
  Spec §5 mock payment behavior

### responsive-spec.md
- Primary target: 390×844 (iPhone 14)
- Breakpoints: declare what's responsive (probably "mobile only —
  390×844 to 430×932"); explicit "desktop not supported in MVP" if
  that's the intent per Frontend Spec
- Per breakpoint: what reflows, what hides, what shows
- Touch target sizes (minimum 44×44 per WCAG)
- Safe-area handling (iOS notch, Android nav bar)
- Webview vs standalone-browser detection (if relevant)

### accessibility-spec.md
- WCAG target level (AA per Frontend Spec)
- Color contrast: every text-on-background combination from tokens.json
  with computed ratio + WCAG pass/fail (cross-reference tokens.json)
- Focus order per screen (Tab key sequence)
- Keyboard shortcuts (Escape closes modals, Enter submits forms, etc.)
- Screen reader announcements: state changes, modal opens, form errors,
  cart updates
- Icon ARIA labels: cross-reference component-inventory.md
- Touch target verification: ≥44×44px (cross-reference responsive-spec)
- Reduced-motion support: animations gracefully degrade

### flows/*.md
Each flow file:
- Frontmatter with flow_id, related_epics, related_stories
- Mermaid sequenceDiagram showing the full user journey across screens
- Screen-by-screen narrative: what user sees, what they do, what
  happens next
- Edge cases: what if step N fails, what if user backs out
- Cross-reference to per-story screens/EPIC-{NAME}/stories/...md

Required flows (derive from BA epics):
- customer-onboarding.md — registration → login → first session
- customer-checkout.md — browse → add to cart → checkout → payment
  success
- customer-order-tracking.md — order list → detail → review
- payment-failure-recovery.md — payment fails/expires → retry/cancel

Add others if BA brief has additional major customer journeys (e.g.,
account-management, address-management).

### screens/EPIC-{NAME}/
Mirror the BA brief's customer-facing epic structure. NOT every BA epic
gets a UX folder — only customer-facing ones. Admin-facing or
governance epics (EPIC-GOVERN typically) skip.

Per epic folder:
- EPIC.md with: epic context, related routes, stakeholder note,
  customer-journey-position (where in the broader flow this epic
  appears)
- stories/STORY-N-{slug}.md per BA story:
  - Frontmatter: ux_story_id, ba_story_id (cross-reference),
    related_route, screen_states_ref, microcopy_keys_used
  - Layout description (Mermaid flowchart or text)
  - State-by-state behavior cross-referencing screen-states.md
  - Microcopy keys used (cross-reference microcopy.json)
  - Component references (cross-reference component-inventory.md)
  - Edge cases specific to this story
  - Accessibility notes specific to this story
  - Open questions for this story

## Quality rules

1. **No invented PII.** Example values in microcopy must look fake:
   - Email: customer+test@shoppilot.test (not real domain)
   - Phone: 081-234-5678 (clearly example)
   - Names: "ลูกค้าตัวอย่าง" / "Test Customer" (clearly fake)

2. **Bilingual handling.** Frontend Spec is Thai-primary. For every
   `en` string, leave a `th` key as TBD-extract-from-prototype unless
   the spec contains the actual Thai string verbatim.

3. **Tipping-off discipline.** Run vocabulary scan on every emitted
   string. If you emit a forbidden phrase, you've broken the contract.

4. **WCAG honesty.** Compute color contrasts with the actual WCAG
   formula. Don't claim AA pass without the math. If a token
   combination fails AA, mark it failed in tokens.json AND surface as
   a finding in README.md.

5. **BA cross-reference accuracy.** Every BA story ID you reference
   must exist in the BA brief. Verify before emitting. Do not invent
   story IDs.

6. **TBD discipline.** When you don't have the data, emit `TBD-<what's
   needed>-<who-fills>` (e.g., `TBD-extract-from-prototype-by-frontend-lead`,
   `TBD-needs-UX-input`, `TBD-pending-BA-OQ-14`). Never silently invent.

7. **Cross-reference integrity.** Every microcopy key referenced in
   screen-states/form-validation/accessibility must exist in
   microcopy.json. Every component referenced must exist in
   component-inventory.md. Every route must appear in route-map.md.

8. **Banking-grade alignment.** Frontend Spec says "no localStorage
   for auth tokens" implicitly via stack recommendation. Surface this
   in accessibility-spec.md or a security-spec.md if not present.

## Output discipline

- Write actual files to disk at the paths above. Do NOT produce a
  single mega-document with all content inline.
- After writing all files, produce a summary in chat listing: files
  created, gaps surfaced, BA stories without UX coverage, UX routes
  without BA stories.
- Do NOT modify the input files (HTML, spec MD, BA brief).
- The pack is the output. Quality > completeness — partial pack with
  honest TBDs beats fabricated complete pack.
```

---

## How to use this prompt

1. **Place inputs in known paths**:
   - Bundled prototype HTML at `inputs/prototype.html`
   - Frontend Spec at `inputs/frontend-spec.md`
   - BA brief at `inputs/ba-brief/output-{idem8}/`

2. **Run Claude Code** with the prompt above, attaching or referencing
   the three input paths.

3. **Review the output**:
   - Open README.md first → confirm maturity level + status
   - Check route-map.md for coverage gaps
   - Open microcopy.json → confirm TBD count is honest
   - Open tokens.json → confirm contrast computations are present

4. **UX team fills TBDs**:
   - Extract Thai strings from running prototype → microcopy.json
   - Add Figma URLs to README
   - Resolve any UX-specific TBDs

5. **Re-run** if input changes, or hand to TL stage.

---

## Limitations to flag to the team

- Bundled HTML means actual Thai strings, exact pixel measurements,
  and runtime behavior are NOT extracted. Humans validate against
  the running prototype.
- Microcopy is keys-with-TBD-values, not finished translations.
- Figma URLs and contact info are placeholders until UX team fills.
- Computed contrasts assume the colors as written in spec; if the
  prototype uses different values at runtime, those drift goes
  undetected by this prompt.
- WCAG AA contrast computation is mechanical; AAA judgments and
  context-sensitive accessibility (e.g., "is this color combination
  appropriate for a financial UI") still need human review.

The output is a **starting point for the UX team to refine**, not a
finished spec. Treat the first run as the audit baseline.
