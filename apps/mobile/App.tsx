import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import AuthScreen from "./screens/AuthScreen";
import HomeScreen from "./screens/HomeScreen";

export type RootStackParamList = {
  Auth: undefined;
  Home: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

// P0-11 skeleton: ДАН OAuth2+PKCE / Play Integrity / App Attest wiring lands
// with P1-12 (mobile review submission). This establishes the nav shell and
// the auth screen's contract with the backend (app/api/v1/auth.py).
export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Auth">
        <Stack.Screen name="Auth" component={AuthScreen} options={{ title: "Нэвтрэх" }} />
        <Stack.Screen name="Home" component={HomeScreen} options={{ title: "OmniRate" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
