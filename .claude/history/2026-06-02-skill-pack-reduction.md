# 2026-06-02 — Skill-pack reduction (aside)

**Skill-pack reduction (2026-06-02).** What used to be a single 113-skill gitignored, non-destructive copy of the external `treasury/*` catalog was reduced to only the skills the pipeline uses; the rest (all 8 packs, `design-time-orchestrators/`, most of `standalone/`, 13 of `squad-delivery-skills/`) plus the old `manifest.json` registry were quarantined and then deleted on 2026-06-02. They are gone from this workspace (no local copy), recoverable only from the external `treasury/` source. Nothing live referenced them.
