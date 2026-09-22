import {
  AgentChatRequest,
  AgentChatResponse,
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

export const DEFAULT_CLOUD_API_URL = "https://devlense.onrender.com";

let customApiUrl: string | null = null;
type ApiUrlListener = (url: string) => void;
const listeners: Set<ApiUrlListener> = new Set();

export function subscribeApiUrl(listener: ApiUrlListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function setCustomApiUrl(url: string | null): void {
  customApiUrl = url ? url.trim().replace(/\/$/, "") : null;
  const current = getApiUrl();
  listeners.forEach((listener) => {
    try {
      listener(current);
    } catch {
      // ignore
    }
  });
}

export function getCustomApiUrl(): string | null {
  return customApiUrl;
}

// Dynamically resolve API URL: supports custom URL, env variable, browser hostname, or Render Cloud default
export function getApiUrl(): string {
  if (customApiUrl) {
    return customApiUrl;
  }
  if (process.env.EXPO_PUBLIC_API_URL) {
    return process.env.EXPO_PUBLIC_API_URL.replace(/\/$/, "");
  }
  if (typeof window !== "undefined" && window.location?.hostname) {
    if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
      return "http://127.0.0.1:8001";
    }
    // If accessed via local network IP (e.g., 192.168.x.x:8081 or 10.x.x.x:8081)
    if (!window.location.hostname.includes(".onrender.com") && !window.location.hostname.includes("devlens")) {
      return `http://${window.location.hostname}:8001`;
    }
  }
  return DEFAULT_CLOUD_API_URL.replace(/\/$/, "");
}

export async function testApiUrl(candidateUrl: string): Promise<HealthResponse> {
  const cleanUrl = candidateUrl.trim().replace(/\/$/, "");
  let res: Response;
  try {
    res = await fetch(`${cleanUrl}/api/v1/health`, { method: "GET" });
  } catch {
    throw new Error(`Could not reach ${cleanUrl}. Check network connection or server status.`);
  }
  if (!res.ok) {
    throw new Error(`Server at ${cleanUrl} responded with HTTP ${res.status}.`);
  }
  return res.json() as Promise<HealthResponse>;
}

export class DevLensApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "DevLensApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = getApiUrl();
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers }
    });
  } catch {
    throw new DevLensApiError(
      `Unable to connect to DevLens server at ${baseUrl}. Verify the server is running or configure its URL in Settings.`
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = body?.detail;
    if (response.status === 404) {
      throw new DevLensApiError(
        `DevLens API was not found at ${baseUrl}. Verify the server route or start the backend on port 8001.`,
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

export const sendAgentChatMessage = (payload: AgentChatRequest) =>
  request<AgentChatResponse>("/api/v1/agent/chat", { method: "POST", body: JSON.stringify(payload) });
