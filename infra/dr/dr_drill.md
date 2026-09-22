# DR дасгал (P3-12)

**Зорилт:** RPO ≤5 мин, RTO ≤30 мин.

## 1. Postgres PITR restore drill

1. Дасгал эхлэхийн өмнө `measure_rpo_rto.py --record-baseline` ажиллуулж, сүүлийн committed мөрийн `created_at`-г бүртгэнэ (baseline).
2. Prod Postgres instance-ийг **унтраасан гэж симуляцлана** (жинхэнэ traffic-д нөлөөлөхгүйгээр stage орчинд гүйцэтгэнэ; prod дээр зөвхөн тохиролцсон maintenance цонхонд).
3. `infra/terraform/modules/postgres/user_data.sh.tftpl`-ийн WAL-G тохиргоог ашиглан шинэ instance дээр сэргээнэ:
   ```bash
   wal-g backup-fetch /var/lib/omnirate-postgres LATEST
   wal-g wal-replay --until "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
   ```
4. Сэргээлт дууссан цагийг тэмдэглэнэ (RTO эхлэл → энэ мөч).
5. `measure_rpo_rto.py --verify --baseline-file baseline.json --db-url <restored-db-url>` ажиллуулж RPO/RTO тайланг гаргана.

## 2. Хайлтын failover drill (S-19)

1. `infra/loadtest/k6/search_failover_load_test.js`-г 500 RPS-ээр эхлүүлнэ.
2. Ачааллын 5-р минутад OpenSearch 3 node-ын аль нэгийг унтраана (`terraform taint` эсвэл instance stop).
3. k6-ийн `http_req_failed` хувь ≤0.1% байгааг баталгаажуулна.
4. Node-ыг сэргээж, cluster `green` төлөвт орохыг хүлээнэ.

## Хүлээн авах шалгуур

| Хэмжүүр | Зорилт | Хэрхэн хэмжих |
|---|---|---|
| RPO | ≤5 мин | `measure_rpo_rto.py`-ийн baseline vs restored max(created_at) зөрүү |
| RTO | ≤30 мин | Алхам 2 эхлэх → алхам 4 дуусах хугацаа |
| Search failover error rate | ≤0.1% | k6 `http_req_failed` |
| K8, K9 failover үед | биелэх | k6 thresholds (`search_failover_load_test.js`) |

## Тэмдэглэл

Энэ дасгалыг гүйцэтгэхэд бодит cloud орчин (AWS instance унтраах/сэргээх эрх) шаардлагатай тул энэ sandbox-д гүйцэтгэгдээгүй ⛔ — доорх скрипт, runbook нь стейж орчинд шууд ашиглах боломжтойгоор бичигдсэн.
