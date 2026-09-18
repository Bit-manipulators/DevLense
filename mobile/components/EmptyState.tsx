import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

export function EmptyState({ title, body }: { title: string; body: string }) {
  return <View style={styles.wrap}><Text style={styles.title}>{title}</Text><Text style={styles.body}>{body}</Text></View>;
}

const styles = StyleSheet.create({
  wrap: { alignItems: "center", borderColor: colors.border, borderRadius: 16, borderWidth: 1, borderStyle: "dashed", padding: spacing.xl, gap: spacing.sm },
  title: { color: colors.text, fontWeight: "800" },
  body: { color: colors.muted, textAlign: "center", lineHeight: 20 }
});

