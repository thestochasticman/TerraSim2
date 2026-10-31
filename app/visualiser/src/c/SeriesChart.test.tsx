import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SERIES_COLOURS, SeriesChart } from "./SeriesChart";
import type { RunSeries } from "@/t/RunSeries";

const series: RunSeries = {
  dates: ["d0", "d1", "d2", "d3", "d4"],
  rain: [0, 10, 0, 0, 5],
  pet: [4, 4, 4, 4, 4],
  moisture: [50, 58, 55, 52, 54],
  infiltration: [0, 10, 0, 0, 5],
  runoff: [0, 0, 0, 0, 0],
  evaporation: [2, 2, 3, 3, 3],
};

describe("SeriesChart", () => {
  it("draws two panels: one moisture line, and rain bars with demand, evaporation and runoff lines", () => {
    const { container } = render(<SeriesChart series={series} day={null} />);
    const strokes = [...container.querySelectorAll("path")].map((p) => p.getAttribute("stroke"));
    expect(strokes.filter((s) => s === SERIES_COLOURS.moisture)).toHaveLength(1);
    expect(strokes.filter((s) => s === SERIES_COLOURS.pet)).toHaveLength(1);
    expect(strokes.filter((s) => s === SERIES_COLOURS.evaporation)).toHaveLength(1);
    expect(strokes.filter((s) => s === SERIES_COLOURS.runoff)).toHaveLength(1);
    expect([...container.querySelectorAll("rect")].filter((r) => r.getAttribute("fill") === SERIES_COLOURS.rain)).toHaveLength(5);
  });

  it("has a legend naming every series and showing the marked day's values", () => {
    render(<SeriesChart series={series} day={1} />);
    const legend = screen.getByRole("list", { name: "legend" });
    expect(legend.textContent).toContain("moisture");
    expect(legend.textContent).toContain("rain");
    expect(legend.textContent).toContain("demand");
    expect(legend.textContent).toContain("58.0");
    expect(legend.textContent).toContain("10.0");
    expect(legend.textContent).toContain("d1");
  });

  it("marks the scrubber's day in both panels", () => {
    const { container } = render(<SeriesChart series={series} day={2} />);
    const markers = container.querySelectorAll('[data-testid="marker"]');
    expect(markers).toHaveLength(2);
    expect(markers[0].getAttribute("x1")).toBe(markers[1].getAttribute("x1"));
  });

  it("clicking the plot seeks to the nearest day", () => {
    const onSeek = vi.fn();
    const { container } = render(<SeriesChart series={series} day={null} onSeek={onSeek} />);
    const svg = container.querySelector("svg") as SVGSVGElement;
    svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1200, height: 240, right: 1200, bottom: 240, x: 0, y: 0, toJSON: () => ({}) });
    fireEvent.click(svg, { clientX: 1200 - 12, clientY: 100 });
    expect(onSeek).toHaveBeenCalledWith(4);
    fireEvent.click(svg, { clientX: 48, clientY: 100 });
    expect(onSeek).toHaveBeenCalledWith(0);
  });

  it("draws without the optional flux series", () => {
    const { container } = render(<SeriesChart series={{ dates: ["a"], rain: [1], pet: [2], moisture: [3] }} day={0} />);
    expect(container.querySelectorAll("path").length).toBeGreaterThan(0);
  });
});
