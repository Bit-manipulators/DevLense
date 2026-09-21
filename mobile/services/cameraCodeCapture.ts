import * as ImagePicker from "expo-image-picker";

import { extractCodeFromImage } from "@/services/api";
import { Language } from "@/types/api";
import { CameraCaptureResult, CameraCodeCaptureService } from "@/types/future";

class ExpoCameraCodeCaptureService implements CameraCodeCaptureService {
  async captureCode(hintLanguage?: string): Promise<CameraCaptureResult> {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      throw new Error("Camera permission is required to photograph and scan code.");
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ["images"],
      allowsEditing: false,
      quality: 0.7,
      base64: true,
    });

    if (result.canceled || !result.assets || result.assets.length === 0) {
      throw new Error("Camera capture was cancelled.");
    }

    const asset = result.assets[0];
    if (!asset.base64) {
      throw new Error("Failed to process captured image data.");
    }

    const ocrResponse = await extractCodeFromImage({
      image_base64: asset.base64,
      hint_language: hintLanguage as Language | undefined,
    });

    return {
      code: ocrResponse.code,
      detectedLanguage: ocrResponse.detected_language,
      confidence: ocrResponse.confidence,
      imageUri: asset.uri,
      provider: ocrResponse.provider,
      errorMessage: ocrResponse.error_message,
    };
  }

  async captureFromGallery(hintLanguage?: string): Promise<CameraCaptureResult> {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      throw new Error("Photo library permission is required to import code screenshots.");
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      allowsEditing: false,
      quality: 0.7,
      base64: true,
    });

    if (result.canceled || !result.assets || result.assets.length === 0) {
      throw new Error("Photo selection was cancelled.");
    }

    const asset = result.assets[0];
    if (!asset.base64) {
      throw new Error("Failed to process selected image data.");
    }

    const ocrResponse = await extractCodeFromImage({
      image_base64: asset.base64,
      hint_language: hintLanguage as Language | undefined,
    });

    return {
      code: ocrResponse.code,
      detectedLanguage: ocrResponse.detected_language,
      confidence: ocrResponse.confidence,
      imageUri: asset.uri,
      provider: ocrResponse.provider,
      errorMessage: ocrResponse.error_message,
    };
  }
}

export const cameraCodeCapture: CameraCodeCaptureService = new ExpoCameraCodeCaptureService();
