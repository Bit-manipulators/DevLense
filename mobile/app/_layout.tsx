import { LogBox, Platform, Text, View } from "react-native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { Button } from "@/components/Button";
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

// Global error handling for React Native native runtime
if (Platform.OS !== "web") {
  const globalAny = globalThis as any;
  if (globalAny.ErrorUtils) {
    const originalHandler = globalAny.ErrorUtils.getGlobalHandler?.();
    globalAny.ErrorUtils.setGlobalHandler((error: any, isFatal?: boolean) => {
      console.error("DevLens Native Global Error:", error);
      if (originalHandler) {
        try {
          originalHandler(error, false);
        } catch {
          // ignore to avoid crashing process
        }
      }
    });
  }
}

export function ErrorBoundary({ error, retry }: { error: Error; retry: () => void }) {
  return (
    <SafeAreaProvider>
      <View style={{ flex: 1, backgroundColor: colors.canvas, justifyContent: "center", alignItems: "center", padding: 24 }}>
        <Text style={{ color: colors.danger, fontSize: 20, fontWeight: "900", marginBottom: 12 }}>
          Application Error
        </Text>
        <Text style={{ color: colors.text, fontSize: 14, textAlign: "center", marginBottom: 24, lineHeight: 20 }}>
          {error?.message || "An unexpected error occurred while starting DevLens."}
        </Text>
        <Button label="Try Again" onPress={retry} />
      </View>
    </SafeAreaProvider>
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

