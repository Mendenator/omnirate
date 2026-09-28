import { Button, Text, View } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";

import type { RootStackParamList } from "../App";

type Props = NativeStackScreenProps<RootStackParamList, "Home">;

export default function HomeScreen({ navigation }: Props) {
  return (
    <View style={{ padding: 24, gap: 12 }}>
      <Text>Нэвтэрлээ. Хайлт, entity хуудас, review илгээх урсгал P1-д нэмэгдэнэ.</Text>
      <Button title="+ Шинэ газар нэмэх" onPress={() => navigation.navigate("NewEntity")} />
    </View>
  );
}
