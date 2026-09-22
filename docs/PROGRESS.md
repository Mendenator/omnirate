# Хэрэгжилтийн явц (SOW v2 эсрэг)

Энэ баримт `OmniRate SOW v2.md`-ийн даалгавар бүрийг код түвшинд хэрхэн хэрэгжүүлж байгааг, юу нь гадаад хамааралтай тул зөвхөн stub/mock хэлбэртэй байгааг тэмдэглэнэ.

Тэмдэглэгээ: ✅ хийгдсэн · 🚧 хийгдэж байна · ⛔ гадаад хамааралтай (код бус)

## P0 — Суурь

| ID | Даалгавар | Төлөв | Тэмдэглэл |
|---|---|---|---|
| P0-01 | Monorepo, CI/CD | ✅ | `.github/workflows/ci.yml`, `deploy-stage.yml` (stage deploy алхам stub — бодит cloud эзэмшигчгүй) |
| P0-02 | Terraform: Postgres16+PostGIS+pg_jsonschema, Redis7, storage | ✅ (код) | `infra/terraform/` — `terraform apply` хийхэд бодит cloud эрх (AWS/GCP) шаардана |
| P0-03 | Observability: OTel, Prometheus, Grafana, Sentry | ✅ | `apps/backend/app/core/observability.py`, `infra/observability/` |
| P0-04 | Alembic migration: 6 хүснэгт + audit_log | ✅ | `apps/backend/alembic/versions/` |
| P0-05 | Schema registry | ✅ | `apps/backend/app/schema_registry/` |
| P0-06 | Entities/Reviews CRUD, idempotency | ✅ | `apps/backend/app/api/v1/` |
| P0-07 | ДАН OAuth2+PKCE, РД HMAC, JWT, OTP | ✅ код / 🚧 mock provider | `apps/backend/app/core/dan_auth.py`, `app/api/v1/auth.py` — бодит ДАН client_id/secret **гэрээ шаарддаг гадаад хамаарал** ⛔, одоогоор `dan_use_mock=true`-р ажиллана |
| P0-08 | Gateway rate limit | ✅ | `apps/backend/app/core/rate_limit.py` |
| P0-09 | Admin UI | ✅ (эхний хувилбар) | `apps/web/app/admin/schemas/` — категори нэмэх builder UI (K7); package.json-оос цааш `npm install`, дизайн систем (S-02) дараа нэгтгэнэ |
| P0-10 | JSON Schema → form renderer | ✅ (эхний хувилбар) | `apps/web/app/entities/new/EntityAttributesForm.tsx` (@rjsf/core) |
| P0-11 | Mobile skeleton | ✅ (эхний хувилбар) | `apps/mobile` — Expo, OTP(L1) auth screen; ДАН/attestation P1-12-т |
| P0-12 | Moderation dataset 15,000 тэмдэглэл | ⛔ | Бодит тэмдэглэгчид (EXT) шаардана — код биш |
| P0-13 | k6 harness, 10M мөрийн generator | ✅ | `infra/loadtest/` |
| P0-14 | DPIA, хуульчийн гэрээ | ⛔ | Монгол хуульчаар батлуулах ёстой — код биш |
| S-01 | Таксономи: card sorting, tree testing | ✅ эх материал / ⛔ судалгаа | Эхний таксономи `docs/taxonomy.md`-д тодорхойлогдсон; бодит 30 хэрэглэгчийн card sorting/tree test хийгдээгүй |
| S-03 | OpenSearch 3 node + CDC indexer | ✅ (код) | `infra/terraform/modules/opensearch`, `apps/backend/app/search/` |
| S-04 | `search`/`display` config schema registry-д | ✅ | `apps/backend/app/schema_registry/models.py` |

## Баталгаажуулалтын хязгаарлалт (энэ орчинд)

Энэ орчинд Docker болон сүлжээний хандалт байхгүй тул дараах зүйлсийг **бичсэн боловч бодитоор ажиллуулж шалгаагүй**:

- `pytest` (Postgres, Redis, OpenSearch container шаардана) — `apps/backend/tests/`
- `docker compose up` бүрэн стек
- `terraform plan/apply` (AWS эрх шаардана)
- GitHub branch protection (repo, `gh` CLI эрх шаардана — `.github/workflows/ci.yml` мержлэхээс өмнө **Settings → Branches**-д гараар асаана уу)

Python синтаксийг `py_compile`-аар шалгасан (алдаагүй), гэхдээ import/runtime түвшний алдаа байж болзошгүй тул эхний CI ажиллуулалт дээр засвар шаардагдаж магадгүй.

## Дараагийн алхам

P1 (Ресторан MVP) — e-barimt QR, OCR, PoE тооцоолол, Bayesian оноо, entity хуудас гэх мэт. `OmniRate SOW v2.md` §6-г үз.

## Гадаад хамаарлын жагсаалт (энэ кодоор шийдэгдэхгүй)

1. **ДАН гэрээ** — OAuth2 client_id/secret, sandbox эрх авахгүйгээр P0-07-г L1(OTP)-оос цааш production-д ашиглах боломжгүй.
2. **e-barimt API эрх** — P1-01-ийг production горимд ажиллуулахад шаардлагатай.
3. **Хуульч** — DPIA, зөвшөөрлийн текст, moderation policy-г батлуулах (PM+EXT).
4. **Pentester** — OWASP ASVS L2 pentest (P1-18).
5. **Тэмдэглэгчид** — 15,000 moderation дээж, gold set (P0-12, S-08).
6. **Бодит хэрэглэгчид** — card sorting/tree test (S-01), usability тест (K12, S-16, S-20), red-team (K4/K5).
