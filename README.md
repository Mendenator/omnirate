# OmniRate

[![GitHub](https://img.shields.io/badge/GitHub-Mendenator%2Fomnirate-181717?logo=github)](https://github.com/Mendenator/omnirate)
[![CI](https://github.com/Mendenator/omnirate/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Mendenator/omnirate/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)](https://github.com/Mendenator/omnirate/actions/workflows/ci.yml)

Polymorphic Rating & Proof-of-Experience Engine — монорепо.

Хэрэгжилт нь [`OmniRate SOW v2.md`](./OmniRate%20SOW%20v2.md) баримтад заасан даалгаврын задаргаагаар явна (P0 → P1 → P2 → P3, S-01…S-20). Ажлын явцын бүртгэл: [`docs/PROGRESS.md`](./docs/PROGRESS.md).

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
