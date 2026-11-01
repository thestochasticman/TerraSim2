import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SeriesPanel } from "./SeriesPanel";

type Props = React.ComponentProps<typeof SeriesPanel>;

const base: Props = {
  width: 200,
  height: 100,
  range: [0, 4],
  yMin: 0,
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

const rectsOf = (container: HTMLElement, key: string) => [...container.querySelectorAll(`rect[data-series="${key}"]`)] as SVGRectElement[];
const num = (el: Element, attr: string) => Number(el.getAttribute(attr));

describe("SeriesPanel", () => {
  it("draws one path per line in the given colours", () => {
    const { container } = renderPanel();
    const strokes = [...container.querySelectorAll("path")].map((p) => p.getAttribute("stroke")).filter((s) => s === "#111" || s === "#222");
    expect(strokes).toEqual(["#111", "#222"]);
  });

  it("draws upward bars from zero, one per visible day", () => {
    const { container } = renderPanel({ lines: [], barGroups: [{ direction: "up", stack: [{ key: "rain", label: "rain", colour: "#333", values: [0, 2, 0, 4, 0] }] }] });
    const bars = rectsOf(container, "rain");
    expect(bars).toHaveLength(5);
    expect(num(bars[1], "height")).toBeGreaterThan(0);
    expect(num(bars[0], "height")).toBe(0);
    expect(num(bars[3], "y") + num(bars[3], "height")).toBeCloseTo(100);
  });

  it("stacks downward bars below zero and draws an outline behind them, with a zero line", () => {
    const { container } = renderPanel({
      lines: [],
      yMin: -10,
      yMax: 10,
      barGroups: [
        {
          direction: "down",
          stack: [
            { key: "evap", label: "evap", colour: "#444", values: [2, 2, 2, 2, 2] },
            { key: "runoff", label: "runoff", colour: "#555", values: [0, 3, 0, 0, 0] },
          ],
          outline: { key: "demand", label: "demand", colour: "#666", values: [5, 5, 5, 5, 5] },
        },
      ],
    });
    const zeroY = 50;
    const evap = rectsOf(container, "evap")[1];
    const runoff = rectsOf(container, "runoff")[1];
    expect(num(evap, "y")).toBeCloseTo(zeroY);
    expect(num(evap, "height")).toBeCloseTo(10);
    expect(num(runoff, "y")).toBeCloseTo(zeroY + 10);
    expect(num(runoff, "height")).toBeCloseTo(15);
    const outlines = [...container.querySelectorAll('rect[data-outline="demand"]')];
    expect(outlines).toHaveLength(5);
    expect(outlines[0].getAttribute("fill")).toBe("none");
    expect(outlines[0].getAttribute("stroke")).toBe("#666");
    expect(num(outlines[0], "height")).toBeCloseTo(25);
    const zeroLines = [...container.querySelectorAll('[data-testid="zero"]')];
    expect(zeroLines).toHaveLength(1);
    expect(num(zeroLines[0], "y1")).toBeCloseTo(zeroY);
    expect(num(zeroLines[0], "x2")).toBe(200);
  });

  it("labels the y axis with absolute values so the downward side reads as a depth, not a negative", () => {
    const { container } = renderPanel({ lines: [], yMin: -10, yMax: 10 });
    const labels = [...container.querySelectorAll("text")].map((t) => t.textContent ?? "");
    expect(labels.some((t) => t.startsWith("-"))).toBe(false);
  });

  it("places the marker at the day's x position and omits it when null", () => {
    const { container } = renderPanel({ markerDay: 2 });
    expect(container.querySelector('[data-testid="marker"]')?.getAttribute("x1")).toBe("100");
    const { container: none } = renderPanel({ markerDay: null });
    expect(none.querySelector('[data-testid="marker"]')).toBeNull();
  });

  it("shows only the days in range: bars for those days, the marker only if inside, the range at the edges", () => {
    const group = { direction: "up" as const, stack: [{ key: "rain", label: "rain", colour: "#333", values: [0, 2, 0, 4, 0] }] };
    const { container } = renderPanel({ range: [1, 3], lines: [], barGroups: [group], markerDay: 2 });
    expect(rectsOf(container, "rain")).toHaveLength(3);
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
