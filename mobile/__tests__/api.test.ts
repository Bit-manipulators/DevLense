import { analyzeCode, deleteSession, DevLensApiError } from "@/services/api";

describe("DevLens API client", () => {
  beforeEach(() => { globalThis.fetch = jest.fn(); });
  it("sends analysis requests through the dedicated API service", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({ ok: true, json: async () => ({ session_id: "id", severity: "high" }) });
    const result = await analyzeCode({ language: "python", code: "x = 1 / 0" });
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/analyze"), expect.objectContaining({ method: "POST" }));
    expect(result.session_id).toBe("id");
  });
  it("turns connectivity failures into a usable UI error", async () => {
    (globalThis.fetch as jest.Mock).mockRejectedValue(new Error("offline"));
    await expect(analyzeCode({ language: "python", code: "print(1)" })).rejects.toBeInstanceOf(DevLensApiError);
  });
  it("explains when a different local server answers the API request", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: "Not Found" }) });
    await expect(analyzeCode({ language: "python", code: "print(1)" })).rejects.toThrow("DevLens API was not found");
  });
  it("handles 204 No Content for deleteSession without parsing errors", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 204 });
    await expect(deleteSession("test-id")).resolves.toBeUndefined();
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/sessions/test-id"),
      expect.objectContaining({ method: "DELETE" })
    );
  });
});
