import { Platform } from "react-native";

/**
 * expo-secure-store has no web implementation at all (it's backed by
 * Keychain/Keystore, which don't exist in a browser) — calling it on web
 * throws "setValueWithKeyAsync is not a function" rather than degrading
 * gracefully. Native (iOS/Android) is this app's actual target per the SOW
 * ("Хамрахгүй: ... iOS/Android-аас бусад платформ"); web support here exists
 * only so the app can be exercised without a simulator during development —
 * localStorage is a reasonable stand-in for that purpose, but is NOT a
 * secure-storage equivalent and must never be treated as one for anything
 * that ships to real users on web.
 */

export async function setToken(key: string, value: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(key, value);
    return;
  }
  const SecureStore = await import("expo-secure-store");
  await SecureStore.setItemAsync(key, value);
}

export async function getToken(key: string): Promise<string | null> {
  if (Platform.OS === "web") {
    return localStorage.getItem(key);
  }
  const SecureStore = await import("expo-secure-store");
  return SecureStore.getItemAsync(key);
}
