export const TOKEN_KEY = "omnirate_access_token";
const CHANGE_EVENT = "omnirate-auth-change";

// Only same-site paths: "//evil.example" and "https://…" would turn the
// post-login redirect into an open redirect.
export function safeNextPath(next: string | undefined): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

// localStorage throws in private windows / with site data blocked.
export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Login still "succeeds" for this page load but won't persist.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Nothing stored to clear.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

// For useSyncExternalStore: "storage" covers other tabs, CHANGE_EVENT this one.
export function subscribeToken(onChange: () => void): () => void {
  window.addEventListener("storage", onChange);
  window.addEventListener(CHANGE_EVENT, onChange);
  return () => {
    window.removeEventListener("storage", onChange);
    window.removeEventListener(CHANGE_EVENT, onChange);
  };
}
