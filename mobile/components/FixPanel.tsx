import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

export function FixPanel({ fix, code }: { fix: string; code: string }) {
  return <View style={styles.wrap}><Text style={styles.label}>SUGGESTED FIX</Text><Text style={styles.fix}>{fix}</Text><Text style={styles.label}>CORRECTED CODE</Text><Text selectable style={styles.code}>{code}</Text></View>;
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  label: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.8 },
  fix: { color: colors.text, lineHeight: 21 },
  code: { backgroundColor: colors.code, borderRadius: 10, color: colors.text, fontFamily: "monospace", fontSize: 12, lineHeight: 19, padding: spacing.sm }
});

