import { useSyncExternalStore } from "react";
import type { ColourScheme } from "@/t/ColourScheme";

const QUERY = "(prefers-color-scheme: dark)";

const isSupported = () => typeof window !== "undefined" && typeof window.matchMedia === "function";

function subscribe(onChange: () => void): () => void {
  if (!isSupported()) return () => {};
  const media = window.matchMedia(QUERY);
  media.addEventListener("change", onChange);
  return () => media.removeEventListener("change", onChange);
}

const getSnapshot = (): ColourScheme => (isSupported() && window.matchMedia(QUERY).matches ? "dark" : "light");
const getServerSnapshot = (): ColourScheme => "light";

/**
 * The colour scheme the page is showing, following the browser's
 * preference as it changes. "light" on the server and wherever the
 * preference cannot be read.
 */
export function useColourScheme(): ColourScheme {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
}
