import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useColourScheme } from "./useColourScheme";

type Listener = () => void;

/** A stand-in for window.matchMedia whose match can be flipped from the test. */
function installMatchMedia(matches: boolean) {
  const listeners = new Set<Listener>();
  const media = {
    get matches() { return matches; },
    addEventListener: (_: string, cb: Listener) => listeners.add(cb),
    removeEventListener: (_: string, cb: Listener) => listeners.delete(cb),
  };
  Object.defineProperty(window, "matchMedia", { configurable: true, value: () => media });
  return { flip: (to: boolean) => { matches = to; listeners.forEach((cb) => cb()); }, listeners };
}

describe("useColourScheme", () => {
  afterEach(() => { delete (window as { matchMedia?: unknown }).matchMedia; });

  it("reads light where matchMedia does not exist", () => {
    const { result } = renderHook(() => useColourScheme());
    expect(result.current).toBe("light");
  });

  it("reads the preference and follows it as it changes, then unsubscribes", () => {
    const media = installMatchMedia(true);
    const { result, unmount } = renderHook(() => useColourScheme());
    expect(result.current).toBe("dark");
    act(() => media.flip(false));
    expect(result.current).toBe("light");
    expect(media.listeners.size).toBe(1);
    unmount();
    expect(media.listeners.size).toBe(0);
  });
});
