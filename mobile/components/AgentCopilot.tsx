import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { Feather } from "@expo/vector-icons";

import { colors, spacing } from "@/constants/theme";
import { sendAgentChatMessage } from "@/services/api";
import { Language } from "@/types/api";

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  codeSnippet?: string;
  model?: string;
}

interface Props {
  code: string;
  language: Language;
  errorMessage?: string;
  question?: string;
  findingSummary?: string;
  sessionId?: string;
  onApplyCode?: (newCode: string) => void;
  onTestCode?: (newCode: string) => void;
}

export function AgentCopilot({
  code,
  language,
  errorMessage = "",
  question = "",
  findingSummary = "",
  sessionId,
  onApplyCode,
  onTestCode,
}: Props) {
  const [expanded, setExpanded] = useState(false);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeModel, setActiveModel] = useState<string>("Ollama / Heuristic Agent");
  const [messages, setMessages] = useState<MessageItem[]>([
    {
      id: "initial",
      role: "assistant",
      content:
        "Hello! I am your AI Debugging Agent. I've analyzed your session context. You can ask me to break down time/space complexity, generate edge-case test suites, or provide alternative fix implementations.",
    },
  ]);

  const sendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || loading) return;

    const userMsgId = Date.now().toString();
    const newMessages: MessageItem[] = [
      ...messages,
      { id: userMsgId, role: "user", content: query },
    ];
    setMessages(newMessages);
    setInputText("");
    setLoading(true);
    if (!expanded) setExpanded(true);

    try {
      const historyPayload = newMessages.slice(-6).map((m) => ({
        role: m.role as "user" | "assistant",
        content: m.content,
      }));

      const res = await sendAgentChatMessage({
        code,
        language,
        error_message: errorMessage,
        question,
        finding_summary: findingSummary,
        session_id: sessionId,
        user_message: query,
        history: historyPayload,
      });

      if (res.model) {
        setActiveModel(res.model.includes("ollama") ? "Ollama Active" : "Heuristic Copilot");
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: res.reply,
          codeSnippet: res.code_snippet,
          model: res.model,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "⚠️ Unable to reach the AI agent service. Please verify that the DevLens backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header Toggle */}
      <Pressable
        onPress={() => setExpanded(!expanded)}
        style={styles.header}
        accessibilityRole="button"
        accessibilityLabel="Toggle AI Debugging Copilot"
      >
        <View style={styles.headerLeft}>
          <View style={styles.agentIconWrapper}>
            <Feather name="cpu" size={15} color={colors.primary} />
          </View>
          <View>
            <Text style={styles.headerTitle}>DEVLENS COPILOT</Text>
            <View style={styles.modelStatusRow}>
              <View style={styles.statusDot} />
              <Text style={styles.modelText}>{activeModel}</Text>
            </View>
          </View>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.toggleHint}>{expanded ? "Collapse" : "Ask Copilot"}</Text>
          <Feather
            name={expanded ? "chevron-down" : "chevron-up"}
            size={18}
            color={colors.primary}
          />
        </View>
      </Pressable>

      {/* Quick Prompt Chips */}
      <View style={styles.chipsRow}>
        <Pressable
          onPress={() => sendMessage("Explain the Big-O time and space complexity of this code.")}
          style={styles.chip}
          accessibilityRole="button"
        >
          <Feather name="zap" size={11} color={colors.primary} />
          <Text style={styles.chipText}>Explain Big-O</Text>
        </Pressable>

        <Pressable
          onPress={() => sendMessage("Generate 3 edge cases and boundary unit tests for this function.")}
          style={styles.chip}
          accessibilityRole="button"
        >
          <Feather name="check-circle" size={11} color={colors.primary} />
          <Text style={styles.chipText}>Edge Cases</Text>
        </Pressable>

        <Pressable
          onPress={() => sendMessage("Suggest an alternative fix using defensive programming.")}
          style={styles.chip}
          accessibilityRole="button"
        >
          <Feather name="repeat" size={11} color={colors.primary} />
          <Text style={styles.chipText}>Alternative Fix</Text>
        </Pressable>
      </View>

      {/* Expanded Chat Drawer */}
      {expanded ? (
        <View style={styles.drawerBody}>
          <ScrollView
            style={styles.messagesScroll}
            contentContainerStyle={styles.messagesContainer}
            nestedScrollEnabled
          >
            {messages.map((msg) => (
              <View
                key={msg.id}
                style={[
                  styles.messageBubble,
                  msg.role === "user" ? styles.userBubble : styles.assistantBubble,
                ]}
              >
                <Text style={styles.messageRole}>
                  {msg.role === "user" ? "YOU" : "COPILOT"}
                </Text>
                <Text style={styles.messageContent}>{msg.content}</Text>

                {/* Candidate Code Snippet Card */}
                {msg.codeSnippet ? (
                  <View style={styles.snippetCard}>
                    <View style={styles.snippetHeader}>
                      <Text style={styles.snippetTitle}>PROPOSED CODE / TEST</Text>
                      <View style={styles.snippetActions}>
                        {onApplyCode ? (
                          <Pressable
                            onPress={() => onApplyCode(msg.codeSnippet!)}
                            style={styles.snippetBtn}
                            accessibilityRole="button"
                          >
                            <Feather name="check" size={11} color={colors.primary} />
                            <Text style={styles.snippetBtnText}>Apply</Text>
                          </Pressable>
                        ) : null}
                        {onTestCode ? (
                          <Pressable
                            onPress={() => onTestCode(msg.codeSnippet!)}
                            style={styles.snippetBtn}
                            accessibilityRole="button"
                          >
                            <Feather name="play" size={11} color={colors.primary} />
                            <Text style={styles.snippetBtnText}>Test</Text>
                          </Pressable>
                        ) : null}
                      </View>
                    </View>
                    <Text style={styles.snippetText}>{msg.codeSnippet}</Text>
                  </View>
                ) : null}
              </View>
            ))}

            {loading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={styles.loadingText}>Copilot is analyzing code in sandbox...</Text>
              </View>
            ) : null}
          </ScrollView>

          {/* Input Bar */}
          <View style={styles.inputRow}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Ask Copilot about this bug or fix..."
              placeholderTextColor={colors.muted}
              multiline={false}
              onSubmitEditing={() => sendMessage()}
            />
            <Pressable
              onPress={() => sendMessage()}
              disabled={loading || !inputText.trim()}
              style={[
                styles.sendBtn,
                (!inputText.trim() || loading) && styles.sendBtnDisabled,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Send message to Copilot"
            >
              <Feather name="send" size={15} color={colors.canvas} />
            </Pressable>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 16,
    overflow: "hidden",
    marginTop: spacing.md,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: spacing.md,
    backgroundColor: colors.surfaceRaised,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  agentIconWrapper: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: "rgba(94, 234, 212, 0.12)",
    borderWidth: 1,
    borderColor: "rgba(94, 234, 212, 0.3)",
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: {
    color: colors.text,
    fontSize: 13,
    fontWeight: "900",
    letterSpacing: 0.8,
  },
  modelStatusRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    marginTop: 2,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.success,
  },
  modelText: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "700",
  },
  headerRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
  },
  toggleHint: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  chipText: {
    color: colors.text,
    fontSize: 11,
    fontWeight: "700",
  },
  drawerBody: {
    padding: spacing.md,
    gap: spacing.sm,
  },
  messagesScroll: {
    maxHeight: 280,
  },
  messagesContainer: {
    gap: spacing.sm,
    paddingBottom: spacing.sm,
  },
  messageBubble: {
    borderRadius: 12,
    padding: spacing.sm + 2,
  },
  userBubble: {
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.primaryDark,
    borderWidth: 1,
    alignSelf: "flex-end",
    maxWidth: "85%",
  },
  assistantBubble: {
    backgroundColor: colors.code,
    borderColor: colors.border,
    borderWidth: 1,
    alignSelf: "flex-start",
    maxWidth: "96%",
  },
  messageRole: {
    color: colors.primary,
    fontSize: 9,
    fontWeight: "900",
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  messageContent: {
    color: colors.text,
    fontSize: 13,
    lineHeight: 19,
  },
  snippetCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 8,
    marginTop: spacing.sm,
    overflow: "hidden",
  },
  snippetHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: colors.surfaceRaised,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  snippetTitle: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
  snippetActions: {
    flexDirection: "row",
    gap: spacing.xs,
  },
  snippetBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    backgroundColor: colors.surface,
    borderColor: colors.primary,
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  snippetBtnText: {
    color: colors.primary,
    fontSize: 10,
    fontWeight: "800",
  },
  snippetText: {
    color: colors.text,
    fontFamily: "monospace",
    fontSize: 12,
    lineHeight: 17,
    padding: spacing.sm,
  },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
  },
  loadingText: {
    color: colors.muted,
    fontSize: 12,
    fontStyle: "italic",
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    marginTop: spacing.xs,
  },
  textInput: {
    flex: 1,
    backgroundColor: colors.surfaceRaised,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    color: colors.text,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 8,
    fontSize: 13,
  },
  sendBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  sendBtnDisabled: {
    opacity: 0.4,
  },
});
