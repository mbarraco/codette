import { useCallback, useEffect, useRef, useState } from "react";

type UseFetchOptions = {
  pollingInterval?: number;
};

type UseFetchResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
};

export function useFetch<T>(
  url: string,
  opts?: UseFetchOptions,
): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (mountedRef.current) {
        setData(json);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : "Fetch failed");
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [url]);

  useEffect(() => {
    mountedRef.current = true;
    setLoading(true);
    fetchData();

    let interval: ReturnType<typeof setInterval> | undefined;
    if (opts?.pollingInterval) {
      interval = setInterval(fetchData, opts.pollingInterval);
    }

    return () => {
      mountedRef.current = false;
      if (interval) clearInterval(interval);
    };
  }, [fetchData, opts?.pollingInterval]);

  return { data, loading, error, refetch: fetchData };
}
