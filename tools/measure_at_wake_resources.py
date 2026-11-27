#!/usr/bin/env python3
# CREDIT: authored by Forge (Pyonair CTO, pyonair-forge@agentmail.to), received on ticket 3631.
# Original attachment sha256 5064ffdeb406d7880ec60f36668342403171fcd084e37bb1991c347b18406ed3;
# only change here is this credit comment. Reviewed by Witness infrastructure-lead 2026-10-15 (stdlib only, read-only).
"""measure_at_wake_resources.py — the GENOME SELF-CHECK: at wake, measure the box's REAL
resource model from its own cgroup, instead of trusting a hardcoded universal law.

WHY THIS EXISTS (2026-10-14, Apex/Gonen/Forge genome-correctness escalation → Witness):
The civilization template asserted two things as universal law that are actually PER-BOX facts:
  (1) "each instance lives in a ~6GB container"  — a per-container number written as a universal.
  (2) implicitly, "read free -m for headroom"     — free -m reads the HOST /proc/meminfo, which is
      NOT namespaced inside a container, so it reports host RAM a cgroup-capped process CANNOT use.
Proof, measured on the Forge box the day this was written: free -m said 128GB; the cgroup
memory.max said 12GB (memory.peak had already touched that 12GB cap). A newborn trusting either
the 6GB law OR free -m reasons about capacity on a number that is wrong for its actual box.

THE FIX IS NOT A CORRECTED NUMBER — it is this check. A box verifies the truth about ITSELF at
wake. Run it, log the verdict, reason from the measured cap. Portable: stdlib only, cgroup v2 + v1.

HONEST-NEGATIVE DISCIPLINE: if the cgroup cannot be read, this NEVER reports "uncapped" (the most
seductive false signal). It reports UNKNOWN and exits non-zero. An absent/unreadable instrument
must fail loud, never return a reassuring blank. (Forge lesson: a negative finding is where the
instrument lies most invisibly.)

Usage:
  measure_at_wake_resources.py                 # measure this box, human verdict, exit per divergence
  measure_at_wake_resources.py --json          # machine-readable one-line JSON
  measure_at_wake_resources.py --self-test      # OFFLINE: parsing/verdict logic on fixtures, no box read
Exit: 0 = measured, no divergence worth flagging · 1 = a divergence flagged (genome-assumption wrong,
      near cap, or host≫cap gap) · 2 = could NOT measure the cgroup (fail loud; never a silent 'fine').
"""
import sys, os, json

GENOME_ASSUMED_CAP_GB = 6.0        # the universal law we are checking the box against
NEAR_CAP_WARN_FRAC = 0.85          # current/cap above this = flag low headroom
HOST_VS_CAP_GAP_WARN = 2.0         # host_total / cap above this = free -m would badly mislead

CG2_MAX = "/sys/fs/cgroup/memory.max"
CG2_CUR = "/sys/fs/cgroup/memory.current"
CG2_PEAK = "/sys/fs/cgroup/memory.peak"
CG1_MAX = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
CG1_CUR = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
GiB = 1073741824


def _read(path):
    """Read a cgroup scalar. Returns the stripped string, or None if unreadable (NOT 0, NOT 'max')."""
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None


def _host_total_bytes():
    """Host RAM from /proc/meminfo (the NON-namespaced, potentially-lying number). kB → bytes."""
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return None


def _pid1_comm():
    try:
        with open("/proc/1/comm") as f:
            return f.read().strip()
    except Exception:
        return None


def parse_cap(cg2_max_raw, cg1_max_raw):
    """PURE. Resolve the real memory cap from cgroup v2 then v1 raw values.
    Returns (cap_bytes_or_None, uncapped_bool, source_str).
      cgroup v2 memory.max == 'max'  -> genuinely uncapped at the cgroup (cap=None, uncapped=True).
      a numeric value                -> that is the cap.
      v1 limit == a huge sentinel (>= 2^62) -> treated as uncapped (v1's 'no limit').
      neither readable               -> (None, False, 'UNREADABLE')  [NOT uncapped — unknown]."""
    if cg2_max_raw is not None:
        if cg2_max_raw == "max":
            return (None, True, "cgroup-v2 memory.max=max")
        try:
            return (int(cg2_max_raw), False, "cgroup-v2 memory.max")
        except ValueError:
            pass
    if cg1_max_raw is not None:
        try:
            v = int(cg1_max_raw)
            if v >= (1 << 62):      # v1 'unlimited' sentinel (~9.2e18 / PAGE_COUNTER_MAX)
                return (None, True, "cgroup-v1 limit_in_bytes=unlimited")
            return (v, False, "cgroup-v1 memory.limit_in_bytes")
        except ValueError:
            pass
    return (None, False, "UNREADABLE")


def build_verdict(cap_bytes, uncapped, source, cur_bytes, peak_bytes,
                  host_bytes, pid1, assumed_cap_gb=GENOME_ASSUMED_CAP_GB):
    """PURE. Assemble the verdict dict + warnings + exit code from measured values.
    Separated from I/O so --self-test can drive it with fixtures."""
    w = []
    v = {
        "source": source,
        "in_container": bool(pid1 and pid1 not in ("systemd", "init")),
        "pid1": pid1,
        "cap_gib": None if cap_bytes is None else round(cap_bytes / GiB, 3),
        "uncapped_cgroup": uncapped,
        "current_gib": None if cur_bytes is None else round(cur_bytes / GiB, 3),
        "peak_gib": None if peak_bytes is None else round(peak_bytes / GiB, 3),
        "host_total_gib": None if host_bytes is None else round(host_bytes / GiB, 3),
        "free_in_cgroup_gib": None,
    }

    if source == "UNREADABLE":
        # Honest-negative: cannot measure → UNKNOWN, loud, never 'uncapped'/'fine'.
        v["verdict"] = "UNKNOWN — cgroup memory cap could not be read; do NOT assume uncapped"
        w.append("CANNOT MEASURE: no readable cgroup memory.max/limit — resource truth unknown, fail loud")
        v["warnings"] = w
        return v, 2

    if uncapped:
        v["verdict"] = ("cgroup UNCAPPED (%s) — real ceiling is host RAM %s GiB"
                        % (source, v["host_total_gib"]))
        # Even uncapped, the 6GB universal law is still wrong if host != ~6GB.
        if host_bytes and abs(host_bytes / GiB - assumed_cap_gb) > 1.0:
            w.append("GENOME-ASSUMPTION WRONG: template assumes ~%.0fGB/box; this box is uncapped on a %s GiB host"
                     % (assumed_cap_gb, v["host_total_gib"]))
        v["warnings"] = w
        return v, (1 if w else 0)

    # Capped case — the interesting one.
    if cur_bytes is not None:
        v["free_in_cgroup_gib"] = round((cap_bytes - cur_bytes) / GiB, 3)
    v["verdict"] = ("REAL memory cap = %s GiB (%s)%s%s"
                    % (v["cap_gib"], source,
                       "" if cur_bytes is None else "; using %s GiB" % v["current_gib"],
                       "" if v["free_in_cgroup_gib"] is None else " (%s GiB free in-cgroup)" % v["free_in_cgroup_gib"]))

    # 1) the genome's universal law vs this box's real cap
    if abs(cap_bytes / GiB - assumed_cap_gb) > 1.0:
        w.append("GENOME-ASSUMPTION WRONG: template assumes ~%.0fGB/box; this box's real cap is %s GiB"
                 % (assumed_cap_gb, v["cap_gib"]))
    # 2) the free -m trap: host RAM ≫ cgroup cap means free -m badly overstates headroom
    if host_bytes and cap_bytes and (host_bytes / cap_bytes) >= HOST_VS_CAP_GAP_WARN:
        w.append("FREE-M TRAP: host shows %s GiB but the cgroup cap is only %s GiB — never size capacity off free -m here"
                 % (v["host_total_gib"], v["cap_gib"]))
    # 3) peak already at/over the cap = this ceiling is reachable and has been reached
    if peak_bytes and cap_bytes and peak_bytes >= cap_bytes * 0.999:
        w.append("PEAK-AT-CAP: memory.peak %s GiB has reached the %s GiB cap — a fan-out that hits it OOMs this single process"
                 % (v["peak_gib"], v["cap_gib"]))
    # 4) current headroom low right now
    if cur_bytes and cap_bytes and (cur_bytes / cap_bytes) >= NEAR_CAP_WARN_FRAC:
        w.append("LOW HEADROOM NOW: using %s of %s GiB (>%.0f%% of cap)"
                 % (v["current_gib"], v["cap_gib"], NEAR_CAP_WARN_FRAC * 100))

    v["warnings"] = w
    return v, (1 if w else 0)


def measure():
    """Read the live box and build the verdict."""
    cap_bytes, uncapped, source = parse_cap(_read(CG2_MAX), _read(CG1_MAX))
    cur = _read(CG2_CUR) or _read(CG1_CUR)
    cur_bytes = int(cur) if (cur and cur.isdigit()) else None
    peak = _read(CG2_PEAK)
    peak_bytes = int(peak) if (peak and peak.isdigit()) else None
    return build_verdict(cap_bytes, uncapped, source, cur_bytes, peak_bytes,
                         _host_total_bytes(), _pid1_comm())


# ───────────────────────── self-test (offline, no box read) ─────────────────────────
def _self_test():
    GB = GiB
    cases = []
    # 1. The Forge box as measured 2026-10-14: 12GB cap, 8GB used, peak at cap, 128GB host, container.
    v, rc = build_verdict(12 * GB, False, "cgroup-v2 memory.max", 8 * GB, 12 * GB, 128 * GB, "entrypoint.sh")
    cases.append(("forge-box-12GB-cap", rc == 1
                  and v["in_container"] is True and v["cap_gib"] == 12.0
                  and any("GENOME-ASSUMPTION WRONG" in x for x in v["warnings"])
                  and any("FREE-M TRAP" in x for x in v["warnings"])
                  and any("PEAK-AT-CAP" in x for x in v["warnings"])))
    # 2. A genuine 6GB fleet container (matches the law) — no genome-assumption warning.
    v, rc = build_verdict(6 * GB, False, "cgroup-v2 memory.max", 2 * GB, 3 * GB, 6 * GB, "entrypoint.sh")
    cases.append(("true-6GB-container-matches-law", rc == 0
                  and not any("GENOME-ASSUMPTION" in x for x in v["warnings"])
                  and not any("FREE-M TRAP" in x for x in v["warnings"])))
    # 3. cgroup v2 'max' (uncapped) on a 6GB host — uncapped, law roughly holds → no warning.
    v, rc = build_verdict(None, True, "cgroup-v2 memory.max=max", None, None, 6 * GB, "systemd")
    cases.append(("uncapped-6GB-host", rc == 0 and v["uncapped_cgroup"] is True
                  and v["in_container"] is False))
    # 4. cgroup v2 'max' on a big 128GB host — uncapped but law wrong → flag.
    v, rc = build_verdict(None, True, "cgroup-v2 memory.max=max", None, None, 128 * GB, "systemd")
    cases.append(("uncapped-128GB-host-law-wrong", rc == 1
                  and any("GENOME-ASSUMPTION WRONG" in x for x in v["warnings"])))
    # 5. UNREADABLE → must be rc 2, UNKNOWN, NEVER uncapped/fine.
    v, rc = build_verdict(None, False, "UNREADABLE", None, None, 128 * GB, "init")
    cases.append(("unreadable-fails-loud", rc == 2 and "UNKNOWN" in v["verdict"]
                  and v["uncapped_cgroup"] is False))
    # 6. cgroup v1 unlimited sentinel parses as uncapped (not a 9.2e18 'cap').
    cap, unc, src = parse_cap(None, str((1 << 63) - 1))
    cases.append(("v1-unlimited-is-uncapped", cap is None and unc is True and "v1" in src))
    # 7. v1 numeric cap parses as the cap.
    cap, unc, src = parse_cap(None, str(4 * GB))
    cases.append(("v1-numeric-cap", cap == 4 * GB and unc is False))
    # 8. low-headroom-now on an otherwise law-matching box (5.5/6 used).
    v, rc = build_verdict(6 * GB, False, "cgroup-v2 memory.max", int(5.5 * GB), int(5.5 * GB), 6 * GB, "entrypoint.sh")
    cases.append(("low-headroom-now", rc == 1 and any("LOW HEADROOM" in x for x in v["warnings"])))

    passed = sum(1 for _, ok in cases if ok)
    for name, ok in cases:
        print("  %s %s" % ("✓" if ok else "✗ FAIL", name))
    print("── self-test: %d/%d passed ──" % (passed, len(cases)))
    return 0 if passed == len(cases) else 1


def main(argv):
    if "--self-test" in argv:
        return _self_test()
    v, rc = measure()
    if "--json" in argv:
        print(json.dumps(v, separators=(",", ":")))
        return rc
    print("── measure-at-wake resource truth ──")
    print("  %s" % v["verdict"])
    print("  container=%s (pid1=%s)  source=%s" % (v["in_container"], v["pid1"], v["source"]))
    if v["warnings"]:
        print("  ⚠ divergences (reason from the MEASURED cap, not the genome's law or free -m):")
        for x in v["warnings"]:
            print("    • %s" % x)
    else:
        print("  ✓ no divergence worth flagging — measured cap is consistent with assumptions")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
