import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { ErrorPanel } from "@/components/ErrorPanel";
import { LoadingState } from "@/components/LoadingState";
import { Screen } from "@/components/Screen";
import { colors, spacing } from "@/constants/theme";
import { getApiUrl, healthCheck, setCustomApiUrl, testApiUrl } from "@/services/api";
import { HealthResponse } from "@/types/api";

export default function SettingsScreen() {
  const [currentUrl, setCurrentUrl] = useState(getApiUrl());
  const [inputUrl, setInputUrl] = useState(getApiUrl());
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingUrl, setTestingUrl] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const check = async () => {
    setLoading(true);
    setError(null);
    try {
      setHealth(await healthCheck());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to reach the backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void check();
  }, []);

  const handleApplyUrl = async (candidate: string) => {
    const trimmed = candidate.trim().replace(/\/$/, "");
    if (!trimmed) {
      setError("Please enter a valid server URL.");
      return;
    }
    setTestingUrl(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const healthData = await testApiUrl(trimmed);
      setCustomApiUrl(trimmed);
      setCurrentUrl(trimmed);
      setInputUrl(trimmed);
      setHealth(healthData);
      setSuccessMessage(`Connected successfully to ${trimmed}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : `Failed to connect to ${trimmed}`);
    } finally {
      setTestingUrl(false);
    }
  };

  return (
    <Screen>
      <Text style={styles.intro}>
        Connect your mobile app to your 24/7 cloud backend on Render or to your PC over Wi-Fi / USB.
      </Text>

      <Card>
        <Text style={styles.heading}>SERVER CONNECTION</Text>
        <Detail label="ACTIVE ENDPOINT" value={currentUrl} />

        <Text style={styles.inputLabel}>SERVER URL (CLOUD OR LOCAL):</Text>
        <TextInput
          value={inputUrl}
          onChangeText={setInputUrl}
          placeholder="https://devlens-api.onrender.com"
          placeholderTextColor={colors.muted}
          autoCapitalize="none"
          autoCorrect={false}
          style={styles.input}
        />

        <View style={styles.presetRow}>
          <Text style={styles.presetLabel}>PRESETS:</Text>
          <Pressable
            onPress={() => setInputUrl("https://devlens-api.onrender.com")}
            style={({ pressed }) => [styles.presetPill, pressed && styles.presetPillPressed]}
          >
            <Text style={styles.presetText}>Render Cloud</Text>
          </Pressable>
          <Pressable
            onPress={() => setInputUrl("http://10.140.36.194:8001")}
            style={({ pressed }) => [styles.presetPill, pressed && styles.presetPillPressed]}
          >
            <Text style={styles.presetText}>PC Wi-Fi</Text>
          </Pressable>
          <Pressable
            onPress={() => setInputUrl("http://127.0.0.1:8001")}
            style={({ pressed }) => [styles.presetPill, pressed && styles.presetPillPressed]}
          >
            <Text style={styles.presetText}>USB / 127.0.0.1</Text>
          </Pressable>
        </View>

        <Button
          label={testingUrl ? "Connecting…" : "Save & Connect"}
          onPress={() => void handleApplyUrl(inputUrl)}
          loading={testingUrl}
        />
      </Card>

      {successMessage ? (
        <View style={styles.successBox}>
          <Text style={styles.successTitle}>CONNECTED</Text>
          <Text style={styles.successText}>{successMessage}</Text>
        </View>
      ) : null}

      <ErrorPanel message={error} />
      {loading ? <LoadingState label="Checking DevLens server…" /> : null}

      {health ? (
        <Card>
          <Text style={styles.heading}>LIVE SERVER STATUS</Text>
          <Detail label="BACKEND STATUS" value={health.status === "ok" ? "Connected (200 OK)" : health.status} good />
          <Detail label="ENVIRONMENT" value={health.environment.toUpperCase()} />
          <Detail
            label="DOCKER SANDBOX"
            value={health.execution_sandbox_available ? "Available" : "Unavailable (Host does not run Docker engine)"}
            good={health.execution_sandbox_available}
          />
        </Card>
      ) : null}

      <Card>
        <Text style={styles.heading}>CAMERA / OCR ENGINE</Text>
        <Detail label="STATUS" value="Active & Connected" good />
        <Detail label="PRIVACY" value="Zero Retention (In-Memory Processing)" good />
        <Text style={styles.body}>
          Photograph code directly with your camera or import screenshots from your gallery. Code is extracted, auto-detected, and presented in a live review modal.
        </Text>
      </Card>

      <Card>
        <Text style={styles.heading}>24/7 FREE CLOUD HOSTING</Text>
        <Text style={styles.body}>
          DevLens includes a pre-configured `render.yaml` blueprint. You can deploy this backend for free on Render.com directly from your GitHub repository with zero configuration!
        </Text>
      </Card>
    </Screen>
  );
}

function Detail({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <View style={styles.detail}>
      <Text style={styles.detailHeading}>{label}</Text>
      <Text style={[styles.detailValue, good === false && styles.bad]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  intro: { color: colors.muted, lineHeight: 21 },
  heading: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.8, marginBottom: spacing.sm },
  inputLabel: { color: colors.muted, fontSize: 11, fontWeight: "800", letterSpacing: 0.6, marginTop: spacing.sm, marginBottom: 4 },
  input: {
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    color: colors.text,
    fontSize: 14,
    paddingHorizontal: spacing.sm,
    paddingVertical: 10,
    marginBottom: spacing.sm,
  },
  presetRow: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: spacing.xs, marginBottom: spacing.md },
  presetLabel: { color: colors.muted, fontSize: 10, fontWeight: "800", marginRight: 2 },
  presetPill: { backgroundColor: colors.surfaceRaised, borderColor: colors.border, borderWidth: 1, borderRadius: 8, paddingHorizontal: 9, paddingVertical: 5 },
  presetPillPressed: { opacity: 0.7 },
  presetText: { color: colors.primary, fontSize: 11, fontWeight: "700" },
  successBox: {
    backgroundColor: "#063A2E",
    borderColor: colors.success,
    borderRadius: 12,
    borderWidth: 1,
    gap: 4,
    padding: spacing.md,
  },
  successTitle: { color: colors.success, fontSize: 11, fontWeight: "900", letterSpacing: 0.8 },
  successText: { color: colors.text, fontSize: 13, lineHeight: 19 },
  detail: { gap: 4, marginBottom: spacing.md },
  detailHeading: { color: colors.primary, fontSize: 11, fontWeight: "900", letterSpacing: 0.8 },
  detailValue: { color: colors.text, fontWeight: "700" },
  bad: { color: colors.warning },
  body: { color: colors.text, lineHeight: 21, marginTop: spacing.sm },
});
