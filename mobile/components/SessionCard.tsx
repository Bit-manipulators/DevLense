import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";
import { SessionListItem } from "@/types/api";
import { SeverityBadge } from "./SeverityBadge";

export function SessionCard({ session, onPress }: { session: SessionListItem; onPress: () => void }) {
  return <Pressable accessibilityRole="button" accessibilityLabel={`Open ${session.summary}`} onPress={onPress} style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
    <View style={styles.row}><Text numberOfLines={1} style={styles.title}>{session.summary}</Text><SeverityBadge severity={session.severity} /></View>
    <Text style={styles.meta}>{session.language.toUpperCase()} · {Math.round(session.confidence * 100)}% confidence</Text>
  </Pressable>;
}

const styles = StyleSheet.create({
  card: { gap: spacing.sm, backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 14, padding: spacing.md },
  row: { alignItems: "center", flexDirection: "row", gap: spacing.sm },
  title: { color: colors.text, flex: 1, fontWeight: "800" },
  meta: { color: colors.muted, fontSize: 12, fontWeight: "700" },
  pressed: { opacity: 0.75 }
});

