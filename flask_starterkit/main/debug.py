"""Outbound debugger attach, for PyCharm.

VSCode and Cursor attach *into* the container (the `debugger` target): debugpy
listens on 5678 and the IDE connects to it. PyCharm cannot use that shape
together with Werkzeug's reloader. pydevd propagates a session into the reload
child by injecting a connect-back address that only exists inside the parent
process, so the first hot reload leaves the child dialling a dead port:

    Could not connect to 127.0.0.1: 56679
    ConnectionRefusedError: [Errno 111] Connection refused

pydevd treats that as fatal, the child exits 1, and the container goes with it.

Reversing the direction sidesteps it entirely: PyCharm runs a Python Debug
Server that listens on the host, and each reload child connects out to it on
its own. Nothing has to survive the restart, so nothing breaks when one happens.
"""

import logging
import os

logger = logging.getLogger(__name__)

_TRUTHY = {"1", "true", "yes", "on"}

DEFAULT_HOST = "host.docker.internal"
DEFAULT_PORT = 5678


def attach_pycharm_debugger() -> bool:
    """Connect to a PyCharm Python Debug Server, if this process should.

    Enabled by `$PYCHARM_DEBUG`; the host and port are overridable with
    `$PYCHARM_DEBUG_HOST` and `$PYCHARM_DEBUG_PORT`. Failure to reach the IDE is
    a warning rather than an error: an unattached container should still serve.

    Returns:
        bool: True if this process is now attached to the debug server.
    """
    if os.environ.get("PYCHARM_DEBUG", "").lower() not in _TRUTHY:
        return False

    # Werkzeug's reloader runs the app in a child process and keeps the parent
    # for watching files. Attaching from the parent would hand PyCharm the one
    # process that never serves a request, and breakpoints would never hit.
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return False

    host = os.environ.get("PYCHARM_DEBUG_HOST", DEFAULT_HOST)
    port = int(os.environ.get("PYCHARM_DEBUG_PORT", DEFAULT_PORT))

    try:
        import pydevd_pycharm
    except ImportError:
        logger.warning(
            "PYCHARM_DEBUG is set but pydevd-pycharm is not installed. Use the "
            "debugger-pycharm target, or install the version matching your IDE."
        )
        return False

    # Only host/port/suspend are passed: JetBrains renamed the rest between
    # builds (stdoutToServer -> stdout_to_server), and naming them would break
    # this call on any build but the pinned one. The defaults are what we want
    # anyway -- output stays in `docker compose logs`, and subprocess patching,
    # the mechanism that breaks the reloader, stays off.
    try:
        pydevd_pycharm.settrace(
            host,
            port=port,
            # Do not freeze the app on the first traced line -- the debug server
            # is a background attach, not a breakpoint.
            suspend=False,
        )
    except (OSError, SystemExit):
        # No debug server listening, most likely. Serve undebugged rather than
        # killing a container the developer may only want to run.
        logger.warning(
            "No PyCharm debug server at %s:%s -- continuing without a debugger. "
            "Start the 'PyCharm Debug Server' run configuration first.",
            host,
            port,
        )
        return False

    logger.info("Attached to PyCharm debug server at %s:%s", host, port)
    return True
