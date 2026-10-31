import { act, renderHook } from "@testing-library/react";
import { StrictMode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { usePlayback } from "./usePlayback";

describe("usePlayback", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("starts following the newest day and is inert while disabled", () => {
    const { result } = renderHook(() => usePlayback(10, false, 10));
    expect(result.current.day).toBeNull();
    expect(result.current.playing).toBe(false);
    act(() => result.current.togglePlay());
    expect(result.current.playing).toBe(false);
  });

  it("setDay jumps and clamps, and stops playback", () => {
    const { result } = renderHook(() => usePlayback(10, true, 10));
    act(() => result.current.setDay(4));
    expect(result.current.day).toBe(4);
    act(() => result.current.setDay(99));
    expect(result.current.day).toBe(9);
    act(() => result.current.setDay(-3));
    expect(result.current.day).toBe(0);
    act(() => result.current.togglePlay());
    expect(result.current.playing).toBe(true);
    act(() => result.current.setDay(2));
    expect(result.current.playing).toBe(false);
    expect(result.current.day).toBe(2);
  });

  it("play advances one day per frame and stops on the last day", () => {
    const { result } = renderHook(() => usePlayback(4, true, 10));
    act(() => result.current.togglePlay());
    expect(result.current.playing).toBe(true);
    expect(result.current.day).toBe(0);
    act(() => { vi.advanceTimersByTime(10); });
    expect(result.current.day).toBe(1);
    act(() => { vi.advanceTimersByTime(10); });
    expect(result.current.day).toBe(2);
    act(() => { vi.advanceTimersByTime(10); });
    expect(result.current.day).toBe(3);
    expect(result.current.playing).toBe(false);
    act(() => { vi.advanceTimersByTime(50); });
    expect(result.current.day).toBe(3);
  });

  it("play from the last day restarts at zero; pause holds the day", () => {
    const { result } = renderHook(() => usePlayback(4, true, 10));
    act(() => result.current.setDay(3));
    act(() => result.current.togglePlay());
    expect(result.current.day).toBe(0);
    act(() => { vi.advanceTimersByTime(10); });
    act(() => result.current.togglePlay());
    expect(result.current.playing).toBe(false);
    const held = result.current.day;
    act(() => { vi.advanceTimersByTime(50); });
    expect(result.current.day).toBe(held);
  });

  it("under StrictMode, which mounts effects twice, still advances exactly one day per frame", () => {
    const { result } = renderHook(() => usePlayback(100, true, 10), { wrapper: StrictMode });
    act(() => result.current.togglePlay());
    expect(result.current.day).toBe(0);
    act(() => { vi.advanceTimersByTime(10); });
    expect(result.current.day).toBe(1);
    act(() => { vi.advanceTimersByTime(100); });
    expect(result.current.day).toBe(11);
  });

  it("disabling resets to following the newest day", async () => {
    const { result, rerender } = renderHook(({ enabled }) => usePlayback(10, enabled, 10), { initialProps: { enabled: true } });
    act(() => result.current.setDay(5));
    rerender({ enabled: false });
    await act(async () => { vi.advanceTimersByTime(1); });
    expect(result.current.day).toBeNull();
    expect(result.current.playing).toBe(false);
  });
});
