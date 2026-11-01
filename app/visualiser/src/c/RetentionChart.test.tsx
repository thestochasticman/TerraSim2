import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RetentionChart } from "./RetentionChart";
import type { RetentionCurves } from "@/t/RetentionCurves";

const data: RetentionCurves = {
  suction: [1, 10, 100, 1000, 10000],
  fieldCapacity: 33,
  wiltingPoint: 1500,
  models: {
    campbell: [
      { texture: "sand", theta: [0.37, 0.1, 0.03, 0.01, 0.005], thetaFc: 0.04, thetaPwp: 0.004, availableWater: 36 },
      { texture: "clay", theta: [0.5, 0.45, 0.33, 0.25, 0.18], thetaFc: 0.376, thetaPwp: 0.228, availableWater: 148 },
    ],
    van_genuchten: [
      { texture: "sand", theta: [0.38, 0.12, 0.05, 0.03, 0.025], thetaFc: 0.061, thetaPwp: 0.023, availableWater: 38 },
      { texture: "clay", theta: [0.5, 0.46, 0.35, 0.27, 0.2], thetaFc: 0.391, thetaPwp: 0.247, availableWater: 144 },
    ],
  },
};

describe("RetentionChart", () => {
  it("draws one line per texture for the chosen model, both reference lines, and a bar per model per texture", () => {
    const { container } = render(<RetentionChart data={data} />);
    expect(container.querySelectorAll("path[data-texture]")).toHaveLength(2);
    expect(container.querySelectorAll('[data-testid="reference"]')).toHaveLength(2);
    expect(container.querySelectorAll('rect[data-model="campbell"]')).toHaveLength(2);
    expect(container.querySelectorAll('rect[data-model="van_genuchten"]')).toHaveLength(2);
    expect(container.querySelector('[data-testid="curves"]')?.getAttribute("data-model")).toBe("campbell");
    expect(container.textContent).toContain("field capacity, 33 J/kg");
    expect(container.textContent).toContain("wilting point, 1.5k J/kg");
  });

  it("the table shows the chosen model's contents and available water, and the radio switches models", () => {
    const { container } = render(<RetentionChart data={data} />);
    const table = screen.getByRole("table", { name: "textures" });
    expect(table.textContent).toContain("0.040");
    expect(table.textContent).toContain("148");
    fireEvent.click(screen.getByLabelText("van Genuchten"));
    expect(table.textContent).toContain("0.061");
    expect(table.textContent).toContain("144");
    expect(container.querySelector('[data-testid="curves"]')?.getAttribute("data-model")).toBe("van_genuchten");
  });

  it("hovering a table row, a line or a bar highlights that texture everywhere, and leaving clears it", () => {
    const { container } = render(<RetentionChart data={data} />);
    const clayRow = screen.getByRole("cell", { name: "clay" }).closest("tr")!;
    fireEvent.mouseEnter(clayRow);
    expect(container.querySelector('path[data-texture="clay"]')?.getAttribute("data-highlighted")).toBe("true");
    expect(container.querySelector('path[data-texture="sand"]')?.getAttribute("stroke-opacity")).toBe("0.25");
    expect(container.querySelector('[data-testid="backdrop"]')).not.toBeNull();
    fireEvent.mouseLeave(clayRow);
    expect(container.querySelector('[data-testid="backdrop"]')).toBeNull();
    fireEvent.mouseEnter(container.querySelector('path[data-hit="sand"]')!);
    expect(container.querySelector('path[data-texture="sand"]')?.getAttribute("data-highlighted")).toBe("true");
    fireEvent.mouseLeave(container.querySelector('path[data-hit="sand"]')!);
    fireEvent.mouseEnter(container.querySelector('rect[data-model="campbell"][data-texture="clay"]')!);
    expect(clayRow.getAttribute("data-highlighted")).toBe("true");
  });
});
