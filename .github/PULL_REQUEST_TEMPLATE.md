## Summary

<!-- What does this change do, and why? -->

SOW task ID (if applicable): <!-- e.g. P1-05 -->

## Changes

<!-- Bullet list of the concrete changes -->

-

## Testing

<!-- How did you verify this? Prefer commands/output over "tested locally". -->

- [ ] Backend: `ruff check .` / `mypy app` / `pytest --cov=app --cov-fail-under=80` (`apps/backend`)
- [ ] Web: `npm run lint` / `npm run typecheck` / `npm run build` / `npm run e2e` (`apps/web`)
- [ ] Mobile: `npx tsc --noEmit`, tested on affected platform(s) (`apps/mobile`)
- [ ] N/A — docs/config only

## Checklist

- [ ] Change is scoped to one concern (no unrelated refactors bundled in)
- [ ] New/changed behavior has test coverage
- [ ] `docs/PROGRESS.md` updated if this changes SOW task status
- [ ] No secrets, credentials, or `.env` values committed

## Notes for reviewers

<!-- Anything a reviewer should know: tradeoffs, follow-ups, external deps this depends on, etc. -->
