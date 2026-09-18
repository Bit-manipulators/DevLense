import { ActivityIndicator, Pressable, StyleSheet, Text, ViewStyle } from "react-native";

import { colors, spacing } from "@/constants/theme";

type Tone = "primary" | "secondary" | "danger";

interface Props {
  label: string;
  onPress: () => void;
  tone?: Tone;
  loading?: boolean;
  disabled?: boolean;
  style?: ViewStyle;
  accessibilityLabel?: string;
}

export function Button({ label, onPress, tone = "primary", loading, disabled, style, accessibilityLabel }: Props) {
  const isDisabled = disabled || loading;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      disabled={isDisabled}
      onPress={onPress}
      style={({ pressed }) => [styles.base, styles[tone], isDisabled && styles.disabled, pressed && styles.pressed, style]}
    >
      {loading ? <ActivityIndicator color={tone === "secondary" ? colors.text : colors.canvas} /> : <Text style={[styles.label, tone === "secondary" && styles.secondaryLabel]}>{label}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: { minHeight: 48, borderRadius: 12, paddingHorizontal: spacing.md, alignItems: "center", justifyContent: "center" },
  primary: { backgroundColor: colors.primary },
  secondary: { backgroundColor: colors.surfaceRaised, borderWidth: 1, borderColor: colors.border },
  danger: { backgroundColor: colors.danger },
  disabled: { opacity: 0.5 },
  pressed: { opacity: 0.8 },
  label: { fontSize: 15, fontWeight: "800", color: colors.canvas },
  secondaryLabel: { color: colors.text }
});

