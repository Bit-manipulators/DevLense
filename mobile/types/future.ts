export interface CameraCaptureResult {
  code: string;
  detectedLanguage?: string;
  confidence?: number;
  imageUri?: string;
  provider?: string;
}

export interface CameraCodeCaptureService {
  captureCode(hintLanguage?: string): Promise<CameraCaptureResult>;
  captureFromGallery(hintLanguage?: string): Promise<CameraCaptureResult>;
}

export interface VoiceInputService {
  captureQuestion(): Promise<string>;
}

