import { LogBox, Platform } from "react-native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { DebugDraftProvider } from "@/hooks/useDebugDraft";
import { colors } from "@/constants/theme";

LogBox.ignoreLogs([
  "Failed to connect to MetaMask",
  /MetaMask/,
  /chrome-extension:\/\//,
  /moz-extension:\/\//,
]);

if (Platform.OS === "web" && typeof window !== "undefined") {
  const isExtensionError = (errorOrMessage: unknown, filename?: string) => {
    const text = String(errorOrMessage || "");
    const file = String(filename || "");
    return (
      text.includes("MetaMask") ||
      text.includes("inpage.js") ||
      file.includes("chrome-extension://") ||
      file.includes("moz-extension://")
    );
  };

  window.addEventListener(
    "error",
    (event) => {
      if (isExtensionError(event.message || event.error, event.filename)) {
        event.stopImmediatePropagation();
        event.preventDefault();
      }
    },
    true
  );

  window.addEventListener(
    "unhandledrejection",
    (event) => {
      if (isExtensionError(event.reason)) {
        event.stopImmediatePropagation();
        event.preventDefault();
      }
    },
    true
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <DebugDraftProvider>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.canvas },
            headerTintColor: colors.text,
            headerShadowVisible: false,
            contentStyle: { backgroundColor: colors.canvas },
          }}
        >
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="new-session" options={{ title: "New Debug Session" }} />
          <Stack.Screen name="analysis/[sessionId]" options={{ title: "Analysis" }} />
          <Stack.Screen name="execution" options={{ title: "Sandbox Output" }} />
          <Stack.Screen name="history" options={{ title: "Debug History" }} />
          <Stack.Screen name="settings" options={{ title: "Settings" }} />
        </Stack>
      </DebugDraftProvider>
    </SafeAreaProvider>
  );
}

