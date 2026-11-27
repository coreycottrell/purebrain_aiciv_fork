"""Guard test for tools/measure_at_wake_resources.py (script authored by Forge, Pyonair; ticket 3631).
Run: python3 -m unittest tools/test_measure_at_wake_resources.py  (from repo root)"""
import os, subprocess, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_at_wake_resources as m

GB = m.GiB


class T(unittest.TestCase):
    def test_builtin_self_test_passes(self):
        self.assertEqual(m._self_test(), 0)

    def test_unreadable_never_reports_uncapped(self):
        cap, unc, src = m.parse_cap(None, None)
        self.assertEqual((cap, unc, src), (None, False, "UNREADABLE"))
        v, rc = m.build_verdict(cap, unc, src, None, None, 128 * GB, "init")
        self.assertEqual(rc, 2)
        self.assertFalse(v["uncapped_cgroup"])

    def test_12gb_cap_on_128gb_host_flags_free_m_trap(self):
        v, rc = m.build_verdict(12 * GB, False, "cgroup-v2 memory.max", 8 * GB, 12 * GB, 128 * GB, "entrypoint.sh")
        self.assertEqual(rc, 1)
        self.assertTrue(any("FREE-M TRAP" in w for w in v["warnings"]))

    def test_script_only_reads_no_network_or_subprocess(self):
        src = open(m.__file__.replace(".pyc", ".py")).read()
        for banned in ("import socket", "import subprocess", "urllib", "requests", "os.system", "open(path, 'w'", "os.remove"):
            self.assertNotIn(banned, src)

    def test_cli_runs_with_expected_exit_codes(self):
        rc = subprocess.run([sys.executable, "-B", m.__file__, "--json"], capture_output=True).returncode
        self.assertIn(rc, (0, 1, 2))


if __name__ == "__main__":
    unittest.main()
