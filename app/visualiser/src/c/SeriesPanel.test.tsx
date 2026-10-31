import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeriesPanel } from "./SeriesPanel";

function renderPanel(extra: Partial<React.ComponentProps<typeof SeriesPanel>> = {}) {
  const props = {
    width: 200,
    height: 100,
    nDays: 5,
    yMax: 10,
    lines: [
      { key: "a", label: "A", colour: "#111", values: [1, 2, 3, 4, 5] },
      { key: "b", label: "B", colour: "#222", values: [5, 4, 3, 2, 1] },
    ],
    markerDay: 2,
    yLabel: "mm",
    showXAxis: true,
    dates: ["d0", "d1", "d2", "d3", "d4"],
    ...extra,
  };
  return render(
    <svg>
      <SeriesPanel {...props} />
    </svg>,
  );
}

describe("SeriesPanel", () => {
  it("draws one path per line in the given colours", () => {
    const { container } = renderPanel();
    const strokes = [...container.querySelectorAll("path")].map((p) => p.getAttribute("stroke")).filter((s) => s === "#111" || s === "#222");
    expect(strokes).toEqual(["#111", "#222"]);
  });

  it("draws bars behind the lines when given, one per day", () => {
    const { container } = renderPanel({ bars: { key: "rain", label: "rain", colour: "#333", values: [0, 2, 0, 4, 0] } });
    const bars = [...container.querySelectorAll("rect")].filter((r) => r.getAttribute("fill") === "#333");
    expect(bars).toHaveLength(5);
    expect(Number(bars[1].getAttribute("height"))).toBeGreaterThan(0);
    expect(Number(bars[0].getAttribute("height"))).toBe(0);
  });

  it("places the marker at the day's x position and omits it when null", () => {
    const { container, rerender } = renderPanel({ markerDay: 2 });
    const marker = container.querySelector('[data-testid="marker"]');
    expect(marker?.getAttribute("x1")).toBe("100");
    rerender(
      <svg>
        <SeriesPanel width={200} height={100} nDays={5} yMax={10} lines={[]} markerDay={null} yLabel="mm" showXAxis={false} dates={[]} />
      </svg>,
    );
    expect(container.querySelector('[data-testid="marker"]')).toBeNull();
  });

  it("labels x ticks with dates only when the x axis is shown", () => {
    const { container, rerender } = renderPanel({ showXAxis: true });
    expect(container.textContent).toContain("d0");
    rerender(
      <svg>
        <SeriesPanel width={200} height={100} nDays={5} yMax={10} lines={[]} markerDay={null} yLabel="mm" showXAxis={false} dates={["d0", "d1", "d2", "d3", "d4"]} />
      </svg>,
    );
    expect(container.textContent).not.toContain("d0");
  });
});
