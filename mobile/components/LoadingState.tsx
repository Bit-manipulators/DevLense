import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

export function LoadingState({ label }: { label: string }) {
  return <View accessibilityRole="progressbar" style={styles.wrap}><ActivityIndicator color={colors.primary} /><Text style={styles.text}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  wrap: { alignItems: "center", gap: spacing.sm, paddingVertical: spacing.xl },
  text: { color: colors.muted, fontWeight: "700" }
});

