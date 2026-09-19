import * as ImagePicker from "expo-image-picker";

import { extractCodeFromImage } from "@/services/api";
import { cameraCodeCapture } from "@/services/cameraCodeCapture";

jest.mock("expo-image-picker", () => ({
  requestCameraPermissionsAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  requestMediaLibraryPermissionsAsync: jest.fn(),
  launchImageLibraryAsync: jest.fn(),
}));

describe("Camera and OCR Code Capture", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    globalThis.fetch = jest.fn();
  });

  it("extractCodeFromImage sends POST request to /api/v1/ocr", async () => {
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        code: "def add(a, b):\n    return a + b",
        detected_language: "python",
        confidence: 0.95,
        provider: "tesseract",
      }),
    });

    const result = await extractCodeFromImage({
      image_base64: "dGVzdA==",
      hint_language: "python",
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/ocr"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ image_base64: "dGVzdA==", hint_language: "python" }),
      })
    );
    expect(result.code).toContain("def add");
    expect(result.detected_language).toBe("python");
    expect(result.confidence).toBe(0.95);
  });

  it("throws clear error when camera permission is denied", async () => {
    (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({
      granted: false,
    });

    await expect(cameraCodeCapture.captureCode()).rejects.toThrow(
      "Camera permission is required"
    );
  });

  it("launches camera and extracts code when permission is granted", async () => {
    (ImagePicker.requestCameraPermissionsAsync as jest.Mock).mockResolvedValue({
      granted: true,
    });
    (ImagePicker.launchCameraAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://temp/photo.jpg", base64: "base64photo" }],
    });
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        code: "console.log('hello')",
        detected_language: "javascript",
        confidence: 0.9,
        provider: "tesseract",
      }),
    });

    const result = await cameraCodeCapture.captureCode("javascript");
    expect(ImagePicker.launchCameraAsync).toHaveBeenCalledWith(
      expect.objectContaining({ mediaTypes: ["images"], base64: true })
    );
    expect(result.code).toBe("console.log('hello')");
    expect(result.detectedLanguage).toBe("javascript");
    expect(result.imageUri).toBe("file://temp/photo.jpg");
  });

  it("throws clear error when gallery permission is denied", async () => {
    (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({
      granted: false,
    });

    await expect(cameraCodeCapture.captureFromGallery()).rejects.toThrow(
      "Photo library permission is required"
    );
  });

  it("launches gallery and extracts code successfully", async () => {
    (ImagePicker.requestMediaLibraryPermissionsAsync as jest.Mock).mockResolvedValue({
      granted: true,
    });
    (ImagePicker.launchImageLibraryAsync as jest.Mock).mockResolvedValue({
      canceled: false,
      assets: [{ uri: "file://temp/screenshot.png", base64: "base64screenshot" }],
    });
    (globalThis.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        code: "#include <iostream>",
        detected_language: "cpp",
        confidence: 0.92,
        provider: "tesseract",
      }),
    });

    const result = await cameraCodeCapture.captureFromGallery("cpp");
    expect(ImagePicker.launchImageLibraryAsync).toHaveBeenCalled();
    expect(result.code).toBe("#include <iostream>");
    expect(result.detectedLanguage).toBe("cpp");
  });
});
