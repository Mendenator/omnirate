# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project has no tagged releases yet (pre-production); changes are
grouped under `[Unreleased]` until the first release is cut. For
day-to-day implementation status against the SOW task breakdown, see
[`docs/PROGRESS.md`](./docs/PROGRESS.md).

## [Unreleased]

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
  (Next.js 15→16, Expo SDK) rather than force-applying them — see
  [`SECURITY.md`](./SECURITY.md).
