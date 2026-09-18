export interface CameraCodeCaptureService {
  captureCode(): Promise<{ code: string; detectedLanguage?: string }>;
}

export interface VoiceInputService {
  captureQuestion(): Promise<string>;
}

