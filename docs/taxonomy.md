# Таксономи v0.1 (S-01)

SOW §5.1 шаардлага: ≤3 түвшин, түвшин бүрт ≤12 зүйл. Энэ бол хөгжүүлэлтийг эхлүүлэх **эхлэлийн таксономи** — эцсийн хувилбар нь 30 хэрэглэгчийн card sorting + tree testing (амжилт ≥80%) дараа батлагдана (`docs/PROGRESS.md`-д ⛔ гэж тэмдэглэсэн, код бус процесс).

Byршлын бүтэц (аймаг/хот → сум/дүүрэг → баг/хороо) нь энэ салбарын мод дээр **давхарладаггүй**, харин зэрэгцээ facet болж ажиллана (жишээ: `/eruul-mend/emneleg/ulaanbaatar/khan-uul/intermed`).

## Салбар → Категори (v0.1, эцсийн бус)

| Салбар (slug) | Категориуд (slug) |
|---|---|
| `hool-zoog` (Хоол, зоог) | `restoran`, `kafe`, `turgen-hool`, `bar`, `delivery-only` |
| `eruul-mend` (Эрүүл мэнд) | `emneleg`, `shudnii-emneleg`, `emiin-san`, `poliklinik`, `lab` |
| `bolovsrol` (Боловсрол) | `surguuli`, `tsetserleg`, `ikh-surguuli`, `dund-surguuli`, `mergejliin-surgalt` |
| `tur-alba` (Төрийн алба) | `uikh-gishuun`, `itkh-gishuun`, `zasag-darga`, `sum-darga` |

Категори бүр (жишээ нь `restoran`) `category_schemas`/`schema_registry_entries`-д JSON Schema + `search.facets` + `display.sections`-тэй хамт бүртгэгдэнэ (`apps/backend/app/schema_registry/`). Дэд түвшин (жишээ: "Хоолны төрөл" = итали/солонгос/монгол) нь категори биш, **facet утга** — ингэснээр модны гүн 3-аас хэтрэхгүй.

## URL бүтэц

```
/{салбар}/{категори}/{байршил}/{entity}
/eruul-mend/emneleg/ulaanbaatar/khan-uul/intermed
```

Байршилгүй жагсаалт: `/{салбар}/{категори}` (жишээ: `/hool-zoog/restoran`).

## Дараагийн алхам (S-01 дуусгах)

1. 30 хэрэглэгчтэй card sorting (энэ v0.1 жагсаалтыг эх материал болгон ашиглана).
2. Tree testing — амжилт ≥80% болтол давтан засна.
3. Батлагдсан таксономийг `schema_registry_entries` seed migration болгон бичих (`apps/backend/alembic/versions/`).
