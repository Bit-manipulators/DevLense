import { StyleSheet, Text, View } from "react-native";

import { colors } from "@/constants/theme";
import { Severity } from "@/types/api";

const tone: Record<Severity, string> = {
  low: colors.success,
  medium: colors.warning,
  high: "#FB923C",
  critical: colors.danger
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  const color = (severity && tone[severity]) ? tone[severity] : colors.warning;
  const label = (severity ? String(severity) : "INFO").toUpperCase();
  return <View style={[styles.badge, { borderColor: color }]}><Text style={[styles.text, { color }]}>{label}</Text></View>;
}

const styles = StyleSheet.create({
  badge: { alignSelf: "flex-start", borderRadius: 20, borderWidth: 1, paddingHorizontal: 9, paddingVertical: 4 },
  text: { fontSize: 11, fontWeight: "900", letterSpacing: 0.7 }
});

