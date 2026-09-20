import { useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { Feather } from "@expo/vector-icons";

import { Button } from "@/components/Button";
import { CameraScanModal } from "@/components/CameraScanModal";
import { Card } from "@/components/Card";
import { CodeEditor } from "@/components/CodeEditor";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LanguageSelector } from "@/components/LanguageSelector";
import { Screen } from "@/components/Screen";
import { colors, spacing } from "@/constants/theme";
import { useDebugDraft } from "@/hooks/useDebugDraft";
import { analyzeCode } from "@/services/api";
import { cameraCodeCapture } from "@/services/cameraCodeCapture";
import { Language } from "@/types/api";
import { CameraCaptureResult } from "@/types/future";
import { demoExamples } from "@/utils/demoData";

export default function NewDebugSession() {
  const router = useRouter();
  const { draft, updateDraft, clearDraft } = useDebugDraft();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [scanLoading, setScanLoading] = useState(false);
  const [scanResult, setScanResult] = useState<CameraCaptureResult | null>(null);
  const [showScanModal, setShowScanModal] = useState(false);

  const analyze = async () => {
    if (!draft.code.trim()) { setError("Add source code before starting an analysis."); return; }
    setLoading(true); setError(null);
    try {
      const result = await analyzeCode({ language: draft.language, code: draft.code, error_message: draft.errorMessage, question: draft.question });
      router.push({ pathname: "/analysis/[sessionId]", params: { sessionId: result.session_id } });
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Analysis failed. Please retry."); } finally { setLoading(false); }
  };

  const run = () => {
    if (!draft.code.trim()) { setError("Add source code before running it."); return; }
    setError(null);
    router.push({ pathname: "/execution", params: { autoRun: "true" } });
  };

  const handleScanCamera = async () => {
    setScanLoading(true);
    setError(null);
    try {
      const result = await cameraCodeCapture.captureCode(draft.language);
      setScanResult(result);
      setShowScanModal(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Camera capture failed.");
    } finally {
      setScanLoading(false);
    }
  };

  const handleScanGallery = async () => {
    setScanLoading(true);
    setError(null);
    try {
      const result = await cameraCodeCapture.captureFromGallery(draft.language);
      setScanResult(result);
      setShowScanModal(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Image import failed.");
    } finally {
      setScanLoading(false);
    }
  };

  const handleApplyScan = (code: string, language: Language) => {
    updateDraft({ code, language });
    setShowScanModal(false);
  };

  return <Screen>
    <Text style={styles.intro}>Paste or scan a code snippet, choose its language, and DevLens will diagnose errors and suggest fixes.</Text>
    <Text style={styles.label}>LANGUAGE</Text>
    <LanguageSelector value={draft.language} onChange={(language) => updateDraft({ language })} />

    <View style={styles.headingRow}>
      <Text style={styles.label}>SOURCE CODE</Text>
      <View style={styles.scanActions}>
        {scanLoading ? (
          <View style={styles.scanningIndicator}>
            <ActivityIndicator size="small" color={colors.primary} />
            <Text style={styles.scanningText}>Scanning OCR…</Text>
          </View>
        ) : (
          <>
            <Pressable
              onPress={handleScanCamera}
              style={({ pressed }) => [styles.actionPill, pressed && styles.actionPillPressed]}
              accessibilityRole="button"
              accessibilityLabel="Scan code with camera"
            >
              <Feather name="camera" size={13} color={colors.primary} />
              <Text style={styles.actionPillText}>Camera</Text>
            </Pressable>
            <Pressable
              onPress={handleScanGallery}
              style={({ pressed }) => [styles.actionPill, pressed && styles.actionPillPressed]}
              accessibilityRole="button"
              accessibilityLabel="Upload code image from gallery"
            >
              <Feather name="upload" size={13} color={colors.primary} />
              <Text style={styles.actionPillText}>Upload</Text>
            </Pressable>
          </>
        )}
        <Text onPress={() => updateDraft({ code: "" })} style={styles.clear}>Clear</Text>
      </View>
    </View>
    <CodeEditor value={draft.code} onChangeText={(code) => updateDraft({ code })} />

    <Text style={styles.label}>ERROR OR STACK TRACE <Text style={styles.optional}>OPTIONAL</Text></Text>
    <TextInput accessibilityLabel="Error or stack trace" autoCapitalize="none" multiline onChangeText={(errorMessage) => updateDraft({ errorMessage })} placeholder="Paste compiler output or stack trace…" placeholderTextColor={colors.muted} style={styles.textArea} textAlignVertical="top" value={draft.errorMessage} />
    <Text style={styles.label}>QUESTION <Text style={styles.optional}>OPTIONAL</Text></Text>
    <TextInput accessibilityLabel="Debugging question" multiline onChangeText={(question) => updateDraft({ question })} placeholder="e.g. Why is this causing a segmentation fault?" placeholderTextColor={colors.muted} style={styles.question} textAlignVertical="top" value={draft.question} />
    <ErrorPanel message={error} />
    <View style={styles.buttons}><Button label="Analyze Code" loading={loading} onPress={analyze} /><Button label="Run Code" disabled={loading} onPress={run} tone="secondary" /></View>
    <Text style={styles.label}>TRY A REAL EXAMPLE</Text>
    {demoExamples.map((example) => <Card key={example.title} style={styles.demo}><Text style={styles.demoTitle}>{example.title}</Text><Button label="Load demo" tone="secondary" onPress={() => updateDraft({ language: example.language, code: example.code, errorMessage: example.error, question: example.question })} /></Card>)}
    <Text onPress={clearDraft} style={styles.reset}>Reset all fields</Text>

    {scanResult ? (
      <CameraScanModal
        visible={showScanModal}
        imageUri={scanResult.imageUri}
        initialCode={scanResult.code}
        detectedLanguage={(scanResult.detectedLanguage as Language) || draft.language}
        confidence={scanResult.confidence ?? 0.8}
        provider={scanResult.provider}
        onApply={handleApplyScan}
        onRetake={handleScanCamera}
        onClose={() => setShowScanModal(false)}
      />
    ) : null}
  </Screen>;
}

const styles = StyleSheet.create({
  intro: { color: colors.muted, lineHeight: 21 },
  label: { color: colors.muted, fontSize: 11, fontWeight: "900", letterSpacing: 0.9 },
  optional: { color: colors.muted, fontWeight: "500" },
  headingRow: { alignItems: "center", flexDirection: "row", justifyContent: "space-between" },
  scanActions: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  actionPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  actionPillPressed: {
    opacity: 0.7,
    borderColor: colors.primary,
  },
  actionPillText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: "700",
  },
  scanningIndicator: { flexDirection: "row", alignItems: "center", gap: 6 },
  scanningText: { color: colors.primary, fontSize: 12, fontWeight: "700" },
  clear: { color: colors.muted, fontSize: 13, fontWeight: "800", marginLeft: 4 },
  textArea: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, color: colors.text, minHeight: 112, padding: spacing.md, fontFamily: "monospace", fontSize: 13 },
  question: { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: 12, borderWidth: 1, color: colors.text, minHeight: 84, padding: spacing.md },
  buttons: { gap: spacing.sm },
  demo: { alignItems: "center", flexDirection: "row", gap: spacing.sm, justifyContent: "space-between" },
  demoTitle: { color: colors.text, flex: 1, fontWeight: "800" },
  reset: { color: colors.muted, fontSize: 13, fontWeight: "700", textAlign: "center" }
});

