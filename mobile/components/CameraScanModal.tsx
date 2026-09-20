import { useState, useEffect } from "react";
import { Image, Modal, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Feather } from "@expo/vector-icons";

import { Button } from "@/components/Button";
import { LanguageSelector } from "@/components/LanguageSelector";
import { colors, spacing } from "@/constants/theme";
import { Language } from "@/types/api";

interface Props {
  visible: boolean;
  imageUri?: string;
  initialCode: string;
  detectedLanguage?: Language;
  confidence?: number;
  provider?: string;
  onApply: (code: string, language: Language) => void;
  onRetake: () => void;
  onClose: () => void;
}

export function CameraScanModal({
  visible,
  imageUri,
  initialCode,
  detectedLanguage = "python",
  confidence = 0.8,
  provider,
  onApply,
  onRetake,
  onClose,
}: Props) {
  const [editedCode, setEditedCode] = useState(initialCode);
  const [selectedLanguage, setSelectedLanguage] = useState<Language>(detectedLanguage);

  useEffect(() => {
    setEditedCode(initialCode);
    setSelectedLanguage(detectedLanguage);
  }, [initialCode, detectedLanguage]);

  const confidencePercent = Math.round(confidence * 100);
  const isHighConfidence = confidence >= 0.75;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.modalCard}>
          <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
            <View style={styles.header}>
              <View>
                <Text style={styles.eyebrow}>DEV LENS OCR ENGINE</Text>
                <Text style={styles.title}>Scanned Code Review</Text>
              </View>
              <View style={[styles.confidenceBadge, isHighConfidence ? styles.confHigh : styles.confLow]}>
                <Feather
                  name={isHighConfidence ? "check-circle" : "alert-circle"}
                  size={12}
                  color={isHighConfidence ? "#4ade80" : "#facc15"}
                />
                <Text style={[styles.confidenceText, { color: isHighConfidence ? "#4ade80" : "#facc15" }]}>
                  {confidencePercent}% {isHighConfidence ? "Confidence" : "Review needed"}
                </Text>
              </View>
            </View>

            {imageUri ? (
              <View style={styles.previewContainer}>
                <Image source={{ uri: imageUri }} style={styles.thumbnail} resizeMode="contain" />
              </View>
            ) : null}

            <Text style={styles.sectionLabel}>DETECTED LANGUAGE</Text>
            <LanguageSelector value={selectedLanguage} onChange={setSelectedLanguage} />

            <View style={styles.codeHeaderRow}>
              <Text style={styles.sectionLabel}>EXTRACTED CODE</Text>
              <Text style={styles.instruction}>Review or adjust indentation below</Text>
            </View>
            <TextInput
              multiline
              autoCapitalize="none"
              autoCorrect={false}
              style={styles.codeEditor}
              value={editedCode}
              onChangeText={setEditedCode}
              placeholder="No code extracted"
              placeholderTextColor={colors.muted}
            />

            <View style={styles.privacyNote}>
              <Feather name="shield" size={13} color={colors.primary} />
              <Text style={styles.privacyText}>
                Zero retention: Captured photo is processed in-memory and never saved to the server.
              </Text>
            </View>

            <View style={styles.actions}>
              <Button
                label="Insert into Editor"
                onPress={() => onApply(editedCode, selectedLanguage)}
                accessibilityLabel="Insert scanned code into editor"
              />
              <View style={styles.secondaryActions}>
                <Button
                  label="Retake Photo"
                  onPress={onRetake}
                  tone="secondary"
                  style={styles.flexBtn}
                  accessibilityLabel="Retake code scan"
                />
                <Button
                  label="Cancel"
                  onPress={onClose}
                  tone="secondary"
                  style={styles.flexBtn}
                  accessibilityLabel="Cancel code scan"
                />
              </View>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.75)",
    justifyContent: "flex-end",
  },
  modalCard: {
    backgroundColor: colors.canvas,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    borderWidth: 1,
    borderColor: colors.border,
    maxHeight: "90%",
  },
  scrollContent: {
    padding: spacing.lg,
    gap: spacing.md,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
  },
  eyebrow: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "900",
    letterSpacing: 1.2,
  },
  title: {
    color: colors.text,
    fontSize: 22,
    fontWeight: "900",
  },
  confidenceBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  confHigh: {
    backgroundColor: "rgba(74, 222, 128, 0.15)",
    borderWidth: 1,
    borderColor: "#4ade80",
  },
  confLow: {
    backgroundColor: "rgba(250, 204, 21, 0.15)",
    borderWidth: 1,
    borderColor: "#facc15",
  },
  confidenceText: {
    color: colors.text,
    fontSize: 11,
    fontWeight: "800",
  },
  previewContainer: {
    height: 120,
    borderRadius: 10,
    overflow: "hidden",
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  sectionLabel: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 0.9,
  },
  codeHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  instruction: {
    color: colors.muted,
    fontSize: 11,
  },
  codeEditor: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    color: colors.text,
    minHeight: 160,
    maxHeight: 280,
    padding: spacing.md,
    fontFamily: "monospace",
    fontSize: 13,
    lineHeight: 19,
    textAlignVertical: "top",
  },
  privacyNote: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    padding: spacing.sm,
  },
  privacyText: {
    flex: 1,
    color: colors.muted,
    fontSize: 11,
    lineHeight: 16,
  },
  actions: {
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  secondaryActions: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  flexBtn: {
    flex: 1,
  },
});
