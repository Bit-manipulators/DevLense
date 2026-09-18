import { CameraCodeCaptureService } from "@/types/future";

/**
 * Extension point only. No OCR is exposed in the UI until a real camera and OCR
 * provider is installed, so users never receive a fabricated scan result.
 */
export const cameraCodeCapture: CameraCodeCaptureService | undefined = undefined;

