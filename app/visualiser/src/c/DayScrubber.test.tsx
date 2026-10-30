import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DayScrubber } from "./DayScrubber";

const base = { daysAvailable: 10, nDays: 10, day: 3, date: "2024-01-04", enabled: true, playing: false, onSeek: () => {}, onTogglePlay: () => {} };

describe("DayScrubber", () => {
  it("shows the day, the date and the count, with the slider spanning the available days", () => {
    render(<DayScrubber {...base} />);
    const slider = screen.getByRole("slider", { name: "day" }) as HTMLInputElement;
    expect(slider.value).toBe("3");
    expect(slider.max).toBe("9");
    expect(screen.getByText("2024-01-04")).toBeTruthy();
    expect(screen.getByText("day 4 of 10")).toBeTruthy();
  });

  it("seeks and toggles through its callbacks and labels the button by state", () => {
    const onSeek = vi.fn();
    const onTogglePlay = vi.fn();
    const { rerender } = render(<DayScrubber {...base} onSeek={onSeek} onTogglePlay={onTogglePlay} />);
    fireEvent.change(screen.getByRole("slider"), { target: { value: "7" } });
    expect(onSeek).toHaveBeenCalledWith(7);
    fireEvent.click(screen.getByRole("button", { name: "play" }));
    expect(onTogglePlay).toHaveBeenCalledTimes(1);
    rerender(<DayScrubber {...base} playing onSeek={onSeek} onTogglePlay={onTogglePlay} />);
    expect(screen.getByRole("button", { name: "pause" })).toBeTruthy();
  });

  it("is a progress bar while disabled: controls inert, thumb on the newest day", () => {
    render(<DayScrubber {...base} enabled={false} daysAvailable={4} day={3} nDays={10} />);
    const slider = screen.getByRole("slider") as HTMLInputElement;
    expect(slider.disabled).toBe(true);
    expect(slider.max).toBe("3");
    expect(slider.value).toBe("3");
    expect((screen.getByRole("button") as HTMLButtonElement).disabled).toBe(true);
  });
});
