# Security Policy

## Project status

OmniRate is pre-production (see [`docs/PROGRESS.md`](./docs/PROGRESS.md)).
There are no tagged releases yet — security fixes land on `master`.

## Reporting a vulnerability

**Please do not open a public GitHub issue for a security vulnerability.**

Report it privately via GitHub's
[security advisory form](https://github.com/Mendenator/omnirate/security/advisories/new)
for this repository. Include:

- A description of the issue and its potential impact
- Steps to reproduce (a minimal repro is ideal)
- Affected file(s)/endpoint(s), if known

You should get an initial response within a few days. Please give us a
reasonable amount of time to investigate and fix an issue before any public
disclosure.

## Known limitations (not new findings — no need to report these)

These are tracked, pre-existing gaps documented in
[`docs/PROGRESS.md`](./docs/PROGRESS.md); they don't need a fresh report,
though follow-up is still welcome if you have specifics that aren't already
captured there:

- **Role-based authorization is not yet enforced.** Moderator/law-enforcement
  endpoints (P2-12, P3-06) are currently reachable by any authenticated
  user. This must be locked down before any production deployment.
- **ДАН and e-barimt integrations run against local mocks**
  (`settings.dan_use_mock` / `settings.e_barimt_use_mock`) — production
  credentials require OmniRate's own legal entity to sign agreements with
  the National Data Center and the tax authority; see
  `apps/backend/app/core/dan_auth.py` and
  `apps/backend/app/core/e_barimt.py` for details.
- **LLM-based moderation (P2-05) has no API key configured**, so all
  borderline content currently falls back to `needs_human_review` (a safe
  default, not an open gap).
- **Known dependency advisories that require a breaking upgrade:**
  `pip-audit` and `npm audit` are run and tracked (see
  `docs/PROGRESS.md`); at last check, `apps/web` had 2 advisories in a
  `postcss`/Next.js transitive dependency (needs Next.js 15→16) and
  `apps/mobile` had 25 in the Expo/React Native dependency tree (needs an
  Expo SDK major upgrade). Both require breaking framework upgrades and are
  deliberately not force-applied outside a planned upgrade — flagging a new
  advisory that isn't one of these is still useful.
- **No independent penetration test or legal review has been performed yet**
  (P1-18, P3-09 in the SOW) — this codebase has not been production-hardened
  end to end.

## Supported versions

Only the `master` branch is supported / receives fixes.
