import { PropsWithChildren } from "react";
import { SafeAreaView } from "react-native-safe-area-context";
import { ScrollView, StyleSheet } from "react-native";

import { colors, spacing } from "@/constants/theme";

export function Screen({ children, scroll = true }: PropsWithChildren<{ scroll?: boolean }>) {
  if (!scroll) return <SafeAreaView edges={["top"]} style={styles.safe}>{children}</SafeAreaView>;
  return <SafeAreaView edges={["top"]} style={styles.safe}><ScrollView contentContainerStyle={styles.content}>{children}</ScrollView></SafeAreaView>;
}

const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: colors.canvas }, content: { padding: spacing.md, gap: spacing.md, paddingBottom: spacing.xl * 2 } });

