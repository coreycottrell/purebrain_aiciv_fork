#!/usr/bin/env python3
"""Guard (ticket 3631, P23): fails if the template tells a newborn a universal "6GB RAM" container.
The cap is set per AI and is measured from the cgroup at wake; see .claude/CLAUDE.md "Your Container - Know Your Limits".
Intended home: tools/test_no_universal_ram_claim.py in each template repo (pyonair-aiciv-fork, aiciv-fork-template, yourAICIV-fork-template, -m3).
Run from the template root: python3 tools/test_no_universal_ram_claim.py   (exit 0 = ok, 1 = regression)"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAD = [("Docker container has 6GB RAM", ".claude/CLAUDE.md"),
       ("RAM: 6GB. Period.", "docs/civ-operations-manual.md")]
MUST = [("set per AI by your operator", ".claude/CLAUDE.md"), ("memory.max", ".claude/CLAUDE.md")]
bad = 0
for text, rel in BAD:
    p = os.path.join(ROOT, rel)
    if os.path.exists(p) and text in open(p, encoding="utf-8", errors="replace").read():
        print(f"FAIL: {rel} contains the stale universal claim: {text!r}"); bad += 1
for text, rel in MUST:
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p) or text not in open(p, encoding="utf-8", errors="replace").read():
        print(f"FAIL: {rel} is missing required text: {text!r}"); bad += 1
print("ok" if not bad else f"{bad} failure(s)")
sys.exit(1 if bad else 0)
