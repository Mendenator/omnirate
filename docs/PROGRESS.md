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

## P2 — Эмнэлэг ба Anti-fraud

| ID | Даалгавар | Төлөв | Тэмдэглэл |
|---|---|---|---|
| P2-01 | GPS geofence dwell-time | ✅ | `app/domain/geofence.py`, `app/api/v1/poe_evidence.py`-ийн `/evidence/gps` |
| P2-02 | Mock location, хурдны үсрэлт илрүүлэх | ✅ | `app/domain/geofence.py`-д нэгтгэсэн (`detect_mock_location`) |
| P2-03 | Эмнэлгийн QR: Ed25519, 72ц JWT, PDF | ✅ | `app/core/hospital_qr.py`, `hospital_qr_pdf.py`, `app/api/v1/hospital_qr.py` |
| P2-04 | Эрүүл мэндийн PII redaction | ✅ | `app/domain/medical_pii.py` — жинхэнэ "эмийн толь" эх сурвалж ⛔ |
| P2-05 | LLM moderation worker | ✅ бүтэц / ⛔ LLM endpoint | `app/ml/llm_moderation.py` — threshold 0.93, sampling ≤30% хэрэгжсэн; бодит LLM API тохируулаагүй |
| P2-06 | Засах санал (rewrite) UX | ✅ | `apps/web/.../RewriteSuggestion.tsx` |
| P2-07 | CDC → Parquet → DuckDB | ✅ (код) | `app/analytics/` — бодит S3/Postgres холболтгүйгээр ажиллуулж шалгаагүй |
| P2-08 | LightGBM fraud загвар + синтетик өгөгдөл | ✅ бүрэн ажиллана | `app/ml/fraud_model.py`, `fraud_synthetic_data.py` — **синтетик өгөгдөр AUC>0.9 баталгаажсан**; бодит өгөгдөр дахин сургах шаардлагатай |
| P2-09 | Louvain graph job | ✅ | `app/ml/graph_fraud.py` — 1M ирмэгийн хэмжээнд networkx-ээс igraph/graph-tool руу шилжих санал тэмдэглэсэн |
| P2-10 | Embedding төстэй байдал (pgvector) | ✅ storage/query / ⛔ e5 загвар | `app/domain/embedding_service.py`, `app/ml/embeddings.py` |
| P2-11 | Surge mode | ✅ | `app/domain/surge.py`, `surge_service.py` |
| P2-12 | Хүний шалгалт, 2-moderator урсгал | ✅ | `app/domain/moderation_queue.py`, `app/api/v1/moderation_queue.py` |
| P2-13 | Device binding, 7 хоногийн cooldown | ✅ | `app/domain/device_binding.py` |
| P2-14 | Red-team: 10,000 бот, 300 хүн | ⛔ | Бодит бот/хүний нөөц шаардана — код биш |
| S-14 | Query understanding | ✅ | `app/search/query_understanding.py` |
| S-15 | Zero-result fallback | ✅ | `app/search/zero_result.py` |
| S-16 | Usability тест 1-р шат | ⛔ | 20 бодит хэрэглэгч шаардана — код биш |
| S-17 | Ranking-ийн эсрэг манипуляц | ✅ | `tests/test_ranking_anti_manipulation.py` — P1-09-ийн fraud-score шүүлт S-17 шаардлагыг хангахыг баталгаажуулна |

## P3 — Улс төрийн хаалттай бета

| ID | Даалгавар | Төлөв | Тэмдэглэл |
|---|---|---|---|
| P3-01 | Хороо → тойргийн mapping, хувилбартай импорт | ✅ | `app/domain/jurisdiction.py`, `district_mappings` хүснэгт |
| P3-02 | jurisdiction_match ба тусгаарласан оноо | ✅ | `app/domain/political_scoring.py` |
| P3-03 | Улс төрчийн schema + ирцийн импорт | ✅ бүтэц / ⛔ эх сурвалж | `app/domain/attendance_import.py`, `app/core/attendance_source.py` — SOW-ийн өөрийнх нь тэмдэглэсэн "Өгөгдлийн эх сурвалж" хамаарал шийдэгдээгүй |
| P3-04 | strict_defamation moderation горим | ✅ | `app/domain/defamation.py`, `app/workers/moderation.py`-д нэгтгэсэн |
| P3-05 | Notice-and-takedown, SLA таймер, hash-chain audit | ✅ | `app/domain/takedown.py`, `app/api/v1/takedown.py` — audit chain P0-06-ийн `app/domain/audit.py` дээр суурилсан |
| P3-06 | Хууль сахиулах байгууллагын портал | ✅ | `/api/v1/law-enforcement-requests` — 4ц SLA; **анхаар**: жинхэнэ role-based auth хараахан бэхлэгдээгүй |
| P3-07 | Сарын ил тод байдлын тайлан | ✅ | `app/analytics/transparency_report.py` |
| P3-08 | Moderator сургалт, playbook | ⛔ | Бодит сургалт/шалгалт — код биш |
| P3-09 | Хуульчийн эцсийн хяналт | ⛔ | Монгол хуульч шаардана |
| P3-10 | Хаалттай бета: 2 тойрог, 1,000 хэрэглэгч | ⛔ | Бодит хэрэглэгч татах — код биш |
| P3-11 | Load test: 1,000 RPS унших, 200 RPS бичих | ✅ | P0-13-ийн `infra/loadtest/k6/` (K1, K2 аль хэдийн хамрагдсан) |
| P3-12 | DR дасгал | ✅ runbook+script / ⛔ гүйцэтгэл | `infra/dr/dr_drill.md`, `measure_rpo_rto.py` — бодит AWS орчинд ажиллуулаагүй |
| S-18 | Төрийн албаны хайлт: тойргоор үзэх, төвийг сахисан эрэмбэ | ✅ жагсаалт / 🚧 газрын зураг | `app/api/v1/political_search.py`, `apps/web/app/tur-alba/` — бодит choropleth зураг GeoJSON эх сурвалж дутуу тул жагсаалт хэлбэрээр |
| S-19 | Хайлтын load test 500 RPS + failover | ✅ | `infra/loadtest/k6/search_failover_load_test.js` |
| S-20 | Эцсийн usability + WCAG аудит | ✅ автомат хэсэг / ⛔ хүний тест | `apps/web/e2e/accessibility.spec.ts` (axe-core) — бодит 20 хэрэглэгчийн usability тест хийгдээгүй |

## Баталгаажуулалтын явдал

**`docker compose up` бүрэн стек болон `pytest` бодитоор ажиллуулж шалгасан** (Docker Desktop + Python 3.12 суулгасны дараа): бүх 7 сервис (postgres, redis, opensearch, prometheus, grafana, backend, worker) эрүүл ажиллаж, 13 Alembic migration бүгд амжилттай орж, **169/169 backend тест live Postgres/Redis/OpenSearch эсрэг амжилттай давсан**.

Энэ явцад олдож засагдсан бодит алдаанууд (git history-д дэлгэрэнгүй):
- `infra/postgres/Dockerfile`: Debian 11 bullseye EOL → archive.debian.org, libxml2 downgrade зөрчил, pgvector огт суулгаагүй байсан, pg_jsonschema.so нэрний алдаа.
- `docker-compose.yml`: opensearch healthcheck дутуу байсан тул backend/worker эрт унаж байсан.
- 5 worker файл: `redis_settings` нь `@staticmethod` байсан нь arq-тай зөрчилдсөн (жинхэнэ RedisSettings объект байх ёстой).
- `app/workers/indexer.py`: forward-reference алдаа (`noop_heartbeat` class-аас доор тодорхойлогдсон байсан).
- 3 API response model (`complaints.py`, `moderation_queue.py`, `takedown.py`): `id: str` бодит баганын төрөл `uuid.UUID`-тай зөрчилдсөн.
- Тестийн fixture: `client` fixture-ийн зохиомол хэрэглэгч бодит `users` мөр байгаагүй тул FK constraint зөрчиж байсан.

**`apps/web` бодитоор ажиллуулж шалгасан** (Node.js 24 суулгасны дараа): `npm install` (332 сан) амжилттай, `next dev` эхэлж, дараах хуудсууд шалгагдсан —

- Нүүр хуудас, `/search` (zero-result fallback K11 зурвас зөв харагдана)
- `/admin/schemas` (K7 builder) — **бүтэн E2E урсгал бодитоор шалгагдсан**: React UI-аас категори нэмж, `/api/backend/*` rewrite proxy-гоор жинхэнэ FastAPI backend руу, тэндээс live Postgres руу мөр бичигдэж, буцаж GET-ээр баталгаажсан (Кирилл текст — `label_mn: "Хоолны төрөл"` — гэмтэлгүй round-trip хийсэн).

**Playwright e2e (P1-17) + axe-core WCAG аудит (S-20) бодитоор ажиллуулж шалгасан**: Chromium суулгаж, `apps/web/e2e/`-ийн бүх **7 тест 7/7 давсан** (нэг тест эхлээд entity өгөгдөл дутуу тул алгассан байсан ч жинхэнэ entity Postgres-д үүсгээд дахин ажиллуулахад давсан). `/`, `/search`, `/admin/schemas`, `/tur-alba` — 4 хуудсанд critical/serious WCAG 2.2 AA зөрчил **0**.

Одоо хараахан шалгаагүй:
- `terraform plan/apply` (AWS эрх шаардана)
- GitHub branch protection (repo, `gh` CLI эрх шаардана — `.github/workflows/ci.yml` мержлэхээс өмнө **Settings → Branches**-д гараар асаана уу)
- `npm run build` (production build)
- `apps/mobile`-ийн `npm install`/Expo build

## Дараагийн алхам

**SOW-ийн 4 үе шат (P0–P3) бүгд код түвшинд хэрэгжсэн.** Одоо үлдсэн зүйлс нь код бичих ажил биш, харин:

1. `npm install` / `uv sync` хийж бодит орчинд (docker-compose) шалгах — эхний "жинхэнэ" ажиллуулалт энд болно, тул алдаа (import, migration дараалал, semver зөрчил) гарах магадлалтай.
2. Гадаад хамаарлууд шийдэгдэх (доор жагсаасан).
3. Хийгдээгүй үлдсэн жижиг зүйлс: S-12 (SEO — sitemap/schema.org), S-13 (хайлтын CTR/zero-result dashboard тусад нь), S-18-ийн бодит choropleth газрын зураг.
4. Хуулийн болон аюулгүй байдлын эцсийн шалгалт (P1-18 pentest, P3-09 хуульчийн дүгнэлт) — үүнгүйгээр production-д гарахгүй.

## Гадаад хамаарлын жагсаалт (энэ кодоор шийдэгдэхгүй)

1. **ДАН гэрээ** — OAuth2 client_id/secret, sandbox эрх авахгүйгээр P0-07-г L1(OTP)-оос цааш production-д ашиглах боломжгүй.
2. **e-barimt API эрх** — P1-01-ийг production горимд ажиллуулахад шаардлагатай.
3. **Хуульч** — DPIA, зөвшөөрлийн текст, moderation policy, P3-09 эцсийн хяналт батлуулах (PM+EXT).
4. **Pentester** — OWASP ASVS L2 pentest (P1-18).
5. **Тэмдэглэгчид** — 15,000 moderation дээж, gold set (P0-12, S-08).
6. **Бодит хэрэглэгчид** — card sorting/tree test (S-01), usability тест (K12, S-16, S-20), red-team (K4/K5, P2-14), хаалттай бета 1,000 хэрэглэгч (P3-10), moderator сургалт (P3-08).
7. **PaddleOCR/XLM-R/e5 загвар** — P1-03/P1-08/P2-10 interface бэлэн, гэхдээ бодит загвар татаж (HuggingFace) эсвэл P0-12-ийн өгөгдөл дээр сургах шаардлагатай.
8. **`npm install`/`pip install`** — энэ орчинд сүлжээ/registry хандалт байхгүй тул хийгдээгүй; Node/Python dependency-үүд tsconfig/pyproject-д зарлагдсан ч суулгаагүй.
9. **LLM moderation endpoint** — P2-05 нь бодит Anthropic/OpenAI API түлхүүр тохируулаагүй.
10. **LightGBM fraud загвар** — синтетик өгөгдөр дээр AUC>0.9 батлагдсан ч бодит SOW acceptance зөвхөн бодит fraud/normal өгөгдөр дээр дахин сургаж баталгаажна.
11. **Ирцийн (P3-03) эх сурвалж** — SOW өөрөө "Өгөгдлийн эх сурвалж" гэж тодорхойгүй үлдээсэн; тодорхой засгийн газрын open-data API сонгогдоогүй.
12. **Role-based auth** — moderator/law-enforcement эрхийн систем (P2-12, P3-06) одоогоор аль ч аутентификациятай хэрэглэгчид нээлттэй; production-д гарахаас өмнө заавал битүүлэх ёстой (P3 admin-hardening даалгавар, SOW-д тусад нь дурдагдаагүй ч зайлшгүй).
13. **Choropleth газрын зураг** (S-18) — тойргийн GeoJSON хилийн өгөгдөл олдоогүй тул жагсаалт хэлбэрээр орлуулсан.
9. **LLM moderation endpoint** — P2-05 нь бодит Anthropic/OpenAI API түлхүүр тохируулаагүй тул одоогоор бүх borderline кейс `needs_human_review`-д унана (аюулгүй fallback, гэхдээ P2-12 багийн ачааллыг нэмэгдүүлнэ).
10. **LightGBM fraud загвар** — код бүрэн ажиллаж, синтетик өгөгдөр дээр AUC>0.9 баталгаажсан ч бодит SOW-ийн AUC≥0.93 acceptance зөвхөн бодит fraud/normal өгөгдөр дээр дахин сургаж баталгаажуулна.
