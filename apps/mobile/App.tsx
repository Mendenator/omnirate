import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import AuthScreen from "./screens/AuthScreen";
import HomeScreen from "./screens/HomeScreen";
import NewEntityScreen from "./screens/NewEntityScreen";
import QrScannerScreen from "./screens/QrScannerScreen";
import ReviewScreen from "./screens/ReviewScreen";

export type RootStackParamList = {
  // `next`: where to land after a successful login — defaults to Home.
  // NewEntityScreen sends users here (and back) when POST /entities 401s.
  Auth: { next?: keyof RootStackParamList } | undefined;
  Home: undefined;
  NewEntity: undefined;
  Review: { entityId: string };
  QrScanner: { reviewId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// P0-11 skeleton + P1-12: ДАН OAuth2+PKCE / Play Integrity / App Attest
// wiring is still pending (see AuthScreen's disabled L2 button); OTP(L1)
// auth -> review submission -> e-barimt QR scan is the flow that's wired
// end-to-end today.
export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator id={undefined} initialRouteName="Auth">
        <Stack.Screen name="Auth" component={AuthScreen} options={{ title: "Нэвтрэх" }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: "OmniRate" }} />
        <Stack.Screen name="NewEntity" component={NewEntityScreen} options={{ title: "Шинэ газар нэмэх" }} />
        <Stack.Screen name="Review" component={ReviewScreen} options={{ title: "Үнэлгээ бичих" }} />
        <Stack.Screen name="QrScanner" component={QrScannerScreen} options={{ title: "e-barimt скан" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
