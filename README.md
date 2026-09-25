# OmniRate

| | | |
|---|---|---|
| **Repo** | [![GitHub](https://img.shields.io/badge/GitHub-Mendenator%2Fomnirate-181717?logo=github)](https://github.com/Mendenator/omnirate) | [![Stars](https://img.shields.io/github/stars/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/stargazers) |
| **Build** | [![CI](https://github.com/Mendenator/omnirate/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Mendenator/omnirate/actions/workflows/ci.yml) | [![codecov](https://codecov.io/gh/Mendenator/omnirate/branch/master/graph/badge.svg)](https://codecov.io/gh/Mendenator/omnirate) |
| **Release** | [![Release](https://img.shields.io/github/v/release/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/releases/latest) | [![Last commit](https://img.shields.io/github/last-commit/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/commits/master) |
| **License** | [![License](https://img.shields.io/github/license/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/blob/master/LICENSE) | [![Website](https://img.shields.io/badge/website-report-24615F)](https://claude.ai/artifact/Ej7rN32MerYjb6LBZ46krC) |
| **Activity** | [![Open Issues](https://img.shields.io/github/issues/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/issues) | [![Open PRs](https://img.shields.io/github/issues-pr/Mendenator/omnirate)](https://github.com/Mendenator/omnirate/pulls) |

Polymorphic Rating & Proof-of-Experience Engine — монорепо.

Хэрэгжилт нь [`OmniRate SOW v2.md`](./OmniRate%20SOW%20v2.md) баримтад заасан даалгаврын задаргаагаар явна (P0 → P1 → P2 → P3, S-01…S-20). Ажлын явцын бүртгэл: [`docs/PROGRESS.md`](./docs/PROGRESS.md).

> 📄 **[Мэргэжлийн бус хүнд зориулсан тайлан](https://claude.ai/artifact/Ej7rN32MerYjb6LBZ46krC)** — юу хийгдсэн, яагаад итгэж болохыг техникийн мэдлэггүй хүнд ч ойлгомжтой энгийн үгээр тайлбарласан гүйцэтгэлийн тайлан.

## Бүтэц

```
apps/
  backend/   FastAPI (domain logic, schema registry, PoE, moderation, search API)
  web/       Next.js (public site + admin UI)
  mobile/    Expo / React Native
infra/
  terraform/ Postgres+PostGIS, Redis, object storage, OpenSearch
docs/
  adr/       Architecture decision records
```

## Хэрэгжүүлэлтийн статус

Энэ бол production контракт (ДАН, e-barimt), хуулийн зөвшөөрөл, 7.5 FTE багийн бодит хүний процесс (usability тест, red-team, тэмдэглэгээ) шаарддаг 24 долоо хоногийн SOW. Энд зөвхөн **кодоор бүтээгдэх хэсгүүдийг** хэрэгжүүлж байгаа бөгөөд гадаад хамааралтай зүйлсийг тодорхой `STUB`/`TODO(external)` тэмдэглэгээгээр ялгасан. Дэлгэрэнгүй: [`docs/PROGRESS.md`](./docs/PROGRESS.md).

## Local dev

```bash
cp .env.example .env
docker compose up -d          # postgres, redis, opensearch
cd apps/backend
uv sync                       # эсвэл: pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```
