import { act, fireEvent, render, waitFor } from "@testing-library/react-native";

import AnalysisScreen from "@/app/analysis/[sessionId]";
import NewDebugSession from "@/app/new-session";
import { DebugDraftProvider, useDebugDraft } from "@/hooks/useDebugDraft";
import { analyzeCode, getSession } from "@/services/api";
import { cameraCodeCapture } from "@/services/cameraCodeCapture";

const mockPush = jest.fn();
const mockReplace = jest.fn();

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useLocalSearchParams: () => ({ sessionId: "test-session-123" }),
  useFocusEffect: (cb: () => void) => {
    const React = require("react");
    React.useEffect(cb, [cb]);
  },
}));

jest.mock("@expo/vector-icons", () => ({ Feather: "Feather" }));

jest.mock("@/services/cameraCodeCapture", () => ({
  cameraCodeCapture: {
    captureCode: jest.fn(),
    captureFromGallery: jest.fn(),
  },
}));

jest.mock("@/services/api", () => {
  const actual = jest.requireActual("@/services/api");
  return {
    ...actual,
    analyzeCode: jest.fn(),
    getSession: jest.fn(),
  };
});

jest.setTimeout(20000);

describe("Regression Tests for Three Critical Bugs", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    globalThis.fetch = jest.fn();
  });

  // =========================================================================
  // TEST 1 — OCR TO EDITOR
  // =========================================================================
  describe("Test 1: OCR to Editor Pipeline", () => {
    it("successfully extracts OCR code and populates the editor with proper language", async () => {
      (cameraCodeCapture.captureCode as jest.Mock).mockResolvedValue({
        code: "#include <iostream>\nint main() { return 0; }",
        detectedLanguage: "cpp",
        confidence: 0.95,
        imageUri: "file://temp/photo.jpg",
      });

      const screen = render(
        <DebugDraftProvider>
          <NewDebugSession />
        </DebugDraftProvider>
      );

      const cameraButton = screen.getByLabelText("Scan code with camera");
      await act(async () => {
        fireEvent.press(cameraButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Code extracted successfully")).toBeTruthy();
      });

      // Extracted code reaches editor and review modal
      const editor = screen.getByLabelText("Source code editor");
      expect(editor.props.value).toContain("#include <iostream>");

      // User can freely edit the extracted code in the editor
      fireEvent.changeText(editor, "#include <iostream>\n// edited\nint main() { return 0; }");
      expect(editor.props.value).toContain("// edited");
    });

    it("displays clear error recovery when OCR detects no readable text", async () => {
      (cameraCodeCapture.captureCode as jest.Mock).mockResolvedValue({
        code: "",
        detectedLanguage: "python",
        confidence: 0.0,
        errorMessage: "No text found",
      });

      const screen = render(
        <DebugDraftProvider>
          <NewDebugSession />
        </DebugDraftProvider>
      );

      const cameraButton = screen.getByLabelText("Scan code with camera");
      await act(async () => {
        fireEvent.press(cameraButton);
      });

      await waitFor(() => {
        expect(screen.getByText("Could not read code clearly.")).toBeTruthy();
        expect(screen.getByText("Retake Photo")).toBeTruthy();
        expect(screen.getByText("Enter Code Manually")).toBeTruthy();
      });

      // Press Enter Code Manually clears the recovery card
      fireEvent.press(screen.getByText("Enter Code Manually"));
      expect(screen.queryByText("Could not read code clearly.")).toBeNull();
    });
  });

  // =========================================================================
  // TEST 2 — LANGUAGE ROUTING
  // =========================================================================
  describe("Test 2: Language Routing", () => {
    it("preserves cpp and dispatches correct language payload to API without defaulting to python", async () => {
      (analyzeCode as jest.Mock).mockResolvedValue({
        session_id: "cpp-session-1",
        language: "cpp",
        summary: "Off-by-one loop boundary (possible buffer overflow or out of bounds)",
        severity: "high",
        root_cause: "Loop condition i <= n exceeds bound",
        explanation: "0-indexed arrays run strictly less than bound",
        affected_lines: [1],
        suggested_fix: "Replace i <= n with i < n",
        corrected_code: "for(int i = 0; i < n; i++)",
        debugging_steps: [],
        confidence: 0.95,
      });

      const screen = render(
        <DebugDraftProvider>
          <NewDebugSession />
        </DebugDraftProvider>
      );

      // Select C++
      fireEvent.press(screen.getByText("C++"));

      // Enter C++ source code
      const editor = screen.getByLabelText("Source code editor");
      fireEvent.changeText(editor, "for(int i = 0; i <= n; i++)");

      // Press Analyze
      const analyzeButton = screen.getByText("Analyze Code");
      await act(async () => {
        fireEvent.press(analyzeButton);
      });

      expect(analyzeCode).toHaveBeenCalledWith(
        expect.objectContaining({
          language: "cpp",
          code: "for(int i = 0; i <= n; i++)",
        })
      );
      expect(mockPush).toHaveBeenCalledWith({
        pathname: "/analysis/[sessionId]",
        params: { sessionId: "cpp-session-1" },
      });
    });
  });

  // =========================================================================
  // TEST 3 — MANUAL OVERRIDE PRIORITY
  // =========================================================================
  describe("Test 3: Manual Override Priority", () => {
    it("does NOT let OCR detection override explicit user language selection", async () => {
      // OCR returns detectedLanguage: 'python'
      (cameraCodeCapture.captureCode as jest.Mock).mockResolvedValue({
        code: "for(int i = 0; i <= n; i++)",
        detectedLanguage: "python",
        confidence: 0.8,
        imageUri: "file://temp/photo.jpg",
      });

      let currentDraft: any = null;
      function TestObserver() {
        const { draft } = useDebugDraft();
        currentDraft = draft;
        return null;
      }

      const screen = render(
        <DebugDraftProvider>
          <NewDebugSession />
          <TestObserver />
        </DebugDraftProvider>
      );

      // 1. User explicitly selects C++
      fireEvent.press(screen.getByText("C++"));
      expect(currentDraft.language).toBe("cpp");
      expect(currentDraft.isExplicitLanguage).toBe(true);

      // 2. Camera scans and returns detectedLanguage='python'
      const cameraButton = screen.getByLabelText("Scan code with camera");
      await act(async () => {
        fireEvent.press(cameraButton);
      });

      // 3. User's explicit choice must win!
      expect(currentDraft.language).toBe("cpp");
    });
  });

  // =========================================================================
  // TEST 4 — PASTE FIXED CODE
  // =========================================================================
  describe("Test 4: Paste Fixed Code State Management", () => {
    it("replaces editor code with correctedCode while preserving originalCode", async () => {
      const mockSession = {
        id: "test-session-123",
        language: "cpp" as const,
        code: "for(int i = 0; i <= n; i++)",
        error_message: "",
        question: "",
        summary: "Off-by-one loop boundary",
        severity: "high" as const,
        root_cause: "i <= n",
        explanation: "Should be <",
        affected_lines: [1],
        suggested_fix: "Replace <= with <",
        corrected_code: "for(int i = 0; i < n; i++)",
        debugging_steps: ["Step 1"],
        confidence: 0.95,
        execution_count: 0,
        created_at: "2026-09-22T00:00:00Z",
      };

      (getSession as jest.Mock).mockResolvedValue(mockSession);

      let draftState: any = null;
      function DraftObserver() {
        const { draft } = useDebugDraft();
        draftState = draft;
        return null;
      }

      const screen = render(
        <DebugDraftProvider>
          <AnalysisScreen />
          <DraftObserver />
        </DebugDraftProvider>
      );

      await waitFor(() => {
        expect(screen.getByText("Off-by-one loop boundary")).toBeTruthy();
        expect(screen.getByLabelText("Paste Fixed Code")).toBeTruthy();
      });

      // Press "Paste Fixed Code"
      await act(async () => {
        fireEvent.press(screen.getByLabelText("Paste Fixed Code"));
      });

      // Verify currentEditorCode is correctedCode
      expect(draftState.code).toBe("for(int i = 0; i < n; i++)");
      // Verify originalCode is preserved
      expect(draftState.originalCode).toBe("for(int i = 0; i <= n; i++)");
      // Verify correctedCode is stored
      expect(draftState.correctedCode).toBe("for(int i = 0; i < n; i++)");
      // Verify navigation returned to new-session
      expect(mockReplace).toHaveBeenCalledWith("/new-session");
    });
  });
});
