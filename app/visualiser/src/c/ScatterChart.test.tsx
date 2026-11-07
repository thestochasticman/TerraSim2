import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MAX_POINTS, ScatterChart } from "./ScatterChart";
import type { RunPairs } from "@/t/RunPairs";

const pairs: RunPairs = {
  t: Float32Array.from([0, 0, 5, Number.NaN]),
  row: new Float32Array(4),
  col: new Float32Array(4),
  station: Float32Array.from([0, 1, 0, 1]),
  observed: Float32Array.from([0.2, 0.4, 0.3, 0.5]),
  modelled: Float32Array.from([0.25, 0.3, 0.3, Number.NaN]),
};
const stations = ["a", "b"];
const dates = ["d0", "d1", "d2", "d3", "d4", "d5"];

/** A big set, with the day's points always kept. */
function many(n: number): RunPairs {
  const t = new Float32Array(n).map((_, i) => (i % 100 === 0 ? 7 : 1));
  return { t, row: new Float32Array(n), col: new Float32Array(n), station: new Float32Array(n), observed: new Float32Array(n).fill(0.3), modelled: new Float32Array(n).fill(0.3) };
}

describe("ScatterChart", () => {
  it("draws a dot per paired observation, the 1:1 line, and says how many are drawn", () => {
    const { container } = render(<ScatterChart pairs={pairs} day={null} stations={stations} dates={dates} />);
    expect(container.querySelectorAll("circle")).toHaveLength(3);
    expect(screen.getByTestId("identity")).toBeTruthy();
    expect(screen.getByTestId("readout").textContent).toBe("3 of 4 observations drawn");
  });

  it("draws the day on screen in full and fades the rest", () => {
    const { container } = render(<ScatterChart pairs={pairs} day={0} stations={stations} dates={dates} />);
    const onDay = container.querySelectorAll('circle[data-on-day="true"]');
    const others = container.querySelectorAll('circle[data-on-day="false"]');
    expect(onDay).toHaveLength(2);
    expect(others).toHaveLength(1);
    expect(Number(onDay[0].getAttribute("fill-opacity"))).toBeGreaterThan(Number(others[0].getAttribute("fill-opacity")));
    expect(screen.getByTestId("readout").textContent).toContain("this day in full");
  });

  it("thins a large set to the cap while keeping every point of the day", () => {
    const { container } = render(<ScatterChart pairs={many(MAX_POINTS * 3)} day={7} stations={[]} dates={[]} />);
    const drawn = container.querySelectorAll("circle").length;
    expect(drawn).toBeLessThanOrEqual(MAX_POINTS + MAX_POINTS * 3 / 100);
    expect(container.querySelectorAll('circle[data-on-day="true"]')).toHaveLength((MAX_POINTS * 3) / 100);
  });

  it("hovering near a dot reads its date, station and values", () => {
    const { container } = render(<ScatterChart pairs={pairs} day={null} stations={stations} dates={dates} />);
    const svg = container.querySelector("svg") as SVGSVGElement;
    svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: 360, height: 360, right: 360, bottom: 360, x: 0, y: 0, toJSON: () => ({}) });
    const circle = container.querySelectorAll("circle")[2];
    fireEvent.mouseMove(svg, { clientX: Number(circle.getAttribute("cx")) + 46, clientY: Number(circle.getAttribute("cy")) + 10 });
    expect(screen.getByTestId("readout").textContent).toBe("d5 · a · observed 0.300 · modelled 0.300");
    expect(circle.getAttribute("data-hovered")).toBe("true");
    fireEvent.mouseLeave(svg);
    expect(screen.getByTestId("readout").textContent).toBe("3 of 4 observations drawn");
  });
});
