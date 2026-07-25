# Theme tokens — squad-delivery dashboard palette

These are the visual tokens the renderer bakes into every viewer (light default + a `.dark` class on
`<html>` for dark; `--theme auto` lets the OS choose and the toggle override). Extracted from
`squad-delivery-dashboard.standalone.html`. **The script `scripts/render_contract_viewer.py` is the
source of truth** — this file documents it so a maintainer can keep them in sync (do not duplicate logic).

## Surfaces / text / border (CSS variables)

| Token | Light | Dark |
|---|---|---|
| `--bg` (page) | `#f6f7f9` | `#0c0f15` |
| `--surface` (card) | `#ffffff` | `#13171f` |
| `--surface2` | `#f3f5f8` | `#171c26` |
| `--ink` (primary text) | `#13171d` | `#eef2f8` |
| `--ink2` (headings) | `#2c333d` | `#cfd6e1` |
| `--muted` | `#5b6675` | `#9aa6b6` |
| `--faint` | `#8a94a3` | `#697485` |
| `--border` | `#e4e8ee` | `#252c38` |
| `--border2` | `#d3dae3` | `#323b49` |
| `--accent` | `#2563eb` | `#5b8cff` |
| `--code-bg` / `--code-fg` | `#eef1f6` / `#1f4c87` | `#171f2c` / `#9dc1f0` |

## Status (badges: ok / warn / err / info) — color · bg · border

| Status | Light | Dark |
|---|---|---|
| ok | `#15803d` · `#e8f6ed` · `#bbe3c8` | `#5ed18a` · `#0f2a1b` · `#1d4d33` |
| warn | `#a4570a` · `#fcf1df` · `#f1d4a0` | `#e6b15e` · `#2c2110` · `#553f1b` |
| err | `#c62828` · `#fcebec` · `#f2c1c4` | `#f08a8f` · `#2c1416` · `#5a262a` |
| info | `#1763c6` · `#e9f2fd` · `#bdd8f6` | `#74b1f5` · `#10233c` · `#234a73` |
| slate | `#445268` · `#eef1f5` · `#d3dae2` | `#9fadc2` · `#1a212c` · `#333d4c` |

## Severity dots (high / medium / low)

| Sev | Light | Dark |
|---|---|---|
| high (P1) | `#dc2626` | `#f0726f` |
| medium (P2) | `#d97706` | `#e3a44e` |
| low (P3) | `#64748b` | `#8b97a8` |

## Tier (T1 / T2 / T3) — color · bg · border

| Tier | Light | Dark |
|---|---|---|
| T1 | `#3b5bdb` · `#e8ecfb` · `#c2cdf4` | `#8098f0` · `#161d3a` · `#2c3a73` |
| T2 | `#0284c7` · `#e1f3fb` · `#aadcf1` | `#52b4e8` · `#0c2536` · `#1d4a68` |
| T3 | `#0d9488` · `#e0f5f2` · `#a6e0d8` | `#52c4b6` · `#0b2b27` · `#1b5249` |

## Fonts / shape

- Sans: `'Geist', 'Hanken Grotesk', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`
- Mono: `'Geist Mono', 'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace`
- Radius: `12px` (cards), `8px`/`6px` (controls/badges). Shadow: `0 1px 3px rgba(16,24,40,.07)` (light) /
  `0 1px 3px rgba(0,0,0,.5)` (dark).
- Geist is **not** bundled (that would require font files / `@font-face` URLs and break offline); the
  system fallback stack keeps the look close while staying fully offline.
