import { useEffect, useState } from "react";
import { Button, ScrollView, Switch, Text, TextInput, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import {
  createEntity,
  getCategorySchema,
  listCategories,
  type CategorySchema,
  type CategorySummary,
} from "../lib/api";
import type { RootStackParamList } from "../App";

type Props = NativeStackScreenProps<RootStackParamList, "NewEntity">;

// Mirrors apps/web/app/entities/new: category schema drives the attribute
// fields, so a new category needs no app-store release to become creatable
// here. No rjsf-equivalent exists on mobile, so attributes render as plain
// TextInput/Switch per property type instead of full JSON Schema validation.
export default function NewEntityScreen({ navigation }: Props) {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [categorySlug, setCategorySlug] = useState<string | null>(null);
  const [schema, setSchema] = useState<CategorySchema | null>(null);
  const [name, setName] = useState("");
  const [branchSlug, setBranchSlug] = useState("");
  const [locationSlug, setLocationSlug] = useState("");
  const [attributes, setAttributes] = useState<Record<string, string | boolean>>({});
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listCategories()
      .then(setCategories)
      .catch((e: unknown) => setStatus(e instanceof Error ? e.message : "Категори ачаалж чадсангүй"));
  }, []);

  function pickCategory(slug: string) {
    setCategorySlug(slug);
    setAttributes({});
    setStatus(null);
    getCategorySchema(slug)
      .then(setSchema)
      .catch((e: unknown) => setStatus(e instanceof Error ? e.message : "Бүтэц ачаалж чадсангүй"));
  }

  async function submit() {
    if (!schema || !categorySlug) return;
    if (!name.trim() || !branchSlug.trim()) {
      setStatus("❌ Нэр болон салбарыг бөглөнө үү");
      return;
    }
    setBusy(true);
    setStatus(null);
    try {
      // rjsf on web coerces numeric fields the same way — attributes is JSONB,
      // so an "integer" property saved as the string "5" would silently drift
      // from what the category schema (and anything reading it) expects.
      const coerced: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(attributes)) {
        const propType = properties[key]?.type;
        if (typeof value === "string" && value === "") continue;
        coerced[key] =
          typeof value === "string" && (propType === "integer" || propType === "number")
            ? Number(value)
            : value;
      }

      const result = await createEntity({
        categorySlug,
        schemaVersion: schema.version,
        name: name.trim(),
        branchSlug: branchSlug.trim(),
        locationSlug: locationSlug.trim(),
        attributes: coerced,
      });
      if ("unauthorized" in result) {
        navigation.navigate("Auth", { next: "NewEntity" });
        return;
      }
      setStatus(`✅ Нэмэгдлээ (${result.id})`);
      setName("");
      setLocationSlug("");
      setAttributes({});
    } catch (e) {
      setStatus(e instanceof Error ? `❌ ${e.message}` : "❌ Алдаа гарлаа");
    } finally {
      setBusy(false);
    }
  }

  const properties = schema?.json_schema.properties ?? {};

  return (
    <ScrollView contentContainerStyle={{ padding: 24, gap: 12 }}>
      <Text>Категори</Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
        {categories.map((c) => (
          <Button
            key={c.category_slug}
            title={c.category_slug}
            color={c.category_slug === categorySlug ? "#24615F" : undefined}
            onPress={() => pickCategory(c.category_slug)}
          />
        ))}
      </View>

      {schema && (
        <>
          <Text>Нэр</Text>
          <TextInput value={name} onChangeText={setName} style={{ borderWidth: 1, padding: 8 }} />
          <Text>Салбар (жишээ: ulaanbaatar)</Text>
          <TextInput value={branchSlug} onChangeText={setBranchSlug} style={{ borderWidth: 1, padding: 8 }} />
          <Text>Байршил (заавал биш)</Text>
          <TextInput value={locationSlug} onChangeText={setLocationSlug} style={{ borderWidth: 1, padding: 8 }} />

          {Object.entries(properties).map(([key, prop]) =>
            prop.type === "boolean" ? (
              <View key={key} style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                <Text>{prop.title ?? key}</Text>
                <Switch
                  value={Boolean(attributes[key])}
                  onValueChange={(v) => setAttributes((prev) => ({ ...prev, [key]: v }))}
                />
              </View>
            ) : (
              <View key={key}>
                <Text>{prop.title ?? key}</Text>
                <TextInput
                  value={typeof attributes[key] === "string" ? attributes[key] : ""}
                  onChangeText={(v) => setAttributes((prev) => ({ ...prev, [key]: v }))}
                  keyboardType={prop.type === "integer" || prop.type === "number" ? "numeric" : "default"}
                  style={{ borderWidth: 1, padding: 8 }}
                />
              </View>
            ),
          )}

          <Button title={busy ? "Илгээж байна..." : "Нэмэх"} onPress={submit} disabled={busy} />
        </>
      )}

      {status && <Text>{status}</Text>}
    </ScrollView>
  );
}
