# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
For day-to-day implementation status against the SOW task breakdown,
see [`docs/PROGRESS.md`](./docs/PROGRESS.md).

## [Unreleased]

### Fixed

- Review moderation never ran: `POST /api/v1/reviews` enqueued
  `moderate_review` onto `"arq:queue:moderation"`, but the moderation
  worker's `WorkerSettings` never set a matching `queue_name` (arq's
  default is `"arq:queue"`), and `docker-compose.yml` had no container
  running it at all. The moderation worker now polls
  `MODERATION_QUEUE_NAME` (a single constant shared with the enqueue
  site) and runs as its own `worker-moderation` compose service. It keeps
  its own queue rather than sharing the default one with the indexer
  worker, since two workers with different registered functions on one
  queue would each grab jobs they can't run.

## [0.2.3] - 2026-09-25

### Fixed

- `POST /api/v1/reviews` only ever enqueued a `moderate_review` job — a new
  review never triggered `reindex_entity`, so OpenSearch (and the
  entity-page score) only picked up a new review after someone manually
  reindexed. `create_review` now enqueues `reindex_entity` too.
- `app/workers/indexer.reindex_entity` and
  `app/domain/scoring_service.materialize_entity_score` both computed an
  entity's score from *every* review, including ones blocked by
  moderation for defamation (`Review.is_blocked`). Both now exclude
  blocked reviews, matching `GET /api/v1/entities/{id}`'s existing filter.

### Changed

- (Internal, discovered while fixing the above) `reindex_entity`'s new
  enqueue call deliberately omits a custom `_queue_name` — the indexer
  worker's `WorkerSettings` never declares one, so it polls arq's default
  queue. `moderate_review`'s existing enqueue call still targets
  `"arq:queue:moderation"`, which no running worker actually listens on;
  that's a separate, pre-existing bug (moderation jobs are silently never
  processed) left as-is here since fixing it means deciding whether a
  moderation worker process should be deployed at all, not just a code
  change.

## [0.2.2] - 2026-09-25

### Changed

- README's Open PRs badge switched from a hand-maintained static value to
  shields.io's `github/issues-pr` endpoint, matching the Open Issues
  badge next to it — it now reflects the real open PR count
  automatically instead of needing a manual edit.

## [0.2.1] - 2026-09-25

### Fixed

- `apps/backend/tests/conftest.py`'s `engine` fixture pointed straight at
  `settings.database_url` and dropped/recreated the whole schema on every
  test run — harmless against CI's short-lived service container, but
  locally that URL defaults to the same docker-compose Postgres instance
  a dev backend and any manually-created demo data live in, so every
  local `pytest` run silently wiped it. Tests now run against a derived,
  dedicated `<db>_test` database instead, auto-created on first use.
- Fixing the above exposed a second, previously-hidden bug: `test_import_
  counts_unmatched_records` bypassed the test fixtures and used the app's
  global session factory (pointed at the real database) directly instead
  of the injected `db_session`, and only ever passed because the first
  bug happened to leave that schema lying around. Now uses `db_session`
  like its neighboring tests.

## [0.2.0] - 2026-09-25

### Added

- Entity page display side (P1-10): `GET /api/v1/entities/{id}` now returns
  a live-computed Bayesian score, review/verified-review counts, and a
  per-criterion score breakdown; a new `GET /api/v1/entities/{id}/reviews`
  lists an entity's non-blocked reviews. The web entity page renders all of
  this (score summary, criteria breakdown, review list with dates and PoE
  badges, map link, owner-reply section), replacing what was previously
  header-only placeholder sections. Listing (`/[branch]/[category]`) and
  search results now show each entity's score inline.
- `app/domain/scoring.compute_criteria_breakdown`, a pure per-criterion
  averaging function, plus `EntityResponse.lat`/`lon` exposure needed for
  the new map-link rendering.

### Fixed

- `apps/backend`'s dependency list declared `sqlalchemy>=2.0` without the
  `[asyncio]` extra and never listed `greenlet` explicitly — a fresh
  install had been relying on some other package pulling it in
  transitively. That stopped happening (surfaced as CI's `backend`/
  `web-e2e` jobs suddenly failing with `ModuleNotFoundError: No module
  named 'greenlet'`, breaking both the async engine import and
  `[tool.coverage.run]`'s `concurrency = ["greenlet", "thread"]`).
  `greenlet` is now an explicit dependency.

## [0.1.3] - 2026-09-24

### Added

- Website badge in the README badge table, linking to the
  plain-language report — same URL now set as the repo's GitHub
  homepage link.

## [0.1.2] - 2026-09-24

### Added

- A live release badge in `docs/report.html`'s header (matching
  README's), so the plain-language report also shows the current
  release version.

## [0.1.1] - 2026-09-24

### Added

- README: latest-release badge, and the 9-badge block reformatted into
  a 3-column table (repo, build, release, license, activity) instead
  of one long line of links.
- The plain-language, non-technical progress report (published earlier
  as a Claude Artifact) is now pinned and cross-linked from
  `README.md`, `docs/PROGRESS.md`, and `CONTRIBUTING.md`, and the
  report itself (`docs/report.html`) links back to its own live,
  shareable URL from its header.

### Changed

- Verified the `v0.1.0` GitHub Release's auto-generated source
  archives (zip and tar.gz) download and extract correctly end to end
  — this release exists specifically to catch `master` up to what that
  verification found missing (the badge/doc-link commits above landed
  after `v0.1.0` was tagged).

## [0.1.0] - 2026-09-24

### Added

- **P0 — Foundation**: monorepo scaffold (`apps/backend` FastAPI,
  `apps/web` Next.js, `apps/mobile` Expo), domain API, schema registry,
  OpenSearch-backed search plumbing with Mongolian-language analysis, and
  infra-as-code (Docker Compose stack: Postgres+PostGIS+pg_jsonschema+pgvector,
  Redis, OpenSearch, Prometheus, Grafana).
- **P1 — Restaurant MVP**: Proof-of-Experience (PoE) and Bayesian
  trimmed-mean scoring engine, e-barimt receipt verification (mocked
  pending production access), moderation queue, Mongolian-aware search,
  and the first end-to-end web + mobile review flows.
- **P2 — Hospital + anti-fraud**: GPS geofencing with dwell-time
  calculation and mock-location detection, LightGBM fraud classifier,
  LLM-assisted moderation, and graph/embedding-based fraud-ring
  clustering.
- **P3 — Political closed beta**: jurisdiction-aware scoring,
  `strict_defamation` safeguards for political entities, a takedown /
  law-enforcement portal, and disaster-recovery + transparency
  reporting.
- Project docs: [`LICENSE`](./LICENSE) (Apache 2.0),
  [`CONTRIBUTING.md`](./CONTRIBUTING.md),
  [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md),
  [`SECURITY.md`](./SECURITY.md), a plain-language progress report for
  non-technical readers, and sourced onboarding documentation for the
  ДАН and e-barimt external integrations.

### Fixed

- Backend compatibility issues surfaced by the first real run against
  Python 3.12 and a live Docker stack, including: forward-reference and
  descriptor bugs in several `arq` worker configs, a geofence dwell-time
  calculation that silently bridged excursions outside the fence, an
  overly permissive defamation-pattern regex, and Pydantic response
  models that only failed against real (non-mocked) database rows.
- `infra/postgres/Dockerfile` build failures (Debian bullseye
  end-of-life mirrors, a `libxml2` version conflict) that blocked a
  clean `docker compose build`.
- Next.js 15's breaking change to `params` (now a `Promise`), caught
  only by `next build`, not `next dev`.
- Mobile app startup crash from a missing `expo-asset` dependency, a
  missing `apps/mobile/app.json`, no CORS support for direct mobile
  calls to the backend, and `expo-secure-store` having no web
  implementation (added a platform-aware `lib/tokenStorage.ts`).
- CI workflow (`.github/workflows/ci.yml`) was scoped to trigger on
  `main`, but the repo's default branch is `master` — it had never
  actually run.

### Security

- Replaced `python-jose` with `PyJWT` to drop a transitive `ecdsa`
  dependency flagged for an unpatched timing side-channel
  (PYSEC-2026-1325); the app only ever used HS256, which PyJWT supports
  without `ecdsa` at all.
- Added a config validator rejecting placeholder/short JWT and РД-hash
  secrets outside the `dev` environment.
- Added `CORSMiddleware` with an explicit allow-list instead of no CORS
  policy at all.
- Ran `pip-audit` and `npm audit` across all three apps; documented
  remaining advisories that require breaking major-version upgrades
  rather than force-applying them — see [`SECURITY.md`](./SECURITY.md).

### Changed

- **CI actually runs now.** `.github/workflows/ci.yml` was scoped to
  trigger on `main`; the repo's real default branch is `master`, so it
  had silently never triggered on any commit since it was added. Once
  fixed, that first real run surfaced (and this release fixes) a chain
  of previously-invisible gaps: 43 ruff line-length violations, 92
  `mypy --strict` errors (including two real latent bugs — unchecked
  `None` access in the PoE-evidence endpoints, and a wrong SQLAlchemy
  result type in the hospital-QR replay check), a coverage measurement
  bug (`coverage.py` needs `concurrency = ["greenlet", "thread"]` to
  see inside SQLAlchemy's async/greenlet bridge — without it most
  DB-touching code read as untested even when it wasn't), and a
  Postgres service image that shipped PostGIS but not the `pgvector`
  extension the schema actually needs. Backend test coverage went from
  71.6% to 91.6% in the process. Added a `web-e2e` CI job running the
  real Playwright suite against a live backend + Postgres + Redis +
  OpenSearch stack.
- **Major framework upgrades**, consolidated from 19 individually-
  conflicting Dependabot PRs into two reviewed branches: `apps/web` to
  Next.js 16, React 19, ESLint 10, `@rjsf/*` 6; `apps/mobile` to Expo
  SDK 57 and React 19. TypeScript was deliberately held back on both
  (7.0 hits real, current upstream blockers — `typescript-eslint`
  refuses to run under it at all). Along the way, fixed a real ESLint
  10 / `eslint-plugin-react` incompatibility (pinned
  `settings.react.version` instead of leaving it on the now-broken
  `"detect"` auto-detect path), two genuine `expo-doctor` gaps (missing
  `react-navigation` peer deps, a duplicate `expo-asset` install), and
  two more pre-existing type errors in `apps/mobile` (a
  `@react-navigation/native-stack` typed-API `id` requirement, and a
  `tsconfig.json` `module` setting that predated dynamic `import()`
  support) — none of these were caused by the upgrades, all were
  invisible until this cycle actually ran the checks for real.
- Repo governance and tooling: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `CODEOWNERS`, PR and issue templates, Dependabot
  config, `.editorconfig`, `.nvmrc` / `.python-version`, and a Prettier
  config for `apps/web` (applied once, repo-wide, so it starts
  consistent rather than immediately failing its own check).
