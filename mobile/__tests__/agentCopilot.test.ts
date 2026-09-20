import { sendAgentChatMessage } from "@/services/api";

describe("Agent Copilot Service", () => {
  beforeEach(() => {
    globalThis.fetch = jest.fn();
  });

  it("sends chat request to /api/v1/agent/chat with code and context", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        reply: "The Big-O time complexity is O(N).",
        code_snippet: "def optimized(): pass",
        model: "ollama:qwen2.5-coder:7b",
      }),
    });

    const result = await sendAgentChatMessage({
      code: "for x in arr: pass",
      language: "python",
      user_message: "What is the time complexity?",
      finding_summary: "No defects found",
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/agent/chat"),
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("time complexity"),
      })
    );
    expect(result.reply).toContain("O(N)");
    expect(result.code_snippet).toBe("def optimized(): pass");
    expect(result.model).toContain("ollama");
  });
});
