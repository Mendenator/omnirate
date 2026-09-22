import { CameraView, useCameraPermissions } from "expo-camera";
import { useState } from "react";
import { Button, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { attachEBarimtEvidence } from "../lib/api";
import type { RootStackParamList } from "../App";

type Props = NativeStackScreenProps<RootStackParamList, "QrScanner">;

// P1-12 acceptance: QR read <=2s, success rate >=95% (100 real receipts).
// expo-camera's built-in barcode scanning (not a separate scanner lib) keeps
// the frame-to-decode path in native code, which is where that latency
// budget is actually won or lost.
export default function QrScannerScreen({ route, navigation }: Props) {
  const { reviewId } = route.params;
  const [permission, requestPermission] = useCameraPermissions();
  const [status, setStatus] = useState<string | null>(null);
  const [scanned, setScanned] = useState(false);

  if (!permission) return <View />;
  if (!permission.granted) {
    return (
      <View style={{ padding: 24 }}>
        <Text>Камерын зөвшөөрөл хэрэгтэй</Text>
        <Button title="Зөвшөөрөх" onPress={requestPermission} />
      </View>
    );
  }

  async function handleScan({ data }: { data: string }) {
    if (scanned) return;
    setScanned(true);
    setStatus("Шалгаж байна...");
    try {
      const result = await attachEBarimtEvidence(reviewId, data);
      setStatus(`✅ Баталгаажлаа (PoE ${result.poe_level})`);
      setTimeout(() => navigation.navigate("Home"), 1500);
    } catch (e) {
      setStatus(`❌ ${e instanceof Error ? e.message : "Алдаа"}`);
      setScanned(false);
    }
  }

  return (
    <View style={{ flex: 1 }}>
      <CameraView
        style={{ flex: 1 }}
        barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
        onBarcodeScanned={scanned ? undefined : handleScan}
      />
      {status && (
        <View style={{ position: "absolute", bottom: 24, left: 0, right: 0, alignItems: "center" }}>
          <Text style={{ backgroundColor: "white", padding: 8 }}>{status}</Text>
        </View>
      )}
    </View>
  );
}
