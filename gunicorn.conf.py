"""Gunicorn settings for the production image.

Every value is overridable by environment variable so the same image can be
tuned per deployment without a rebuild.
"""

import multiprocessing
import os


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw and raw.strip() else default


bind = f"0.0.0.0:{_int_env('PORT', 5000)}"

# The usual starting point is (2 x cores) + 1. Override with WEB_CONCURRENCY --
# containers routinely see the host's core count rather than their own CPU
# limit, which otherwise spawns far more workers than the cgroup can feed.
workers = _int_env("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1)
threads = _int_env("WEB_THREADS", 1)

# Must stay below the idle timeout of any load balancer in front of this.
timeout = _int_env("WEB_TIMEOUT", 30)
graceful_timeout = _int_env("WEB_GRACEFUL_TIMEOUT", 30)
keepalive = _int_env("WEB_KEEPALIVE", 5)

# Recycle workers periodically so a slow leak never becomes an outage. The
# jitter keeps every worker from restarting on the same request.
max_requests = _int_env("WEB_MAX_REQUESTS", 1000)
max_requests_jitter = _int_env("WEB_MAX_REQUESTS_JITTER", 100)

# "-" means stdout/stderr: the container runtime collects the logs.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()

# Keep the worker temp directory in RAM. On some hosts /tmp is a slow or
# nearly-full volume, which stalls the heartbeat and gets workers killed.
worker_tmp_dir = "/dev/shm"
