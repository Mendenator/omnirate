"use client";

import Form from "@rjsf/core";
import type { RJSFSchema } from "@rjsf/utils";
import validator from "@rjsf/validator-ajv8";
import { useRouter } from "next/navigation";
import { useState, type ChangeEvent } from "react";

import type { CategorySchema, CategorySummary } from "../../../lib/api";

// P0-10: the whole form is one JSON Schema — the entity's own fields, plus the
// category's published schema nested under `attributes` — so a new category
// needs no code here, and rjsf does the validation and error display.
function buildSchema(category: CategorySchema): RJSFSchema {
  return {
    type: "object",
    required: ["branch_slug", "name"],
    properties: {
      name: { type: "string", title: "Нэр", minLength: 1 },
      branch_slug: { type: "string", title: "Салбар (жишээ: ulaanbaatar)", minLength: 1 },
      location_slug: { type: "string", title: "Байршил (жишээ: sukhbaatar-duureg)" },
      ttd: { type: "string", title: "ТТД (татвар төлөгчийн дугаар)" },
      lat: { type: "number", title: "Өргөрөг", minimum: -90, maximum: 90 },
      lon: { type: "number", title: "Уртраг", minimum: -180, maximum: 180 },
      attributes: { ...(category.json_schema as RJSFSchema), title: "Нэмэлт мэдээлэл" },
    },
  };
}

export default function NewEntityForm({
  categories,
  initialSchema,
  initialBranch,
}: {
  categories: CategorySummary[];
  initialSchema: CategorySchema | null;
  initialBranch: string;
}) {
  const router = useRouter();
  const [category, setCategory] = useState<CategorySchema | null>(initialSchema);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Held here (not rebuilt inline) so unrelated re-renders can't reset what was typed.
  const [data, setData] = useState<Record<string, unknown>>({
    branch_slug: initialBranch || undefined,
  });

  async function pickCategory(e: ChangeEvent<HTMLSelectElement>) {
    const slug = e.target.value;
    setLoadError(null);
    setStatus(null);
    // Another category's attributes don't belong to this one.
    setData((prev) => {
      const rest = { ...prev };
      delete rest.attributes;
      return rest;
    });
    if (!slug) {
      setCategory(null);
      return;
    }
    const res = await fetch(`/api/backend/v1/schemas/${slug}/latest`);
    if (!res.ok) {
      setCategory(null);
      setLoadError(`❌ Категорийн бүтцийг ачаалж чадсангүй (${res.status})`);
      return;
    }
    setCategory(await res.json());
  }

  async function create(formData: Record<string, unknown>) {
    if (!category) return;
    setBusy(true);
    setStatus(null);
    try {
      const res = await fetch("/api/backend/v1/entities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          category_slug: category.category_slug,
          schema_version: category.version,
          attributes: formData.attributes ?? {},
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setStatus(`❌ Алдаа (${res.status}): ${body.detail ?? "тодорхойгүй"}`);
        return;
      }
      const created: { id: string } = await res.json();
      router.push(`/entities/${created.id}`);
    } catch {
      setStatus("❌ Сервертэй холбогдож чадсангүй");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p>
        <label htmlFor="category">Категори</label>
        <br />
        <select id="category" value={category?.category_slug ?? ""} onChange={pickCategory}>
          <option value="">— сонгоно уу —</option>
          {categories.map((c) => (
            <option key={c.category_slug} value={c.category_slug}>
              {c.category_slug}
            </option>
          ))}
        </select>
      </p>
      {loadError && <p role="alert">{loadError}</p>}
      {category && (
        <Form
          key={category.category_slug}
          schema={buildSchema(category)}
          formData={data}
          onChange={(e) => setData(e.formData as Record<string, unknown>)}
          validator={validator}
          disabled={busy}
          onSubmit={(e) => create(e.formData as Record<string, unknown>)}
        >
          <button type="submit" disabled={busy}>
            {busy ? "Илгээж байна..." : "Нэмэх"}
          </button>
        </Form>
      )}
      {status && <p role="status">{status}</p>}
    </>
  );
}
