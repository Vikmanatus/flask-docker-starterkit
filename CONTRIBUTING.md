# Contributing

Thanks for your interest in this project! 🌶️

This repository is a **starterkit** — a small, deliberately minimal boilerplate. That
shapes what does and does not get merged, so please read this before opening a PR.

## Before you open a pull request

**Please open an issue first** to describe what you want to change and why. This repo
regularly receives unsolicited pull requests from training courses and bootcamps that use
it as a practice target. Those are closed without review. An issue takes two minutes and
tells us you are not one of them.

## What is likely to be accepted

- Bug fixes, with a test that fails before the fix and passes after
- Security fixes
- Dependency updates that keep CI green
- Documentation corrections

## What is unlikely to be accepted

- **Adding your own CI/CD, SonarQube, or deployment configuration.** Several past PRs
  hardcoded the contributor's own DockerHub account, SonarCloud project key, or EC2
  secrets. Deployment is the downstream user's concern, not the starterkit's.
- **Removing or disabling existing workflows.** Multiple past PRs deleted or commented out
  the test workflow to make their own checks pass. That is an automatic close.
- **Swapping the tooling** (ruff → pylint/flake8, gunicorn → uwsgi, etc.) without a
  concrete argument for why it is better here.
- Broad reformatting or renaming that touches many files for no functional gain.

## Ground rules

1. **Do not delete or disable tests or workflows.** If a check fails, fix the cause.
2. **Do not commit secrets**, and do not add your personal infrastructure identifiers.
3. **Write a PR description.** A PR titled "Fixes" with an empty body will be closed.
4. **One concern per PR.**

## Local development

```bash
cp .env.example .env
docker compose build
docker compose up app
```

Before pushing, both of these must pass:

```bash
docker compose up --exit-code-from test-runner test-runner
ruff check . && ruff format --check .
```

The source is bind-mounted, so edits are picked up without a rebuild. If you change
`requirements.txt` or `requirements-dev.txt`, run `docker compose build test-runner`
first — dependencies live in the image, not the mount.

CI runs the same checks on every pull request, plus a smoke test that boots the
production image and waits for `/health`.
