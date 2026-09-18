# Future capabilities

## Camera / OCR

The mobile client exposes a `CameraCodeCaptureService` interface but intentionally provides no fake implementation. A real provider should follow:

```text
Camera permission → image capture → OCR → code extraction → language detection → editor → analyzer
```

It needs consent, on-device image handling policy, OCR confidence display, and a user-editable review before analysis.

## Voice input

`VoiceInputService` provides the future seam for speech-to-text:

```text
Microphone permission → speech-to-text → question field → analyzer
```

Do not activate its UI until recording, transcription, error, consent, and deletion flows exist.

## Local AI and Git diff

New `AnalyzerProvider` implementations can add local models or Git-aware analysis while preserving the same `AnalysisFinding` contract. Treat a model as a fallible advisor; retain rule-based fallback.

