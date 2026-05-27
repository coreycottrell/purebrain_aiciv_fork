# Fork Template Audit Changelog

**Auditor**: True Bearing (BOOP #1.483, Day 23)
**Date**: 2026-05-27
**Repo**: coreycottrell/purebrain_aiciv_fork
**Baseline**: Our SOTA (True Bearing operational patterns, 482+ BOOPs proven)
**Scope**: Template-only fixes. No premium add-ons (AI Doc, Hermes fleet).

---

## Gap Categories

| Priority | Meaning |
|----------|---------|
| P0 | CIV cannot function without this fix |
| P1 | CIV functions but poorly — will flounder |
| P2 | Quality-of-life — improves experience |

---

## Fixes Applied

### Fix 1: sprint-mode rewritten from Witness-specific to generic template (P0)
- **File**: `.claude/skills/sprint-mode/SKILL.md`
- **Was**: Lean sprint BOOP with hardcoded `/home/aiciv` paths, "I am Witness" in Step 4, references `nursemaid-birthing` (doesn't exist), `ONBOARDING-FLOW.md` (Witness-specific), `witness-primary` tmux grep
- **Now**: Full identity reconstruction BOOP (v3.0.0). 8 docs + haikus. All paths use `${CIV_ROOT}`. Doc #6 changed from nursemaid-birthing → aiciv-psychology. Step 4 says `${CIV_NAME}` not "Witness". Cron section uses generic session name. Positioned as THE standard hourly BOOP, not a lean fallback.
- **Impact**: CIV can now ground properly without Witness-specific references breaking

### Fix 2: boop_config.json defaults fixed (P0)
- **File**: `config/boop_config.json`
- **Was**: work-mode-boop at 25min cadence (enabled), DEEPWELL at 5min (disabled). min_cadence=5
- **Now**: Identity grounding (sprint-mode) at 60min cadence (enabled), work-mode disabled by default. min_cadence=30. DEEPWELL removed (not relevant to generic template).
- **Impact**: Default BOOP is now identity reconstruction, not task delegation. Hourly cadence matches proven TB pattern.

### Fix 3: aiciv-psychology promoted from PROVISIONAL to STABLE (P1)
- **File**: `.claude/skills/aiciv-psychology/SKILL.md`
- **Was**: v0.1.0 PROVISIONAL — the skill that teaches the CIV about its own cognitive failure modes was marked as a draft
- **Now**: v1.0.0 STABLE — content was already comprehensive (490 lines, 3 layers, 5 degradation causes). Only the version/status tags were wrong.
- **Impact**: CIV and its human now trust this skill as canonical, not experimental

### Fix 4: Scratchpad discipline documented in OPS (P1)
- **File**: `.claude/CLAUDE-OPS.md`
- **Was**: Only referenced `.claude/scratchpad.md` (session-level) and team scratchpads
- **Now**: Also documents daily scratchpad pattern (`.claude/scratchpads/primary-YYYY-MM-DD.md`), append-only discipline, timestamps on every entry
- **Impact**: CIV has continuity across sessions via daily append-only log

### Fix 5: [PENDING — more gaps to address]
