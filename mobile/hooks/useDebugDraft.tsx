import { PropsWithChildren, createContext, useContext, useMemo, useState } from "react";

import { Language } from "@/types/api";

export interface DebugDraft {
  language: Language;
  code: string;
  errorMessage: string;
  question: string;
}

const emptyDraft: DebugDraft = { language: "python", code: "", errorMessage: "", question: "" };

interface DebugDraftContextValue {
  draft: DebugDraft;
  updateDraft: (changes: Partial<DebugDraft>) => void;
  clearDraft: () => void;
}

const DebugDraftContext = createContext<DebugDraftContextValue | undefined>(undefined);

export function DebugDraftProvider({ children }: PropsWithChildren) {
  const [draft, setDraft] = useState<DebugDraft>(emptyDraft);
  const value = useMemo(
    () => ({
      draft,
      updateDraft: (changes: Partial<DebugDraft>) => setDraft((current) => ({ ...current, ...changes })),
      clearDraft: () => setDraft(emptyDraft)
    }),
    [draft]
  );
  return <DebugDraftContext.Provider value={value}>{children}</DebugDraftContext.Provider>;
}

export function useDebugDraft() {
  const context = useContext(DebugDraftContext);
  if (!context) throw new Error("useDebugDraft must be used inside DebugDraftProvider");
  return context;
}

