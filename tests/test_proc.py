"""Tests for handshakelab.util.proc — subprocess helpers."""

from __future__ import annotations

import subprocess

import pytest

from handshakelab.util.proc import CommandResult, format_cmd, run, which


def test_command_result_ok_true():
    r = CommandResult(argv=["x"], returncode=0, stdout="ok", stderr="")
    assert r.ok is True


def test_command_result_ok_false():
    r = CommandResult(argv=["x"], returncode=1, stdout="", stderr="bad")
    assert r.ok is False


def test_which_finds_true():
    """which() finds a real binary on PATH."""
    # python3 should always be on PATH
    result = which("python3")
    assert result is not None
    assert "python" in result.lower()


def test_which_returns_none_for_missing():
    """which() returns None for a binary that doesn't exist."""
    assert which("definitely_not_a_real_binary_xyz123") is None


def test_run_captures_stdout():
    """run() captures stdout of a successful command."""
    result = run(["echo", "hello"])
    assert result.ok
    assert "hello" in result.stdout
    assert result.returncode == 0


def test_run_captures_stderr():
    """run() captures stderr of a failing command."""
    result = run(["false"])
    assert not result.ok
    assert result.returncode != 0


def test_run_check_raises_on_failure():
    """run(check=True) raises CalledProcessError on non-zero return."""
    with pytest.raises(subprocess.CalledProcessError):
        run(["false"], check=True)


def test_run_check_passes_on_success():
    """run(check=True) does not raise on success."""
    result = run(["echo", "ok"], check=True)
    assert result.ok


def test_format_cmd_quotes_args():
    """format_cmd uses shlex.quote for safe shell representation."""
    assert format_cmd(["echo", "hello world"]) == "echo 'hello world'"
    assert format_cmd(["ls", "-l"]) == "ls -l"
    assert format_cmd(["echo", "it's"]) == "echo 'it'\"'\"'s'"


def test_run_with_cwd(tmp_path):
    """run() passes cwd to subprocess."""
    result = run(["pwd"], cwd=tmp_path)
    assert result.ok
    # pwd returns the cwd path; should be the tmp dir
    assert str(tmp_path) in result.stdout
