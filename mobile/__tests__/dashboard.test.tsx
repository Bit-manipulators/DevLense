import { render, waitFor } from "@testing-library/react-native";

import Dashboard from "@/app/index";
import { DebugDraftProvider } from "@/hooks/useDebugDraft";

jest.mock("expo-router", () => ({ useRouter: () => ({ push: jest.fn() }) }));
jest.mock("@/services/api", () => ({ getSessions: jest.fn().mockResolvedValue([]) }));

describe("Dashboard", () => {
  it("renders the developer dashboard and empty history state", async () => {
    const screen = render(<DebugDraftProvider><Dashboard /></DebugDraftProvider>);
    expect(screen.getByText("AI DEBUGGING ASSISTANT")).toBeTruthy();
    expect(screen.getByLabelText("Start new debugging session")).toBeTruthy();
    await waitFor(() => expect(screen.getByText("No sessions yet")).toBeTruthy());
  });
});
