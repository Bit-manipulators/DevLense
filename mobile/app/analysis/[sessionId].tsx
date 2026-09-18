import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import { useLocalSearchParams, useRouter } from "expo-router";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorPanel } from "@/components/ErrorPanel";
import { FixPanel } from "@/components/FixPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { SeverityBadge } from "@/components/SeverityBadge";
import { colors, spacing } from "@/constants/theme";
import { useDebugDraft } from "@/hooks/useDebugDraft";
import { getSession } from "@/services/api";
import { DebugSession } from "@/types/api";

export default function AnalysisScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const router = useRouter();
  const { updateDraft } = useDebugDraft();
  const [session, setSession] = useState<DebugSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    void getSession(sessionId).then((item) => { if (mounted) setSession(item); }).catch((reason) => { if (mounted) setError(reason instanceof Error ? reason.message : "Unable to load analysis."); });
    return () => { mounted = false; };
  }, [sessionId]);

  if (error) return <Screen><ErrorPanel message={error} /><Button label="Back to dashboard" onPress={() => router.replace("/")} /></Screen>;
  if (!session) return <Screen><LoadingState label="Loading structured analysis…" /></Screen>;
  const applyFix = () => { updateDraft({ language: session.language, code: session.corrected_code, errorMessage: session.error_message, question: session.question }); router.replace("/new-session"); };
  const runFix = () => { updateDraft({ language: session.language, code: session.corrected_code, errorMessage: session.error_message, question: session.question }); router.push({ pathname: "/execution", params: { autoRun: "true", sessionId: session.id } }); };

  return <Screen>
    <View style={styles.top}><Text style={styles.eyebrow}>ANALYSIS COMPLETE</Text><SeverityBadge severity={session.severity} /></View>
    <Text style={styles.title}>{session.summary}</Text>
    <Card><Section title="ROOT CAUSE" body={session.root_cause} /><Section title="EXPLANATION" body={session.explanation} />{session.affected_lines.length ? <Section title="AFFECTED LINES" body={session.affected_lines.map((line) => `Line ${line}`).join(", ")} /> : null}<Section title="CONFIDENCE" body={`${Math.round(session.confidence * 100)}% — this is a likely diagnosis, not proof of every program behavior.`} /></Card>
    <Card><FixPanel fix={session.suggested_fix} code={session.corrected_code} /></Card>
    <Card><Text style={styles.sectionTitle}>DEBUGGING STEPS</Text>{session.debugging_steps.map((step, index) => <Text key={step} style={styles.step}>{index + 1}. {step}</Text>)}</Card>
    <Button label="Apply Suggested Fix" onPress={applyFix} /><Button label="Run Fixed Code" onPress={runFix} tone="secondary" /><Button label="Copy Fix" onPress={() => void Clipboard.setStringAsync(session.corrected_code)} tone="secondary" /><Button label="New Analysis" onPress={() => router.replace("/new-session")} tone="secondary" />
  </Screen>;
}

function Section({ title, body }: { title: string; body: string }) { return <View style={styles.section}><Text style={styles.sectionTitle}>{title}</Text><Text style={styles.body}>{body}</Text></View>; }
const styles = StyleSheet.create({ top: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" }, eyebrow: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 1 }, title: { color: colors.text, fontSize: 25, fontWeight: "900", lineHeight: 30 }, section: { gap: 5, marginBottom: spacing.md }, sectionTitle: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.9 }, body: { color: colors.text, lineHeight: 21 }, step: { color: colors.text, lineHeight: 23, marginTop: 5 } });

