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

## P1 — Ресторан MVP

| ID | Даалгавар | Төлөв | Тэмдэглэл |
|---|---|---|---|
| P1-01 | e-barimt QR задлах + баталгаажуулах | ✅ код / 🚧 mock | `app/core/e_barimt.py`, `app/api/v1/poe_evidence.py` — бодит e-barimt API эрх ⛔ |
| P1-02 | Зураг upload, EXIF устгах | ✅ | `app/core/uploads.py`, `app/api/v1/uploads.py`, `tests/test_uploads.py` |
| P1-03 | OCR pipeline (PaddleOCR) | ✅ талбар задлалт / ⛔ загвар | `app/ml/ocr.py` — `run_paddleocr` тодорхой `NotImplementedError`, загвар суулгаагүй |
| P1-04 | pHash давхардал + ELA forensic | ✅ | `app/ml/forensics.py` |
| P1-05 | PoE түвшин/жин engine | ✅ | `app/domain/poe.py` — жингийн хүснэгт PRD-аас баталгаажуулах шаардлагатай |
| P1-06 | Queue + worker, DLQ, retry | ✅ | `app/workers/moderation.py` |
| P1-07 | Moderation шат 1: PII regex | ✅ | `app/domain/moderation.py` |
| P1-08 | XLM-R classifier | ✅ интерфейс / ⛔ загвар сургалт | `app/ml/classifier.py` — heuristic-v0 fallback, бодит F1≥0.88 P0-12 өгөгдөл шаардана |
| P1-09 | Bayesian trimmed оноо | ✅ | `app/domain/scoring.py`, `scoring_service.py` |
| P1-10 | Entity хуудас (SSR) | ✅ (эхний хувилбар) | `apps/web/app/entities/[id]/page.tsx` |
| P1-11 | Web: үнэлгээ илгээх урсгал | ✅ (эхний хувилбар) | `apps/web/app/entities/[id]/review/` |
| P1-12 | Mobile: үнэлгээ, QR scanner | ✅ (эхний хувилбар) | `apps/mobile/screens/ReviewScreen.tsx`, `QrScannerScreen.tsx` |
| P1-13 | Эзэмшигчийн claim + хариу | ✅ | `app/api/v1/ownership.py` |
| P1-14 | Гомдлын endpoint | ✅ | `app/api/v1/complaints.py` |
| P1-16 | Пилот: 50 ресторан, 2,000 хэрэглэгч | ⛔ | Бодит хэрэглэгч татах — код биш |
| P1-17 | E2E тест | ✅ эхлэл | `apps/web/e2e/critical-flows.spec.ts` — 3/20 урсгал; Playwright суулгаагүй |
| P1-18 | OWASP ASVS L2 + pentest | ⛔ | Гадны pentester шаардана |
| S-05 | Монгол анализатор | ✅ | `app/search/mongolian_text.py` — ө/ү folding, галиг, light stemmer |
| S-06 | Autocomplete | ✅ (код) | `app/api/v1/search.py` |
| S-07 | Ranking v1 | ✅ | `app/search/ranking.py` (томьёо 5.4) |
| S-08 | Gold set, NDCG harness | ✅ хэрэгсэл / ⛔ 500 асуулгын дээж | `app/search/ndcg.py`, `infra/search-eval/` — жинхэнэ 500 асуулга тэмдэглэгдээгүй |
| S-09 | Хайлтын үр дүнгийн хуудас | ✅ (эхний хувилбар) | `apps/web/app/search/` |
| S-10 | Салбар/категорийн нүүр хуудас | ✅ (эхний хувилбар) | `apps/web/app/[branch]/[category]/` |
| S-11 | Нэгэн жигд entity хуудасны загвар | ✅ | `display_config.sections`-аар жолоодогдоно (P1-10-той хамт) |
| S-12 | SEO | ⛔ хийгдээгүй | Дараагийн алхам |
| S-13 | Хайлтын аналитик | ⛔ хийгдээгүй | Дараагийн алхам |

## Баталгаажуулалтын хязгаарлалт (энэ орчинд)

Энэ орчинд Docker болон сүлжээний хандалт байхгүй тул дараах зүйлсийг **бичсэн боловч бодитоор ажиллуулж шалгаагүй**:

- `pytest` (Postgres, Redis, OpenSearch container шаардана) — `apps/backend/tests/`
- `docker compose up` бүрэн стек
- `terraform plan/apply` (AWS эрх шаардана)
- GitHub branch protection (repo, `gh` CLI эрх шаардана — `.github/workflows/ci.yml` мержлэхээс өмнө **Settings → Branches**-д гараар асаана уу)

Python синтаксийг `py_compile`-аар шалгасан (алдаагүй), гэхдээ import/runtime түвшний алдаа байж болзошгүй тул эхний CI ажиллуулалт дээр засвар шаардагдаж магадгүй.

## Дараагийн алхам

P2 (Эмнэлэг + Anti-fraud) — GPS geofence, fraud загвар (LightGBM), LLM moderation worker, query understanding, zero-result fallback. `OmniRate SOW v2.md` §6-г үз. Мөн P1 дотор хийгдээгүй үлдсэн зүйлс: S-12 (SEO), S-13 (хайлтын аналитик), P1-16 (пилот), P1-18 (pentest).

## Гадаад хамаарлын жагсаалт (энэ кодоор шийдэгдэхгүй)

1. **ДАН гэрээ** — OAuth2 client_id/secret, sandbox эрх авахгүйгээр P0-07-г L1(OTP)-оос цааш production-д ашиглах боломжгүй.
2. **e-barimt API эрх** — P1-01-ийг production горимд ажиллуулахад шаардлагатай.
3. **Хуульч** — DPIA, зөвшөөрлийн текст, moderation policy-г батлуулах (PM+EXT).
4. **Pentester** — OWASP ASVS L2 pentest (P1-18).
5. **Тэмдэглэгчид** — 15,000 moderation дээж, gold set (P0-12, S-08).
6. **Бодит хэрэглэгчид** — card sorting/tree test (S-01), usability тест (K12, S-16, S-20), red-team (K4/K5).
7. **PaddleOCR/XLM-R загвар** — P1-03/P1-08 interface бэлэн, гэхдээ бодит загвар P0-12-ийн өгөгдөл дээр сургагдах ёстой.
8. **`npm install`/`pip install`** — энэ орчинд сүлжээ/registry хандалт байхгүй тул хийгдээгүй; Node/Python dependency-үүд tsconfig/pyproject-д зарлагдсан ч суулгаагүй.
