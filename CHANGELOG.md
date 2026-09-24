# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
For day-to-day implementation status against the SOW task breakdown,
see [`docs/PROGRESS.md`](./docs/PROGRESS.md).

## [Unreleased]

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
