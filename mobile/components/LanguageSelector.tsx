import { Pressable, StyleSheet, Text, View } from "react-native";

import { languages } from "@/constants/languages";
import { colors, spacing } from "@/constants/theme";
import { Language } from "@/types/api";

export function LanguageSelector({ value, onChange }: { value: Language; onChange: (value: Language) => void }) {
  return <View accessibilityLabel="Programming language" style={styles.row}>
    {languages.map((language) => (
      <Pressable
        key={language.value}
        accessibilityRole="radio"
        accessibilityState={{ selected: value === language.value }}
        onPress={() => onChange(language.value)}
        style={[styles.item, value === language.value && styles.selected]}
      >
        <Text style={[styles.text, value === language.value && styles.selectedText]}>{language.label}</Text>
      </Pressable>
    ))}
  </View>;
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  item: { borderRadius: 10, borderWidth: 1, borderColor: colors.border, paddingHorizontal: 10, paddingVertical: 8 },
  selected: { backgroundColor: colors.primaryDark, borderColor: colors.primary },
  text: { color: colors.muted, fontSize: 13, fontWeight: "700" },
  selectedText: { color: colors.primary }
});

