import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";
import { SessionListItem } from "@/types/api";
import { SeverityBadge } from "./SeverityBadge";

export function SessionCard({ session, onPress }: { session: SessionListItem; onPress: () => void }) {
  const summary = session?.summary || "Untitled Session";
  const language = (session?.language || "CODE").toUpperCase();
  const confidence = Math.round((session?.confidence ?? 0) * 100);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`Open ${summary}`}
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.row}>
        <Text numberOfLines={1} style={styles.title}>{summary}</Text>
        <SeverityBadge severity={session?.severity} />
      </View>
      <Text style={styles.meta}>{language} · {confidence}% confidence</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { gap: spacing.sm, backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 14, padding: spacing.md },
  row: { alignItems: "center", flexDirection: "row", gap: spacing.sm },
  title: { color: colors.text, flex: 1, fontWeight: "800" },
  meta: { color: colors.muted, fontSize: 12, fontWeight: "700" },
  pressed: { opacity: 0.75 }
});

