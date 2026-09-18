import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { colors, spacing } from "@/constants/theme";
import { useDebugDraft } from "@/hooks/useDebugDraft";
import { executeCode } from "@/services/api";
import { ExecuteResponse } from "@/types/api";

export default function ExecutionScreen() {
  const { draft } = useDebugDraft();
  const { sessionId, autoRun } = useLocalSearchParams<{ sessionId?: string; autoRun?: string }>();
  const router = useRouter();
  const [result, setResult] = useState<ExecuteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = async () => {
    if (!draft.code.trim()) { setError("No code is loaded for execution."); return; }
    setLoading(true); setError(null); setResult(null);
    try { setResult(await executeCode({ language: draft.language, code: draft.code, session_id: sessionId })); } catch (reason) { setError(reason instanceof Error ? reason.message : "Unable to execute code."); } finally { setLoading(false); }
  };
  useEffect(() => { if (autoRun === "true") void run(); }, []); // user explicitly pressed Run Code before navigation

  return <Screen>
    <Text style={styles.intro}>Code is sent only to the Docker sandbox. The backend never executes it directly on the host.</Text>
    {loading ? <LoadingState label="Running in isolated sandbox…" /> : null}<ErrorPanel message={error} />
    {result ? <Card><View style={styles.row}><Text style={styles.status}>{result.success ? "EXECUTION SUCCEEDED" : "EXECUTION FAILED"}</Text><Text style={styles.meta}>exit {result.exit_code} · {result.execution_time_ms} ms</Text></View>{result.stdout ? <Output label="STDOUT" content={result.stdout} /> : null}{result.stderr ? <Output label="STDERR / COMPILER OUTPUT" content={result.stderr} error /> : null}</Card> : null}
    <Button label={result ? "Run Again" : "Run in Sandbox"} loading={loading} onPress={run} /><Button label="Back to Editor" onPress={() => router.replace("/new-session")} tone="secondary" />
  </Screen>;
}

function Output({ label, content, error = false }: { label: string; content: string; error?: boolean }) { return <View style={styles.outputWrap}><Text style={[styles.outputLabel, error && styles.errorLabel]}>{label}</Text><Text selectable style={styles.output}>{content}</Text></View>; }
const styles = StyleSheet.create({ intro: { color: colors.muted, lineHeight: 21 }, row: { gap: 3 }, status: { color: colors.primary, fontSize: 12, fontWeight: "900", letterSpacing: 0.8 }, meta: { color: colors.muted, fontSize: 12 }, outputWrap: { gap: spacing.sm, marginTop: spacing.md }, outputLabel: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.7 }, errorLabel: { color: colors.danger }, output: { backgroundColor: colors.code, borderRadius: 10, color: colors.text, fontFamily: "monospace", fontSize: 12, lineHeight: 19, padding: spacing.sm } });

