import { StyleSheet, Text, TextInput, View } from "react-native";

import { colors, spacing } from "@/constants/theme";

interface Props {
  value: string;
  onChangeText: (value: string) => void;
  suspiciousLines?: number[];
}

export function CodeEditor({ value, onChangeText, suspiciousLines = [] }: Props) {
  const lines = Math.max(value.split("\n").length, 8);
  return (
    <View style={styles.container}>
      <View accessible={false} style={styles.gutter}>
        {Array.from({ length: lines }, (_, index) => {
          const line = index + 1;
          return <Text key={line} style={[styles.lineNo, suspiciousLines.includes(line) && styles.suspicious]}>{line}</Text>;
        })}
      </View>
      <TextInput
        accessibilityLabel="Source code editor"
        autoCapitalize="none"
        autoCorrect={false}
        multiline
        onChangeText={onChangeText}
        placeholder="Paste source code here…"
        placeholderTextColor={colors.muted}
        scrollEnabled={false}
        selectionColor={colors.primary}
        style={styles.input}
        textAlignVertical="top"
        value={value}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { minHeight: 245, flexDirection: "row", borderRadius: 12, overflow: "hidden", backgroundColor: colors.code, borderWidth: 1, borderColor: colors.border },
  gutter: { width: 40, paddingTop: spacing.sm + 2, paddingHorizontal: 8, backgroundColor: "#081423" },
  lineNo: { height: 20, lineHeight: 20, color: colors.muted, fontFamily: "monospace", fontSize: 12, textAlign: "right" },
  suspicious: { color: colors.danger, fontWeight: "900" },
  input: { flex: 1, minHeight: 245, color: colors.text, paddingTop: spacing.sm + 2, paddingBottom: spacing.sm + 2, paddingHorizontal: spacing.sm + 2, fontFamily: "monospace", fontSize: 13, lineHeight: 20 }
});

