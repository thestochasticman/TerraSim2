import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SoilColumnChart } from "./SoilColumnChart";
import type { SoilColumn } from "@/t/SoilColumn";

const column: SoilColumn = {
  textures: ["sand", "clay"],
  layerBounds: [0, 0.3, 1.0],
  rootDepth: 0.6,
  model: "campbell",
  layers: [
    { top: 0, bottom: 0.3, texture: "sand", fraction: 0.035, thicknessInRoots: 0.3, mm: 10.5 },
    { top: 0.3, bottom: 1.0, texture: "clay", fraction: 0.148, thicknessInRoots: 0.3, mm: 44.4 },
  ],
  total: 54.9,
};

describe("SoilColumnChart", () => {
  it("draws a solid part within the roots and a faded part below, and marks the root depth", () => {
    const { container } = render(<SoilColumnChart column={column} />);
    expect(container.querySelectorAll('rect[data-layer="sand"][data-part="roots"]')).toHaveLength(1);
    expect(container.querySelectorAll('rect[data-layer="sand"][data-part="below"]')).toHaveLength(0);
    expect(container.querySelectorAll('rect[data-layer="clay"][data-part="roots"]')).toHaveLength(1);
    expect(container.querySelectorAll('rect[data-layer="clay"][data-part="below"]')).toHaveLength(1);
    expect(container.querySelector('[data-testid="root-depth"]')).not.toBeNull();
    expect(container.textContent).toContain("roots to 0.60 m");
  });

  it("a wider fraction makes a wider bar", () => {
    const { container } = render(<SoilColumnChart column={column} />);
    const sand = Number(container.querySelector('rect[data-layer="sand"]')?.getAttribute("width"));
    const clay = Number(container.querySelector('rect[data-layer="clay"]')?.getAttribute("width"));
    expect(clay).toBeGreaterThan(sand * 3);
  });

  it("shows the total and a table of the layers", () => {
    render(<SoilColumnChart column={column} />);
    expect(screen.getByLabelText("total").textContent).toContain("55");
    const table = screen.getByRole("table", { name: "layers" });
    expect(table.textContent).toContain("0–30 cm");
    expect(table.textContent).toContain("30–100 cm");
    expect(table.textContent).toContain("44.4");
    expect(table.textContent).toContain("30 cm");
  });
});
