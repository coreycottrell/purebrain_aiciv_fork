---
name: team-launch
description: "RETIRED-IN-PLACE (2026-07-26): the TeamCreate / Task(team_name) / TeamDelete + tmux-pane spawn mechanism described here is OBE; use paneless Workflow agents (see workflows/). Kept only for the still-binding disciplines: mandatory skills, critical-thinking, rate-limit stagger, summaries-only."
version: 1.0.0
validated: 2026-02-19
---

# Team Launch — Definitive Protocol

## 🟥 RETIRED-IN-PLACE (2026-07-26) — READ THIS FIRST

**The TeamCreate → `Task(team_name)` → TeamDelete spawn *mechanism* taught below is RETIRED (OBE).** It described each team lead as a separate Claude instance in its own tmux pane, supervised by reading that pane. That is no longer how leads run. Do NOT follow the spawn, supervise-by-pane or shutdown-by-pane steps below.

**The live pattern is the PANELESS Workflow agent**: leads run as in-process background workflow agents. There is no tmux pane, no team to delete, nothing to shut down by pane. Supervise by the lead's structured return and run record. **Supervising a pane that does not exist fails quiet and reports healthy** — that is why this banner is first.

**STILL BINDING regardless of spawn mechanism:**
- Mandatory skill loading per vertical (leads load their domain skills every spawn).
- Critical-thinking + scientific method for all diagnosis.
- The rate-limit stagger: launch concurrent agents in batches, not all at once. Bursts have caused day-long rate-limit bans.
- Only summaries reach the podium (the context firewall).
- Memory budget: concurrent agents share ONE container's memory cap. Measure it (`/sys/fs/cgroup/memory.max`, `memory.current`) before wide fan-out.

---


> Empirically validated 2026-02-19. Haiku test confirmed full cycle works.

---

## Key Facts (Do Not Contradict These)

| Fact | Truth |
|------|-------|
| What launches real separate Claude instances? | `Task(team_name=X, name=Y)` — team_name is REQUIRED |
| What does `TeamCreate` do? | Creates team coordination files + makes Primary @main |
| `Task()` without `team_name`? | In-process subagent — floods output back to Primary's context |
| `TeamDelete` after empty team? | ✅ SAFE — just cleans up JSON metadata files, Primary keeps running |
| `TeamDelete` while members active? | ❌ CRASH — state corruption, kills Primary |

---

## The Full Cycle (Validated)

### Step 1: Get on the Podium

```python
TeamCreate("session-YYYYMMDD")
# Primary = @main
# Creates ~/.claude/teams/session-YYYYMMDD/config.json
```

One team per session. Do this once at session start.

---

### Step 2: Spawn Team Leads (Real Separate Instances)

```python
# Read the full template first
template = Read(".claude/team-leads/{vertical}/manifest.md")

# Spawn as named teammate — THIS is what creates real separate Claude instances
Task(
    team_name="session-YYYYMMDD",   # ← REQUIRED for real instance
    name="{vertical}-lead",          # ← identity, appears as pane name
    subagent_type="general-purpose",
    prompt=template + "\n## Objective\n" + task,
    model="sonnet",
    run_in_background=True
)
```

**Multiple leads in parallel — always ask "what else can run now?"**

```python
# One message, multiple Task calls = true parallelism
Task(team_name=..., name="fleet-lead",   prompt=fleet_prompt,   run_in_background=True)
Task(team_name=..., name="gateway-lead", prompt=gateway_prompt, run_in_background=True)
Task(team_name=..., name="infra-lead",   prompt=infra_prompt,   run_in_background=True)
```

---

### Step 3: Receive Work

Team leads communicate via `SendMessage(type="message", recipient="main", ...)`.

Messages land at: `~/.claude/teams/{team-name}/inboxes/main.json`

**Read summaries only. Never pull full specialist output into Primary's context.**

---

### Step 4: Graceful Shutdown (When Work Complete)

```python
# Shutdown all team leads in parallel
SendMessage(type="shutdown_request", recipient="fleet-lead",   content="Work complete.")
SendMessage(type="shutdown_request", recipient="gateway-lead", content="Work complete.")
SendMessage(type="shutdown_request", recipient="infra-lead",   content="Work complete.")

# Wait for ALL to approve — their tmux panes close
```

---

### Step 5: Clean Up

```python
# ONLY after ALL team leads have approved shutdown
TeamDelete()
# → "Cleaned up directories and worktrees for team X"
# → Primary continues running normally
```

---

## The Anti-Pattern That Caused the Crash

```
❌ WRONG (caused crash):
TeamCreate → spawn leads → leads still working → TeamDelete → CRASH

✅ RIGHT:
TeamCreate → spawn leads → leads work → ALL shutdown approved → TeamDelete → clean
```

The crash was `TeamDelete` called while team leads were still active members.
Not `TeamDelete` itself — the TIMING.

---

## Supervision (Without Screenshots)

```bash
# Find panes
tmux list-panes -a -F "#{pane_id} #{pane_title} #{pane_pid}"

# Check status (last 30 lines — usually enough)
tmux capture-pane -t %{id} -p -S -30
```

Healthy: tool calls in progress, memory writes, "Sending completion to Primary..."
Red flags: nothing for 2+ min, repeated identical lines, waiting for approval

---

## Team Lead Specialist Delegation

Team leads delegate to specialists via plain `Task()` — **no `team_name` parameter**:

```python
# Inside fleet-lead's process:
Task(subagent_type="general-purpose", prompt="...", run_in_background=True)
# Specialist output returns to fleet-lead's 200K context window
# fleet-lead synthesizes → sends summary to Primary
```

**Team leads CANNOT create sub-teams.** System enforces "one team per leader" — a team lead is already a member of Primary's team and cannot create another. Confirmed via Test C 2026-02-19.

Team leads use plain Task() specialists. Primary uses TeamCreate + Task(team_name).

---

## Quick Reference

```
Primary
  TeamCreate("session-YYYYMMDD")       ← one time, session start
  Task(team_name=..., name="X-lead")   ← real instances, parallel
  [receive SendMessage summaries]
  SendMessage(shutdown_request) × N    ← all leads in parallel
  [wait for all approvals]
  TeamDelete()                          ← safe, Primary survives
```

---

*Validated: 2026-02-19 — haiku test confirmed full cycle end-to-end*
*Primary survived TeamDelete after empty team. Model confirmed.*
