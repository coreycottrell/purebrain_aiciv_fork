# Kill-Sonnet Genome Fix — purebrain_aiciv_fork (2026-06-11)

**Directive (Corey)**: Minimum model floor is **opus 4.8**. Find anything that sets a model to sonnet and kill it. Detailed per-repo changelog required.

**Branch**: `sonnetkill-20260611` (NEVER main)
**Method**: `grep -rn -i sonnet` across the tree; classify every hit KILL (real model-setting routing work to sonnet) vs KEEP (avoid-instruction / search-filter / example-data / routes-away-from-sonnet prose). Iteration 3 of TB's infrastructure-VP kill-sonnet sweep (after TB's own repo + canonical fork-template @ 27757fe).

This run RECONCILED an orphaned prior incarnation (relaunch-interrupted) that had already edited 131 files on this branch, then completed the 4 misses it left.

---

## LAUNCHER (the critical main-session fix)

`tools/launch_civ_tower.sh:100`
- **before**: `tmux send-keys -t "${SESSION_NAME}" "claude --model claude-sonnet-4-6 --dangerously-skip-permissions '${CLAUDE_PROMPT}'" C-m`
- **after**:  `tmux send-keys -t "${SESSION_NAME}" "claude --model 'claude-opus-4-8[1m]' --dangerously-skip-permissions '${CLAUDE_PROMPT}'" C-m`

The `[1m]` suffix is CORRECT and PROVEN here — it is the main-session tower launcher, where `[1m]` unlocks the 1M context window. (Agent-manifest `model:` fields get plain `claude-opus-4-8`, NO `[1m]`.)

---

## FILES CHANGED: 135 total

- **1** launcher (`tools/launch_civ_tower.sh`) → `claude-opus-4-8[1m]`
- **~118** agent manifests (`.claude/agents/*.md`, `.claude/agents/dev-team/*.md`) frontmatter `model: sonnet` / `model: claude-sonnet-4-5-20250929` / `model: claude-sonnet-4-6` → `model: claude-opus-4-8`; plus mirrored prose `**Model**:` headers.
- **~16** docs/skills/spawn-templates carrying copyable sonnet model-settings:
  - `.claude/CLAUDE-OPS.md`, `.claude/CLAUDE-TEAMS.md` — agent()/Task() spawn examples `model="sonnet"` → `claude-opus-4-8`
  - `.claude/hooks/session_start.py` — printed spawn instruction `model='sonnet'` → `claude-opus-4-8`
  - `.claude/agents/README.md`, `agent-architect.md`, `spawner.md`, `skills-master.md` — agent-creation default-model templates → `claude-opus-4-8`
  - skills: `agent-creation`, `agent-teams-orchestration`, `bluesky-blog-thread`, `daily-blog`, `evening-capture`, `primary-spine`, `team-launch`, `verify-publish`, `fork-readiness-test` — model-settings + live-launch flags → opus-4-8
  - `.claude/team-leads/README.md`, `.claude/team-leads/dev/README.md` — spawn-pattern `model="sonnet"` → `claude-opus-4-8`

### 4 misses left by the orphaned run, completed this iteration:
1. `.claude/skills/fork-readiness-test/SKILL.md:34` — fork-launch instruction `--model claude-sonnet-4-6` → `--model claude-opus-4-8` (a live launch flag fleet is told to use → would boot a real fork on sonnet).
2. `.claude/skills/fork-readiness-test/SKILL.md:593` — same fork-launch flag in remediation block → opus-4-8.
3. `.claude/skills/agent-creation/SKILL.md:124` — prose default `` `claude-sonnet-4-20250514` (default) `` → `` `claude-opus-4-8` (default) `` (the orphaned run fixed the 3 `model:` frontmatter defaults in this file but missed this prose default line).
4. `.claude/skills/daily-blog/SKILL.md:111` — stale comment `# Use sonnet for quality writing` on an already-opus model line → `# Opus 4.8 (minimum floor) for quality writing` (cosmetic; the model-setting was already opus).

---

## KEPT (residual "sonnet" strings that are CORRECT — not model-settings)

1. `.claude/skills/cc-conversation/SKILL.md:294` — `"model": "claude-sonnet-4-5-20250929"` inside **example JSONL log data** (a captured past-session transcript record shown as documentation). Not a config that routes work. KEEP.
2. `.claude/skills/cc-conversation/SKILL.md:159` — `model_filter="claude-sonnet-4-5"` — a **search filter** over historical logs, not a model selection. KEEP.
3. `.claude/team-leads/tgim/manifest.md:82` — "Team leads = Opus ONLY. **NEVER Sonnet**." An **avoid-instruction**. Changing it would invert its meaning. KEEP.
4. `.claude/skills/deep-research/SKILL.md:182` — "Opus/Sonnet hang on complex WebFetch chains, use haiku" — **routes AWAY from sonnet**, descriptive. KEEP.
5. `.claude/skills/deep-research/SKILL.md:405` — same routes-away guidance. KEEP.

---

## GROUND-TRUTH VERIFICATION

`grep -rIn -E "model.{0,3}(:|=).{0,5}['\"]?(claude-)?sonnet"` → **1 hit**, which is the cc-conversation:294 example-log-data KEEP above. **0 real active model-settings route work to sonnet.**

Cardinal applied: verify-not-trust (read each residual's context before classifying) + match-scope-to-metric (did NOT blind grep-replace — kept 5 avoid/filter/example/away hits, killed 2 live fork-launch flags + 1 prose default the orphaned pass missed). Local fork ≠ template: this fork had the SAME launcher-line trap and the SAME fork-readiness launch-flag traps, but the orphaned incarnation's pass missed the fork-readiness + agent-creation-prose defaults — caught here.
