"""TG bridge orphan-bare-shell fix — real ISOLATED tmux server (TMUX unset,
TMUX_TMPDIR in tmp). Bare '{civ}-primary' bash + stale marker must never
receive owner text; it is queued and delivered once a Claude pane exists."""
import asyncio, importlib, os, subprocess, sys, time
from pathlib import Path
from unittest import mock
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def T(*a):
    return subprocess.run(["tmux", *a], capture_output=True, text=True)


def cap(sess):
    r = T("capture-pane", "-p", "-t", f"={sess}:")
    assert r.returncode == 0, r.stderr
    return r.stdout


def wait(pred, t=8):
    end = time.time() + t
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.1)
    return False


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.delenv("TMUX", raising=False)
    monkeypatch.setenv("TMUX_TMPDIR", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    assert T("list-sessions").stdout.strip() == ""
    tg = importlib.import_module("telegram_unified")
    monkeypatch.setattr(tg, "CIV_ID", "testciv")
    monkeypatch.setattr(tg, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(tg, "PENDING_INJECTIONS_FILE", tmp_path / "pending.jsonl")
    recv = tmp_path / "recv.txt"
    fake = tmp_path / "claude"
    fake.write_text(f"#!/bin/bash\nexec -a claude cat >> '{recv}'\n"); fake.chmod(0o755)
    T("new-session", "-d", "-s", "testciv-primary", "bash --norc --noprofile")
    (tmp_path / ".current_session").write_text("testciv-primary")  # stale marker
    wait(lambda: "bash" in T("list-panes", "-a", "-F", "#{pane_current_command}").stdout)
    bot = tg.TelegramBot.__new__(tg.TelegramBot)
    bot.tmux_session = bot.tmux_pane = bot._claude_pane = None
    bot.use_gateway = False
    bot._gateway_registered = False
    from collections import deque
    bot._recent_injections = deque(maxlen=50)
    bot.sent = []

    async def _send(text, *a, **k):
        bot.sent.append(text)
    bot._send_message = _send
    yield tg, bot, fake, recv
    T("kill-server")


def test_bare_shell_only_is_never_detected(env):
    tg, bot, fake, recv = env
    assert bot._detect_acg_session() is None


def test_queued_not_typed_into_bash_then_delivered(env):
    tg, bot, fake, recv = env
    asyncio.run(bot._inject_and_respond("ORPHAN-hello", "owner", 1, "private"))
    time.sleep(0.5)
    assert "ORPHAN-hello" not in cap("testciv-primary")
    assert "command not found" not in cap("testciv-primary")
    assert tg.AI_STARTING_NOTICE in bot.sent
    assert "ORPHAN-hello" in tg.PENDING_INJECTIONS_FILE.read_text()
    # Claude comes up in the timestamped session
    T("new-session", "-d", "-s", "testciv-primary-20260922-000000", str(fake))
    assert wait(lambda: "claude" in T("list-panes", "-a", "-F", "#{pane_current_command}").stdout)
    n = asyncio.run(bot._drain_pending_injections())
    assert n == 1
    assert wait(lambda: recv.exists() and "ORPHAN-hello" in recv.read_text())
    assert tg.PENDING_INJECTIONS_FILE.read_text().strip() == ""
    assert "ORPHAN-hello" not in cap("testciv-primary")


def test_claude_present_delivers_to_claude_pane(env):
    tg, bot, fake, recv = env
    T("new-session", "-d", "-s", "testciv-primary-20260922-000000", str(fake))
    assert wait(lambda: "claude" in T("list-panes", "-a", "-F", "#{pane_current_command}").stdout)
    assert bot._detect_acg_session() == "testciv-primary-20260922-000000"
    asyncio.run(bot._inject_and_respond("DIRECT-hello", "owner", 1, "private"))
    assert wait(lambda: recv.exists() and "DIRECT-hello" in recv.read_text())
    assert "DIRECT-hello" not in cap("testciv-primary")
