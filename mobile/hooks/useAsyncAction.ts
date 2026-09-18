import { useCallback, useState } from "react";

export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (...args: TArgs): Promise<TResult | undefined> => {
      setLoading(true);
      setError(null);
      try {
        return await action(...args);
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Something went wrong. Please retry.");
        return undefined;
      } finally {
        setLoading(false);
      }
    },
    [action]
  );

  return { run, loading, error, clearError: () => setError(null) };
}

