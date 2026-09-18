import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { colors, spacing } from "@/constants/theme";
import { healthCheck } from "@/services/api";
import { HealthResponse } from "@/types/api";

export default function SettingsScreen() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const check = async () => { setLoading(true); setError(null); try { setHealth(await healthCheck()); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to reach the backend."); } finally { setLoading(false); } };
  useEffect(() => { void check(); }, []);
  return <Screen>
    <Text style={styles.intro}>Connection details are deliberately visible: DevLens never makes local AI, OCR, voice, or laptop integration look enabled when it is not.</Text>
    {loading ? <LoadingState label="Checking DevLens server…" /> : null}<ErrorPanel message={error} />
    {health ? <Card><Detail label="BACKEND" value={health.status === "ok" ? "Connected" : health.status} good /><Detail label="ENVIRONMENT" value={health.environment} /><Detail label="DOCKER SANDBOX" value={health.execution_sandbox_available ? "Available" : "Unavailable — execution is safely disabled"} good={health.execution_sandbox_available} /></Card> : null}
    <Button label="Check connection" onPress={() => void check()} loading={loading} tone="secondary" />
    <Card><Text style={styles.heading}>FUTURE EXTENSIONS</Text><Text style={styles.body}>Camera/OCR, voice input, on-device models, Git diff analysis, and Office Kit sync have documented service boundaries but are not implemented in this MVP.</Text></Card>
    <Card><Text style={styles.heading}>PHONE SETUP</Text><Text style={styles.body}>Set EXPO_PUBLIC_API_URL to your computer’s LAN IP, not localhost, before opening the app on a physical Android device.</Text></Card>
  </Screen>;
}

function Detail({ label, value, good }: { label: string; value: string; good?: boolean }) { return <View style={styles.detail}><Text style={styles.heading}>{label}</Text><Text style={[styles.value, good === false && styles.bad]}>{value}</Text></View>; }
const styles = StyleSheet.create({ intro: { color: colors.muted, lineHeight: 21 }, detail: { gap: 4, marginBottom: spacing.md }, heading: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.8 }, value: { color: colors.text, fontWeight: "700" }, bad: { color: colors.warning }, body: { color: colors.text, lineHeight: 21, marginTop: spacing.sm } });

