"use client";

import Form from "@rjsf/core";
import validator from "@rjsf/validator-ajv8";
import { useEffect, useState } from "react";

/**
 * P0-10: renders the "attributes" step of the entity-creation form directly
 * from a category's published JSON Schema — no code change needed per
 * category (acceptance: 3 categories render without a code branch).
 */

interface CategorySchema {
  category_slug: string;
  version: number;
  json_schema: object;
}

export default function EntityAttributesForm({ categorySlug }: { categorySlug: string }) {
  const [schema, setSchema] = useState<CategorySchema | null>(null);
  const [formData, setFormData] = useState<Record<string, unknown>>({});

  useEffect(() => {
    fetch(`/api/backend/v1/schemas/${categorySlug}/latest`)
      .then((res) => (res.ok ? res.json() : null))
      .then(setSchema);
  }, [categorySlug]);

  if (!schema) return <p>Ачааллаж байна...</p>;

  return (
    <Form
      schema={schema.json_schema}
      formData={formData}
      validator={validator}
      onChange={(e) => setFormData(e.formData)}
      onSubmit={(e) => setFormData(e.formData)}
    />
  );
}
