import { useState } from "react";
import { Button, Text, TextInput, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import { verifyOtp } from "../lib/api";
import { setToken } from "../lib/tokenStorage";
import type { RootStackParamList } from "../App";

type Props = NativeStackScreenProps<RootStackParamList, "Auth">;

// L1 (OTP) path — always available. The ДАН (L2+) button below is the
// preferred path once ДАН OAuth is wired into expo-auth-session; until then
// this screen demonstrates the fallback the SOW §7 risk table calls for.
export default function AuthScreen({ navigation }: Props) {
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleOtpLogin() {
    setError(null);
    try {
      const { access_token } = await verifyOtp(phone, otp);
      await setToken("omnirate_access_token", access_token);
      navigation.replace("Home");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Нэвтрэхэд алдаа гарлаа");
    }
  }

  return (
    <View style={{ padding: 24, gap: 12 }}>
      <Text>Утасны дугаар</Text>
      <TextInput value={phone} onChangeText={setPhone} keyboardType="phone-pad" style={{ borderWidth: 1, padding: 8 }} />
      <Text>OTP код</Text>
      <TextInput value={otp} onChangeText={setOtp} keyboardType="number-pad" style={{ borderWidth: 1, padding: 8 }} />
      <Button title="Нэвтрэх (L1)" onPress={handleOtpLogin} />
      <Button title="ДАН-аар нэвтрэх (L2) — удахгүй" disabled />
      {error && <Text style={{ color: "red" }}>{error}</Text>}
    </View>
  );
}
