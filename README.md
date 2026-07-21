# 🌶️ flask-docker-starterkit

A boilerplate providing a complete, production-shaped setup to start a new `flask` project.

## 🚀 Quick start

```bash
cp .env.example .env
docker compose build
docker compose up app
```

The project will be available at `http://127.0.0.1:5000`, with a liveness probe at
`http://127.0.0.1:5000/health`.

> **On macOS**, ControlCenter's AirPlay Receiver already listens on port 5000, so the
> command above fails with `address already in use`. Pick another host port:
>
> ```bash
> APP_PORT=5001 docker compose up app
> ```
>
> Only the host side changes — the container still listens on 5000.

## 🐛 Run with the VSCode debugger

- Run `docker compose up debugger`; `debugpy` waits for the debugger to attach before
  starting the `flask` server
- Go to the `Run and Debug` section
- Select the `▶️` button with the option `Python: Remote Attach`

Hot reload stays active while attached: debugpy follows Werkzeug's reload child, so
breakpoints survive a restart.

The `remoteRoot` in [.vscode/launch.json](.vscode/launch.json) must match `WORKDIR` in
the [Dockerfile](Dockerfile) (`/app`). If they drift apart, breakpoints show up greyed
out and never bind.

Happy debugging! 🚀

## 🐛 Run with the PyCharm debugger

PyCharm needs the connection the other way round — the IDE listens, the container
dials it:

- Run the **`PyCharm Debug Server`** configuration first (it listens on `5678`)
- Then `docker compose up debugger-pycharm`

Hot reload stays active, because each reload child attaches on its own.

**`pydevd-pycharm` must match your PyCharm build.** It ships one release per build and
refuses to talk to any other. Read yours from `Help > About` — `PY-261.26222.68` means
build `261.26222.68` — and if it differs from the default in the
[Dockerfile](Dockerfile):

```bash
PYCHARM_BUILD=<your-build> docker compose build debugger-pycharm
```

> [!NOTE]
> The `debugger` target above does **not** work with PyCharm. `pydevd` propagates a
> debug session into Werkzeug's reload child by injecting a connect-back address that
> only exists inside the parent process, so the first hot reload ends in
> `ConnectionRefusedError` and the container exits `1`. That is what this separate
> target exists to avoid.

## 🧪 Run tests

```bash
docker compose up --exit-code-from test-runner test-runner
```

`--exit-code-from` is required for a failing test to produce a non-zero exit code.
`--abort-on-container-exit` stops the containers but always exits `0`.

The source is bind-mounted, so your current code is always what runs — no rebuild
needed between edits.

**After changing `requirements.txt` or `requirements-dev.txt`, rebuild:** dependencies
are installed into the image rather than mounted, so a new package shows up as
`ModuleNotFoundError` until you run

```bash
docker compose build test-runner
```

## 🎨 Lint and format

```bash
pip install -r requirements-dev.txt
ruff check .
ruff format .
```

## 🏭 Run the production image

The production target runs **gunicorn**, not the Flask development server:

```bash
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))') \
  docker compose -f docker-compose.prod.yml up --build
```

The app refuses to start in production without a `SECRET_KEY` of at least 32 characters.
That is deliberate — booting without one silently breaks sessions and CSRF protection.

Gunicorn is tuned via environment variables (`WEB_CONCURRENCY`, `WEB_TIMEOUT`,
`WEB_THREADS`, `WEB_MAX_REQUESTS`, `PORT`) so one image serves every environment.
See [gunicorn.conf.py](gunicorn.conf.py).

### Behind a reverse proxy

Set `TRUST_PROXY_HOPS` to the number of proxies in front of the app to enable
`ProxyFix`. Leave it at `0` otherwise: trusting `X-Forwarded-*` headers when nothing
strips them lets any client spoof its own source IP and scheme.

## ⚙️ Configuration

`create_app()` takes a config object, so environments differ by class rather than by
scattered `if` statements:

```python
from flask_starterkit.main.config import create_app

app = create_app("testing")          # by name
app = create_app(ProductionConfig()) # or by instance
```

`APP_ENV` selects the default (`development` | `testing` | `production`). Config is read
from the environment when the object is instantiated, not at import time, so import order
never matters. Production config validates itself and fails fast.

## 🕵️ Environment variables

Copy `.env.example` to `.env`. `.env` is gitignored **and** excluded from Docker images —
secrets must never end up in an image layer.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Which config class to load |
| `SECRET_KEY` | *(generated in dev)* | Session signing. Required in production |
| `FLASK_DEBUG` | `1` in dev | Boolean `1`/`0`. Never `1` in production |
| `LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `LOG_FORMAT` | `plain` (`json` in prod) | Log rendering |
| `TRUST_PROXY_HOPS` | `0` | Reverse-proxy hops to trust |
| `WEB_CONCURRENCY` | `(2 × cores) + 1` | Gunicorn workers |

## 🗓️ Features

- Up and running `flask` server, containerized
- Application factory with per-environment config that fails fast
- Gunicorn in production, non-root, read-only rootfs, digest-pinned base image
- `/health` liveness endpoint wired to a Docker `HEALTHCHECK`
- JSON error responses instead of HTML tracebacks
- Structured (JSON) logging to stdout
- Unit tests with coverage, plus a production-image smoke test in CI
- Linting and formatting with `ruff`
- VSCode & PyCharm debugger with hot reload
- Automated dependency updates via Dependabot

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
