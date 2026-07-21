"""The PyCharm attach is guard-heavy and every guard has a failure it prevents.

pydevd-pycharm is not installed in the test image -- it is pinned to a single
IDE build and belongs only in the debugger target -- so these tests inject a
stand-in module. The real library's call signature is checked in CI instead,
against the image that actually has it (.github/workflows/docker-targets.yml).
"""

import sys
import types

import pytest

from flask_starterkit.main.debug import attach_pycharm_debugger


@pytest.fixture
def fake_pydevd(monkeypatch):
    """Stand in for pydevd_pycharm, recording how settrace was called."""
    module = types.ModuleType("pydevd_pycharm")
    module.calls = []

    def settrace(host, **kwargs):
        module.calls.append((host, kwargs))

    module.settrace = settrace
    monkeypatch.setitem(sys.modules, "pydevd_pycharm", module)
    return module


@pytest.fixture
def enabled(monkeypatch):
    """The environment of a reload child that should attach."""
    monkeypatch.setenv("PYCHARM_DEBUG", "1")
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")


def test_does_nothing_unless_enabled(monkeypatch, fake_pydevd):
    monkeypatch.delenv("PYCHARM_DEBUG", raising=False)
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")

    assert attach_pycharm_debugger() is False
    assert fake_pydevd.calls == []


def test_does_not_attach_from_the_reloader_parent(monkeypatch, fake_pydevd):
    """The parent only watches files. Attaching there hits no breakpoints."""
    monkeypatch.setenv("PYCHARM_DEBUG", "1")
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)

    assert attach_pycharm_debugger() is False
    assert fake_pydevd.calls == []


def test_attaches_from_the_reload_child(enabled, fake_pydevd):
    assert attach_pycharm_debugger() is True

    (host, kwargs) = fake_pydevd.calls[0]
    assert host == "host.docker.internal"
    assert kwargs["port"] == 5678
    # Suspending would freeze the app on its first traced line, before it ever
    # binds a port, which reads as a container that hangs on startup.
    assert kwargs["suspend"] is False


def test_host_and_port_are_overridable(enabled, fake_pydevd, monkeypatch):
    monkeypatch.setenv("PYCHARM_DEBUG_HOST", "172.17.0.1")
    monkeypatch.setenv("PYCHARM_DEBUG_PORT", "5999")

    assert attach_pycharm_debugger() is True

    (host, kwargs) = fake_pydevd.calls[0]
    assert host == "172.17.0.1"
    assert kwargs["port"] == 5999


def test_a_missing_debug_server_does_not_kill_the_app(enabled, fake_pydevd):
    """Serving undebugged beats exiting 1 on a container nobody is attached to."""

    def refuse(host, **kwargs):
        raise ConnectionRefusedError(111, "Connection refused")

    fake_pydevd.settrace = refuse

    assert attach_pycharm_debugger() is False


def test_pydevd_exiting_does_not_kill_the_app(enabled, fake_pydevd):
    """pydevd calls sys.exit() on some connection failures rather than raising."""

    def bail(host, **kwargs):
        raise SystemExit(1)

    fake_pydevd.settrace = bail

    assert attach_pycharm_debugger() is False


def test_missing_pydevd_is_survivable(enabled, monkeypatch):
    """PYCHARM_DEBUG set on an image without the library, e.g. the dev target."""
    monkeypatch.setitem(sys.modules, "pydevd_pycharm", None)

    assert attach_pycharm_debugger() is False
