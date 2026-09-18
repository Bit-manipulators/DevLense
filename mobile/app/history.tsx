import { Fragment, useCallback, useEffect, useState } from "react";
import { Alert, StyleSheet, Text } from "react-native";
import { useRouter } from "expo-router";

import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { SessionCard } from "@/components/SessionCard";
import { colors, spacing } from "@/constants/theme";
import { deleteSession, getSessions } from "@/services/api";
import { SessionListItem } from "@/types/api";

export default function HistoryScreen() {
  const router = useRouter();
  const [items, setItems] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => { setLoading(true); setError(null); try { setItems(await getSessions()); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to load history."); } finally { setLoading(false); } }, []);
  useEffect(() => { void load(); }, [load]);
  const remove = (id: string) => Alert.alert("Delete session?", "This will permanently remove its saved analysis and execution results.", [{ text: "Cancel", style: "cancel" }, { text: "Delete", style: "destructive", onPress: () => void deleteSession(id).then(load).catch((reason) => setError(reason instanceof Error ? reason.message : "Could not delete session.")) }]);

  return <Screen>
    <Text style={styles.subtitle}>Saved analyses persist locally in the backend SQLite database.</Text><Button label="Refresh" onPress={() => void load()} tone="secondary" />
    {loading ? <LoadingState label="Loading debugging history…" /> : null}<ErrorPanel message={error} />
    {!loading && !error && items.length === 0 ? <EmptyState title="History is empty" body="Every successful analysis is saved here." /> : null}
    {items.map((item) => <Fragment key={item.id}><SessionCard session={item} onPress={() => router.push({ pathname: "/analysis/[sessionId]", params: { sessionId: item.id } })} /><Text accessibilityRole="button" onPress={() => remove(item.id)} style={styles.delete}>Delete session</Text></Fragment>)}
  </Screen>;
}

const styles = StyleSheet.create({ subtitle: { color: colors.muted, lineHeight: 21 }, delete: { color: colors.danger, fontSize: 12, fontWeight: "800", marginTop: -spacing.sm, textAlign: "right" } });

