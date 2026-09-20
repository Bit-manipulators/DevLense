import {
  AnalyzeRequest,
  AnalysisResponse,
  DebugSession,
  ExecuteRequest,
  ExecuteResponse,
  HealthResponse,
  OcrRequest,
  OcrResponse,
  SessionListItem
} from "@/types/api";

// Dynamically resolve API URL: automatically matches the browser's hostname
// (e.g. LAN IP 10.140.36.194 or localhost) so requests succeed on any phone or PC.
export function getApiUrl(): string {
  if (typeof window !== "undefined" && window.location?.hostname) {
    if (window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
      return `http://${window.location.hostname}:8001`;
    }
  }
  return (process.env.EXPO_PUBLIC_API_URL || "http://127.0.0.1:8001").replace(/\/$/, "");
}

const API_URL = getApiUrl();

export class DevLensApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "DevLensApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers }
    });
  } catch {
    throw new DevLensApiError(
      "Unable to connect to DevLens server. Check that the backend is running and the phone can reach its LAN IP."
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail;
    if (response.status === 404) {
      throw new DevLensApiError(
        `DevLens API was not found at ${API_URL}. Start the DevLens backend on port 8001, then restart Expo with --clear.`,
        response.status
      );
    }
    throw new DevLensApiError(
      typeof message === "string" ? message : "DevLens could not complete that request.",
      response.status
    );
  }
  if (response.status === 204) {
    return undefined as unknown as T;
  }
  return response.json() as Promise<T>;
}

export const analyzeCode = (payload: AnalyzeRequest) =>
  request<AnalysisResponse>("/api/v1/analyze", { method: "POST", body: JSON.stringify(payload) });

export const executeCode = (payload: ExecuteRequest) =>
  request<ExecuteResponse>("/api/v1/execute", { method: "POST", body: JSON.stringify(payload) });

export const getSessions = () => request<SessionListItem[]>("/api/v1/sessions");
export const getSession = (id: string) => request<DebugSession>(`/api/v1/sessions/${id}`);
export const deleteSession = async (id: string): Promise<void> => {
  await request<undefined>(`/api/v1/sessions/${id}`, { method: "DELETE" });
};
export const healthCheck = () => request<HealthResponse>("/api/v1/health");

export const extractCodeFromImage = (payload: OcrRequest) =>
  request<OcrResponse>("/api/v1/ocr", { method: "POST", body: JSON.stringify(payload) });
