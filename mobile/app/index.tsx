import { useCallback, useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { Feather } from "@expo/vector-icons";

import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { SessionCard } from "@/components/SessionCard";
import { colors, spacing } from "@/constants/theme";
import { getApiUrl, getSessions } from "@/services/api";
import { SessionListItem } from "@/types/api";

export default function Dashboard() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setSessions(await getSessions()); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load history."); } finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const safeSessions = Array.isArray(sessions) ? sessions : [];

  return <Screen>
    <View style={styles.topRow}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>AI DEBUGGING ASSISTANT</Text>
        <Text style={styles.logo}>DEV<Text style={styles.accent}>LENS</Text></Text>
      </View>
      <Pressable
        style={({ pressed }) => [styles.settingsBtn, pressed && { opacity: 0.7 }]}
        onPress={() => router.push("/settings")}
        accessibilityLabel="Open Settings"
        accessibilityRole="button"
      >
        <Feather name="settings" size={22} color={colors.primary} />
      </Pressable>
    </View>

    <Text style={styles.tagline}>Find the fault. Understand the root cause. Validate the fix.</Text>

    <Pressable
      style={({ pressed }) => [styles.serverBadge, pressed && { opacity: 0.8 }]}
      onPress={() => router.push("/settings")}
      accessibilityLabel="Server Settings"
    >
      <View style={[styles.statusDot, { backgroundColor: error ? colors.danger : colors.success }]} />
      <Text style={styles.serverBadgeText} numberOfLines={1}>
        {error ? "Backend Unreachable • Tap to configure" : `Server: ${getApiUrl()}`}
      </Text>
      <Feather name="chevron-right" size={14} color={colors.muted} />
    </Pressable>

    <Button label="New Debug Session" onPress={() => router.push("/new-session")} accessibilityLabel="Start new debugging session" />
    <View style={styles.stats}>
      <Metric value={safeSessions.length.toString()} label="analyzed" />
      <Metric value={safeSessions.filter((item) => item?.severity && item.severity !== "low").length.toString()} label="bugs found" />
      <Metric value={safeSessions.reduce((total, item) => total + (item?.execution_count || 0), 0).toString()} label="fixes tested" />
    </View>
    <View style={styles.sectionHead}><Text style={styles.section}>RECENT SESSIONS</Text><Text onPress={() => router.push("/history")} style={styles.link}>View all</Text></View>
    {loading ? <LoadingState label="Loading sessions…" /> : <>{error ? <ErrorPanel message={error} actionLabel="Configure Server in Settings" onAction={() => router.push("/settings")} /> : null}{safeSessions.slice(0, 3).map((item) => <SessionCard key={item.id} session={item} onPress={() => router.push({ pathname: "/analysis/[sessionId]", params: { sessionId: item.id } })} />)}{!error && safeSessions.length === 0 ? <EmptyState title="No sessions yet" body="Start with a demo or paste the code that is giving you trouble." /> : null}</>}
    <Text style={styles.section}>SUPPORTED LANGUAGES</Text><View style={styles.languages}>{["Python", "C++", "JavaScript", "Java"].map((language) => <Text key={language} style={styles.pill}>{language}</Text>)}</View>
  </Screen>;
}

function Metric({ value, label }: { value: string; label: string }) { return <View style={styles.metric}><Text style={styles.metricValue}>{value}</Text><Text style={styles.metricLabel}>{label}</Text></View>; }
const styles = StyleSheet.create({
  topRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", paddingTop: spacing.lg },
  hero: { gap: 5 },
  eyebrow: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 1.3 },
  logo: { color: colors.text, fontSize: 38, fontWeight: "900", letterSpacing: -2 },
  accent: { color: colors.primary },
  settingsBtn: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1,
    height: 44,
    justifyContent: "center",
    width: 44,
  },
  tagline: { color: colors.muted, fontSize: 15, lineHeight: 22 },
  serverBadge: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  statusDot: { borderRadius: 4, height: 8, width: 8 },
  serverBadgeText: { color: colors.muted, flex: 1, fontSize: 12, fontWeight: "700" },
  stats: { flexDirection: "row", gap: spacing.sm },
  metric: { alignItems: "center", backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 14, borderWidth: 1, flex: 1, padding: spacing.md },
  metricValue: { color: colors.text, fontSize: 18, fontWeight: "900" },
  metricLabel: { color: colors.muted, fontSize: 11, fontWeight: "700", marginTop: 2 },
  sectionHead: { alignItems: "center", flexDirection: "row", justifyContent: "space-between", marginTop: spacing.sm },
  section: { color: colors.muted, fontSize: 11, fontWeight: "900", letterSpacing: 1 },
  link: { color: colors.primary, fontWeight: "800" },
  languages: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  pill: { backgroundColor: colors.surfaceRaised, borderRadius: 10, color: colors.text, fontSize: 12, fontWeight: "700", paddingHorizontal: 10, paddingVertical: 8 }
});
