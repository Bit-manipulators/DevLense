import { PropsWithChildren, createContext, useContext, useMemo, useState } from "react";

import { Language } from "@/types/api";

export interface DebugDraft {
  language: Language;
  code: string; // currentEditorCode
  originalCode?: string; // original source code submitted for analysis
  correctedCode?: string; // corrected code returned from analyzer
  isExplicitLanguage?: boolean; // tracks whether user explicitly set the language
  errorMessage: string;
  question: string;
}

const emptyDraft: DebugDraft = {
  language: "python",
  code: "",
  originalCode: "",
  correctedCode: "",
  isExplicitLanguage: false,
  errorMessage: "",
  question: "",
};

interface DebugDraftContextValue {
  draft: DebugDraft;
  updateDraft: (changes: Partial<DebugDraft>) => void;
  clearDraft: () => void;
  applyFixedCode: (codeToApply?: string) => void;
}

const DebugDraftContext = createContext<DebugDraftContextValue | undefined>(undefined);

export function DebugDraftProvider({ children }: PropsWithChildren) {
  const [draft, setDraft] = useState<DebugDraft>(emptyDraft);

  const value = useMemo<DebugDraftContextValue>(
    () => ({
      draft,
      updateDraft: (changes: Partial<DebugDraft>) =>
        setDraft((current) => ({ ...current, ...changes })),
      clearDraft: () => setDraft(emptyDraft),
      applyFixedCode: (codeToApply?: string) => {
        setDraft((current) => {
          const targetFix = codeToApply ?? current.correctedCode ?? current.code;
          return {
            ...current,
            code: targetFix, // currentEditorCode = correctedCode
            originalCode: current.originalCode || current.code,
            correctedCode: targetFix,
          };
        });
      },
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
