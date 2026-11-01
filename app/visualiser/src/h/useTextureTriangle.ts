import { useEffect, useState } from "react";
import { fetchTextureTriangle } from "@/api/fetchTextureTriangle";
import type { TextureTriangle } from "@/t/TextureTriangle";

export type TextureTriangleState = {
  loading: boolean;
  data: TextureTriangle | null;
  error: string | null;
};

/** Fetch the classified texture triangle once, on mount. */
export function useTextureTriangle(): TextureTriangleState {
  const [state, setState] = useState<TextureTriangleState>({ loading: true, data: null, error: null });

  useEffect(() => {
    let cancelled = false;
    fetchTextureTriangle()
      .then((data) => { if (!cancelled) setState({ loading: false, data, error: null }); })
      .catch((err: unknown) => { if (!cancelled) setState({ loading: false, data: null, error: err instanceof Error ? err.message : String(err) }); });
    return () => { cancelled = true; };
  }, []);

  return state;
}
