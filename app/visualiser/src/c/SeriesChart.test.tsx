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

/** A 30-day series so zooming has room to work. */
const long: RunSeries = {
  dates: Array.from({ length: 30 }, (_, i) => `day${i}`),
  rain: Array.from({ length: 30 }, (_, i) => (i % 7 === 0 ? 8 : 0)),
  pet: new Array(30).fill(4),
  moisture: Array.from({ length: 30 }, (_, i) => 40 + i),
};

/** Give the SVG a known on-screen box so pointer x maps to the viewBox 1:1. */
function sized(container: HTMLElement): SVGSVGElement {
  const svg = container.querySelector("svg") as SVGSVGElement;
  svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1200, height: 240, right: 1200, bottom: 240, x: 0, y: 0, toJSON: () => ({}) });
  return svg;
}
const PLOT_LEFT = 48;
const PLOT_WIDTH = 1200 - 48 - 12;
/** Pointer x for a day when the whole series is shown. */
const xForDay = (d: number, nDays: number) => PLOT_LEFT + (d / (nDays - 1)) * PLOT_WIDTH;
const rainBars = (container: HTMLElement) => container.querySelectorAll('rect[data-series="rain"]').length;

describe("SeriesChart", () => {
  it("draws stored water as a line, and every flux as bars: rain up, evaporation and runoff down, demand outlined", () => {
    const { container } = render(<SeriesChart series={series} day={null} />);
    const strokes = [...container.querySelectorAll("path")].map((p) => p.getAttribute("stroke"));
    expect(strokes.filter((s) => s === SERIES_COLOURS.moisture)).toHaveLength(1);
    expect(strokes.filter((s) => s === SERIES_COLOURS.pet || s === SERIES_COLOURS.evaporation || s === SERIES_COLOURS.runoff)).toHaveLength(0);
    expect(rainBars(container)).toBe(5);
    expect(container.querySelectorAll('rect[data-series="evaporation"]')).toHaveLength(5);
    expect(container.querySelectorAll('rect[data-series="runoff"]')).toHaveLength(5);
    const outlines = container.querySelectorAll('rect[data-outline="pet"]');
    expect(outlines).toHaveLength(5);
    expect(outlines[0].getAttribute("fill")).toBe("none");
  });

  it("has a legend naming every series and showing the marked day's values", () => {
    render(<SeriesChart series={series} day={1} />);
    const legend = screen.getByRole("list", { name: "legend" });
    expect(legend.textContent).toContain("stored");
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

  it("a press and release on the same day seeks to it", () => {
    const onSeek = vi.fn();
    const { container } = render(<SeriesChart series={series} day={null} onSeek={onSeek} />);
    const svg = sized(container);
    fireEvent.mouseDown(svg, { clientX: 1200 - 12, clientY: 100, button: 0 });
    fireEvent.mouseUp(svg, { clientX: 1200 - 12, clientY: 100 });
    expect(onSeek).toHaveBeenCalledWith(4);
    fireEvent.mouseDown(svg, { clientX: 48, clientY: 100, button: 0 });
    fireEvent.mouseUp(svg, { clientX: 48, clientY: 100 });
    expect(onSeek).toHaveBeenCalledWith(0);
  });

  it("dragging across days zooms to that span, shows a selection while dragging, and does not seek", () => {
    const onSeek = vi.fn();
    const { container } = render(<SeriesChart series={long} day={null} onSeek={onSeek} />);
    const svg = sized(container);
    expect(rainBars(container)).toBe(30);

    fireEvent.mouseDown(svg, { clientX: xForDay(10, 30), clientY: 100, button: 0 });
    fireEvent.mouseMove(svg, { clientX: xForDay(20, 30), clientY: 100 });
    expect(container.querySelector('[data-testid="selection"]')).not.toBeNull();
    fireEvent.mouseUp(svg, { clientX: xForDay(20, 30), clientY: 100 });

    expect(onSeek).not.toHaveBeenCalled();
    expect(container.querySelector('[data-testid="selection"]')).toBeNull();
    expect(rainBars(container)).toBe(11);
    expect(screen.getByRole("button", { name: "reset zoom" }).textContent).toContain("day10 to day20");
  });

  it("double click and the reset button both restore the whole run", () => {
    const { container } = render(<SeriesChart series={long} day={null} />);
    const svg = sized(container);

    fireEvent.mouseDown(svg, { clientX: xForDay(0, 30), clientY: 100, button: 0 });
    fireEvent.mouseUp(svg, { clientX: xForDay(9, 30), clientY: 100 });
    expect(rainBars(container)).toBe(10);
    fireEvent.click(screen.getByRole("button", { name: "reset zoom" }));
    expect(rainBars(container)).toBe(30);

    fireEvent.mouseDown(svg, { clientX: xForDay(0, 30), clientY: 100, button: 0 });
    fireEvent.mouseUp(svg, { clientX: xForDay(9, 30), clientY: 100 });
    expect(rainBars(container)).toBe(10);
    fireEvent.doubleClick(svg);
    expect(rainBars(container)).toBe(30);
    expect(screen.queryByRole("button", { name: "reset zoom" })).toBeNull();
  });

  it("a zoom narrower than a week widens to a week", () => {
    const { container } = render(<SeriesChart series={long} day={null} />);
    const svg = sized(container);
    fireEvent.mouseDown(svg, { clientX: xForDay(10, 30), clientY: 100, button: 0 });
    fireEvent.mouseUp(svg, { clientX: xForDay(13, 30), clientY: 100 });
    expect(rainBars(container)).toBe(7);
  });

  it("draws without the optional flux series: rain up, demand outlined, nothing stacked down", () => {
    const { container } = render(<SeriesChart series={{ dates: ["a"], rain: [1], pet: [2], moisture: [3] }} day={0} />);
    expect(rainBars(container)).toBe(1);
    expect(container.querySelectorAll('rect[data-outline="pet"]')).toHaveLength(1);
    expect(container.querySelectorAll('rect[data-series="evaporation"]')).toHaveLength(0);
  });
});
