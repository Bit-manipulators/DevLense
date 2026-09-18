import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

export function ErrorPanel({ message }: { message: string | null }) {
  if (!message) return null;
  return <View accessibilityRole="alert" style={styles.panel}><Text style={styles.title}>REQUEST FAILED</Text><Text style={styles.message}>{message}</Text></View>;
}

const styles = StyleSheet.create({
  panel: { backgroundColor: "#3B1020", borderColor: colors.danger, borderWidth: 1, borderRadius: 12, padding: spacing.md, gap: 4 },
  title: { color: colors.danger, fontSize: 11, fontWeight: "900", letterSpacing: 0.8 },
  message: { color: colors.text, lineHeight: 20 }
});

