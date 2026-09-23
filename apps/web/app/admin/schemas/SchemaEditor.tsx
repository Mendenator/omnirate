"use client";

import { useState } from "react";

/**
 * P0-09 + K7: lets a non-developer add a new category — with its attribute
 * fields, search facets, and entity-page sections — without a deploy. The
 * builder rows below compile down to the JSON Schema / search_config /
 * display_config shape that app/schema_registry/service.py validates and
 * publishes (POST /api/v1/schemas).
 */

type FieldType = "string" | "integer" | "boolean";

interface AttributeRow {
  field: string;
  label_mn: string;
  type: FieldType;
  facet: boolean;
}

const ALL_SECTIONS = [
  "summary",
  "criteria_breakdown",
  "reviews",
  "attributes",
  "map",
  "owner_reply",
];

export default function SchemaEditor() {
  const [categorySlug, setCategorySlug] = useState("");
  const [version, setVersion] = useState(1);
  const [rows, setRows] = useState<AttributeRow[]>([
    { field: "", label_mn: "", type: "string", facet: false },
  ]);
  const [sections, setSections] = useState<string[]>(["summary", "criteria_breakdown", "reviews"]);
  const [status, setStatus] = useState<string | null>(null);

  function updateRow(i: number, patch: Partial<AttributeRow>) {
    setRows((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { field: "", label_mn: "", type: "string", facet: false }]);
  }

  function removeRow(i: number) {
    setRows((prev) => prev.filter((_, idx) => idx !== i));
  }

  function toggleSection(section: string) {
    setSections((prev) =>
      prev.includes(section) ? prev.filter((s) => s !== section) : [...prev, section],
    );
  }

  async function publish() {
    setStatus("Илгээж байна...");

    const jsonSchema = {
      type: "object",
      properties: Object.fromEntries(
        rows.filter((r) => r.field).map((r) => [r.field, { type: r.type }]),
      ),
    };

    const searchConfig = {
      facets: rows
        .filter((r) => r.facet && r.field)
        .map((r, i) => ({
          field: r.field,
          type: r.type === "boolean" ? "bool" : r.type === "integer" ? "range" : "multi",
          label_mn: r.label_mn || r.field,
          order: i + 1,
        })),
      synonyms: [],
      default_sort: "relevance",
    };

    const displayConfig = { sections };

    const res = await fetch("/api/backend/v1/schemas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        category_slug: categorySlug,
        version,
        json_schema: jsonSchema,
        search_config: searchConfig,
        display_config: displayConfig,
      }),
    });

    if (res.ok) {
      setStatus(`✅ "${categorySlug}" v${version} нийтлэгдлээ.`);
    } else {
      const body = await res.json().catch(() => ({}));
      setStatus(`❌ Алдаа (${res.status}): ${body.detail ?? "тодорхойгүй"}`);
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: 24, fontFamily: "sans-serif" }}>
      <h1>Шинэ категори нэмэх</h1>
      <p>Код өөрчлөхгүйгээр шинэ категори, шүүлтүүр, хуудасны бүтэц үүсгэнэ (K7: ≤15 мин).</p>

      <label>
        Категорийн slug
        <input
          value={categorySlug}
          onChange={(e) => setCategorySlug(e.target.value)}
          placeholder="restoran"
        />
      </label>
      <label>
        Хувилбар
        <input
          type="number"
          min={1}
          value={version}
          onChange={(e) => setVersion(Number(e.target.value))}
        />
      </label>

      <h2>Талбарууд</h2>
      {rows.map((row, i) => (
        <div key={i} style={{ display: "flex", gap: 8, marginBottom: 4 }}>
          <input
            placeholder="field (жишээ: cuisine)"
            value={row.field}
            onChange={(e) => updateRow(i, { field: e.target.value })}
          />
          <input
            placeholder="Монгол нэр"
            value={row.label_mn}
            onChange={(e) => updateRow(i, { label_mn: e.target.value })}
          />
          <select
            value={row.type}
            onChange={(e) => updateRow(i, { type: e.target.value as FieldType })}
          >
            <option value="string">Текст</option>
            <option value="integer">Тоо</option>
            <option value="boolean">Тийм/Үгүй</option>
          </select>
          <label>
            <input
              type="checkbox"
              checked={row.facet}
              onChange={(e) => updateRow(i, { facet: e.target.checked })}
            />
            Шүүлтүүр
          </label>
          <button type="button" onClick={() => removeRow(i)}>
            −
          </button>
        </div>
      ))}
      <button type="button" onClick={addRow}>
        + Талбар нэмэх
      </button>

      <h2>Entity хуудасны блокууд</h2>
      {ALL_SECTIONS.map((s) => (
        <label key={s} style={{ marginRight: 12 }}>
          <input type="checkbox" checked={sections.includes(s)} onChange={() => toggleSection(s)} />
          {s}
        </label>
      ))}

      <div style={{ marginTop: 24 }}>
        <button type="button" onClick={publish} disabled={!categorySlug}>
          Нийтлэх
        </button>
        {status && <p>{status}</p>}
      </div>
    </div>
  );
}
