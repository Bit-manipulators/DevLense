# Implemented & Future capabilities

## Camera / OCR (Implemented)

The mobile client and backend provide complete Camera & OCR code capture via:

```text
Camera permission → image capture (expo-image-picker) → POST /api/v1/ocr (OcrService) → code extraction & language detection → CameraScanModal review → CodeEditor → analyzer
```

- **Zero-retention privacy:** Captured images are processed in-memory and never written to disk or the database.
- **Confidence meter:** Computes OCR recognition confidence and highlights warnings if review is needed.
- **Editable review:** Developers can inspect the scanned code, fix OCR character ambiguities, and confirm the detected language before inserting into the editor.

## Voice input

`VoiceInputService` provides the future seam for speech-to-text:

```text
Microphone permission → speech-to-text → question field → analyzer
```

Do not activate its UI until recording, transcription, error, consent, and deletion flows exist.

## Local AI and Git diff

New `AnalyzerProvider` implementations can add local models or Git-aware analysis while preserving the same `AnalysisFinding` contract. Treat a model as a fallible advisor; retain rule-based fallback.

