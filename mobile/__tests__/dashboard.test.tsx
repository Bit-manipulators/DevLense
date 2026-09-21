import { fireEvent, render, waitFor } from "@testing-library/react-native";

import Dashboard from "@/app/index";
import { DebugDraftProvider } from "@/hooks/useDebugDraft";

const mockPush = jest.fn();
jest.mock("expo-router", () => ({ useRouter: () => ({ push: mockPush }) }));
jest.mock("@expo/vector-icons", () => ({ Feather: "Feather" }));
jest.mock("@/services/api", () => ({
  getSessions: jest.fn().mockResolvedValue([]),
  getApiUrl: jest.fn().mockReturnValue("http://10.140.36.194:8001"),
}));

describe("Dashboard", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("renders the developer dashboard and empty history state", async () => {
    const screen = render(<DebugDraftProvider><Dashboard /></DebugDraftProvider>);
    expect(screen.getByText("AI DEBUGGING ASSISTANT")).toBeTruthy();
    expect(screen.getByLabelText("Start new debugging session")).toBeTruthy();
    expect(screen.getByLabelText("Open Settings")).toBeTruthy();
    await waitFor(() => expect(screen.getByText("No sessions yet")).toBeTruthy());
  });

  it("navigates to settings when settings button is pressed", async () => {
    const screen = render(<DebugDraftProvider><Dashboard /></DebugDraftProvider>);
    const settingsButton = screen.getByLabelText("Open Settings");
    fireEvent.press(settingsButton);
    expect(mockPush).toHaveBeenCalledWith("/settings");
    await waitFor(() => expect(screen.getByText("No sessions yet")).toBeTruthy());
  });
});
