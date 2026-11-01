import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeriesPanel } from "./SeriesPanel";

type Props = React.ComponentProps<typeof SeriesPanel>;

const base: Props = {
  width: 200,
  height: 100,
  range: [0, 4],
  yMax: 10,
  lines: [
    { key: "a", label: "A", colour: "#111", values: [1, 2, 3, 4, 5] },
    { key: "b", label: "B", colour: "#222", values: [5, 4, 3, 2, 1] },
  ],
  markerDay: 2,
  yLabel: "mm",
  showXAxis: true,
  dates: ["d0", "d1", "d2", "d3", "d4"],
};

function renderPanel(extra: Partial<Props> = {}) {
  return render(
    <svg>
      <SeriesPanel {...base} {...extra} />
    </svg>,
  );
}

describe("SeriesPanel", () => {
  it("draws one path per line in the given colours", () => {
    const { container } = renderPanel();
    const strokes = [...container.querySelectorAll("path")].map((p) => p.getAttribute("stroke")).filter((s) => s === "#111" || s === "#222");
    expect(strokes).toEqual(["#111", "#222"]);
  });

  it("draws bars behind the lines when given, one per visible day", () => {
    const { container } = renderPanel({ bars: { key: "rain", label: "rain", colour: "#333", values: [0, 2, 0, 4, 0] } });
    const bars = [...container.querySelectorAll("rect")].filter((r) => r.getAttribute("fill") === "#333");
    expect(bars).toHaveLength(5);
    expect(Number(bars[1].getAttribute("height"))).toBeGreaterThan(0);
    expect(Number(bars[0].getAttribute("height"))).toBe(0);
  });

  it("places the marker at the day's x position and omits it when null", () => {
    const { container } = renderPanel({ markerDay: 2 });
    expect(container.querySelector('[data-testid="marker"]')?.getAttribute("x1")).toBe("100");
    const { container: none } = renderPanel({ markerDay: null });
    expect(none.querySelector('[data-testid="marker"]')).toBeNull();
  });

  it("shows only the days in range: bars for those days, the marker only if inside, the range at the edges", () => {
    const { container } = renderPanel({ range: [1, 3], bars: { key: "rain", label: "rain", colour: "#333", values: [0, 2, 0, 4, 0] }, markerDay: 2 });
    const bars = [...container.querySelectorAll("rect")].filter((r) => r.getAttribute("fill") === "#333");
    expect(bars).toHaveLength(3);
    expect(container.querySelector('[data-testid="marker"]')?.getAttribute("x1")).toBe("100");
    const { container: outside } = renderPanel({ range: [1, 3], markerDay: 4 });
    expect(outside.querySelector('[data-testid="marker"]')).toBeNull();
    const { container: edge } = renderPanel({ range: [1, 3], markerDay: 1 });
    expect(edge.querySelector('[data-testid="marker"]')?.getAttribute("x1")).toBe("0");
  });

  it("labels x ticks with dates only when the x axis is shown", () => {
    const { container } = renderPanel({ showXAxis: true });
    expect(container.textContent).toContain("d0");
    const { container: hidden } = renderPanel({ showXAxis: false, lines: [] });
    expect(hidden.textContent).not.toContain("d0");
  });
});
