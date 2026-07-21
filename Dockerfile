# syntax=docker/dockerfile:1
#
# Multi-stage build. Targets:
#   development -- flask dev server, for `docker compose up app`
#   debugger    -- debugpy, waits for VSCode to attach
#   debugger-pycharm -- pydevd, dials out to a PyCharm debug server
#   test        -- pytest, includes dev-only dependencies
#   production  -- gunicorn, runtime dependencies only
#
# The base image is pinned by digest so a rebuild six months from now produces
# the same image. Dependabot keeps the digest current (see .github/dependabot.yml).
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Apply Debian security patches published since this base image was built. The
# digest pin fixes the starting point; without this the image carries whatever
# CVEs were open on build day until upstream republishes the tag.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create the unprivileged user up front: it is a stable layer, so it caches.
RUN adduser --uid 5678 --disabled-password --gecos "" appuser

# Dependencies before source, so editing a .py file does not reinstall the world.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . /app

EXPOSE 5000

# Shared by every target. Uses urllib because the slim image has no curl.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).status == 200 else 1)"]


# --- Development: hot reload, source bind-mounted over /app by compose --------
FROM base AS development
ENV APP_ENV=development FLASK_DEBUG=1
USER appuser
CMD ["flask", "--app", "run:app", "run", "--host", "0.0.0.0", "--port", "5000"]


# --- Debugger: identical, but waits for the VSCode debugger to attach ---------
FROM base AS debugger
# PYDEVD_DISABLE_FILE_VALIDATION silences a startup notice that is expected here.
ENV APP_ENV=development FLASK_DEBUG=1 PYDEVD_DISABLE_FILE_VALIDATION=1
RUN python -m pip install --no-cache-dir debugpy==1.8.21
USER appuser
EXPOSE 5678
# -Xfrozen_modules=off: on Python 3.11+ frozen stdlib modules make debugpy miss
# breakpoints intermittently. The reloader stays enabled -- debugpy propagates the
# session into Werkzeug's reload child, so breakpoints survive a restart.
CMD ["python", "-Xfrozen_modules=off", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", \
     "-m", "flask", "--app", "run:app", "run", "--host", "0.0.0.0", "--port", "5000"]


# --- Debugger (PyCharm): dials out to a listening IDE instead of being dialled -
# The stage above cannot serve PyCharm: pydevd propagates a session into the
# reload child by injecting an address that only exists in the parent process,
# so the first hot reload exits 1 and takes the container down. Here the app
# connects out to a PyCharm "Python Debug Server" and each reload child attaches
# for itself -- see flask_starterkit/main/debug.py.
FROM base AS debugger-pycharm
ENV APP_ENV=development FLASK_DEBUG=1 PYDEVD_DISABLE_FILE_VALIDATION=1 PYCHARM_DEBUG=1
# pydevd-pycharm ships one release per IDE build and refuses to talk to any
# other. Read your build from Help > About (PY-261.26222.68 -> 261.26222.68) and
# override on mismatch:  docker compose build --build-arg PYCHARM_BUILD=... debugger-pycharm
ARG PYCHARM_BUILD=261.26222.68
RUN python -m pip install --no-cache-dir pydevd-pycharm==${PYCHARM_BUILD}
USER appuser
# No EXPOSE 5678: the connection is outbound, to the IDE.
CMD ["python", "-Xfrozen_modules=off", "-m", "flask", "--app", "run:app", "run", "--host", "0.0.0.0", "--port", "5000"]


# --- Test: dev dependencies live here and nowhere else ------------------------
FROM base AS test
ENV APP_ENV=testing
# /app is owned by root and appuser cannot write to it -- deliberate, so the app
# can never rewrite its own code. That means pytest's scratch files need to go
# somewhere else, or coverage dies with "unable to open database file" (which is
# an INTERNALERROR, not a test failure, and is easy to mistake for a pass).
ENV COVERAGE_FILE=/tmp/.coverage \
    PYTEST_ADDOPTS="-p no:cacheprovider"
COPY requirements-dev.txt ./
RUN python -m pip install --no-cache-dir -r requirements-dev.txt
USER appuser
CMD ["python", "-m", "pytest"]


# --- Production: gunicorn, no dev dependencies, non-root ----------------------
FROM base AS production
ENV APP_ENV=production
USER appuser
CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
