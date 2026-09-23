# Contributing to OmniRate

Thanks for your interest in OmniRate. This is a monorepo implementing the
`OmniRate SOW v2.md` task breakdown (P0 → P1 → P2 → P3, S-01…S-20); see
[`docs/PROGRESS.md`](./docs/PROGRESS.md) for current status and
[`README.md`](./README.md) for the repo layout.

## Before you start

- Check [`docs/PROGRESS.md`](./docs/PROGRESS.md) and open issues/PRs first
  so you don't duplicate work already in flight.
- For anything non-trivial (new endpoints, schema changes, new external
  integrations), open an issue describing the change before writing code —
  it's much easier to discuss direction early than to rework a finished PR.
- Some parts of the system (ДАН auth, e-barimt verification) depend on
  external agreements OmniRate itself must sign and run against local mocks
  in the meantime (`settings.dan_use_mock` / `settings.e_barimt_use_mock`).
  See the module docstrings in `apps/backend/app/core/dan_auth.py` and
  `apps/backend/app/core/e_barimt.py` before touching those integrations.

## Local setup

```bash
cp .env.example .env
docker compose up -d          # postgres, redis, opensearch
cd apps/backend
uv sync                       # or: pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

Web and mobile each have their own `package.json`:

```bash
cd apps/web && npm install && npm run dev
cd apps/mobile && npm install && npm start
```

## Making changes

1. Create a branch off `master`.
2. Keep changes scoped — a bug fix shouldn't carry unrelated refactors.
3. Match the existing code style rather than introducing a new one.
4. Run the checks below for whichever app(s) you touched before opening a PR.
5. Write a commit message that explains *why*, not just *what*.

### Backend (`apps/backend`)

```bash
ruff check .              # lint
mypy app                  # type check
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

New behavior needs test coverage; the CI gate fails under 80% line coverage.

### Web (`apps/web`)

```bash
npm run lint
npm run typecheck
npm run build
npm run e2e                # Playwright, requires the backend running
```

### Mobile (`apps/mobile`)

```bash
npx tsc --noEmit
```

Test on both native (`expo start --ios` / `--android`) and web
(`expo start --web`) if your change touches `lib/` or shared screens —
the two platforms use different storage backends (see
`apps/mobile/lib/tokenStorage.ts`).

## Pull requests

- CI (`.github/workflows/ci.yml`) runs lint, type check, and tests against
  `master` on every push and PR — it must pass before merge.
- Reference the relevant SOW task ID (e.g. `P1-05`) in the PR description
  when applicable.
- Small, focused PRs are easier to review than large ones; split unrelated
  changes into separate PRs.

## Security

Do not open a public issue for a suspected security vulnerability
(credential handling, РД/national-ID hashing, auth flows, etc.). Instead
contact the maintainers privately first so a fix can be prepared before
details are public.

## Code of conduct

Be respectful and constructive. Disagreements about technical direction are
normal; personal attacks are not.
