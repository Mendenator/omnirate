import { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { submitReview } from "../lib/api";
import type { RootStackParamList } from "../App";

type Props = NativeStackScreenProps<RootStackParamList, "Review">;

// P1-12: review + e-barimt QR scan flow, mobile side. Submits the review
// first, then routes to QrScanner to attach e-barimt evidence — mirrors the
// web flow (apps/web/app/entities/[id]/review) so the PoE step-up story is
// consistent across platforms.
export default function ReviewScreen({ route, navigation }: Props) {
  const { entityId } = route.params;
  const [score, setScore] = useState("5");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    try {
      const review = await submitReview(entityId, Number(score), body);
      navigation.navigate("QrScanner", { reviewId: review.id });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Илгээхэд алдаа гарлаа");
    }
  }

  return (
    <View style={{ padding: 24, gap: 12 }}>
      <Text>Ерөнхий оноо (0-5)</Text>
      <TextInput value={score} onChangeText={setScore} keyboardType="decimal-pad" style={{ borderWidth: 1, padding: 8 }} />
      <Text>Тайлбар</Text>
      <TextInput value={body} onChangeText={setBody} multiline style={{ borderWidth: 1, padding: 8, minHeight: 80 }} />
      <Button title="Илгээх" onPress={handleSubmit} />
      {error && <Text style={{ color: "red" }}>{error}</Text>}
    </View>
  );
}
