import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LAYOUT, TextureTriangle } from "./TextureTriangle";
import { TRIANGLE_HEIGHT } from "@/f/projectTernary";
import type { TextureTriangle as Data } from "@/t/TextureTriangle";

const data: Data = {
  textures: ["sand", "clay"],
  step: 50,
  points: {
    sand: [100, 50, 0, 50, 0, 0],
    silt: [0, 50, 100, 0, 50, 0],
    clay: [0, 0, 0, 50, 50, 100],
    texture: [0, 0, 0, 1, 1, 1],
    diameter: [317, 56, 10, 6.7, 1.2, 0.14],
    psiE: [-0.39, -1.44, -2.5, -2.74, -3.79, -5.1],
    b: [1, 3.2, 5.3, 5.85, 8, 10.73],
  },
  typical: [{ texture: "sand", sand: 92, silt: 5, clay: 3, diameter: 211.75 }],
};

/** Give the SVG a box equal to its viewBox so pointer coordinates are SVG units. */
function sized(container: HTMLElement): SVGSVGElement {
  const svg = container.querySelector("svg") as SVGSVGElement;
  svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: LAYOUT.width, height: LAYOUT.height, right: LAYOUT.width, bottom: LAYOUT.height, x: 0, y: 0, toJSON: () => ({}) });
  return svg;
}

describe("TextureTriangle", () => {
  it("draws a dot per composition, a label per class, and a ring per typical soil", () => {
    const { container } = render(<TextureTriangle data={data} />);
    expect(container.querySelectorAll("circle[data-point]")).toHaveLength(6);
    expect(container.querySelector('[data-region="sand"]')).not.toBeNull();
    expect(container.querySelector('[data-region="clay"]')).not.toBeNull();
    expect(container.querySelectorAll("circle[data-typical]")).toHaveLength(1);
    expect(screen.getByLabelText("reading").textContent).toContain("Move over the triangle");
  });

  it("reads the nearest composition under the pointer, and clears outside the triangle", () => {
    const { container } = render(<TextureTriangle data={data} />);
    const svg = sized(container);
    const apexX = LAYOUT.left + LAYOUT.side / 2;
    const apexY = LAYOUT.base - LAYOUT.side * TRIANGLE_HEIGHT;
    fireEvent.mouseMove(svg, { clientX: apexX, clientY: apexY + 2 });
    const reading = screen.getByLabelText("reading");
    expect(reading.textContent).toContain("clay");
    expect(reading.textContent).toContain("0 / 0 / 100 %");
    expect(reading.textContent).toContain("-5.10 J/kg");
    expect(container.querySelector('[data-testid="cursor"]')).not.toBeNull();
    fireEvent.mouseMove(svg, { clientX: LAYOUT.left + LAYOUT.side / 2, clientY: LAYOUT.base + 300 });
    expect(reading.textContent).toContain("Move over the triangle");
    expect(container.querySelector('[data-testid="cursor"]')).toBeNull();
  });

  it("hovering a class in the list dims the other classes' dots", () => {
    const { container } = render(<TextureTriangle data={data} />);
    const item = screen.getByRole("list", { name: "classes" }).querySelector("li")!;
    fireEvent.mouseEnter(item);
    expect(container.querySelector('circle[data-point="5"]')?.getAttribute("fill-opacity")).toBe("0.25");
    expect(container.querySelector('circle[data-point="0"]')?.getAttribute("fill-opacity")).toBe("1");
    expect(item.getAttribute("data-highlighted")).toBe("true");
    fireEvent.mouseLeave(item);
    expect(container.querySelector('circle[data-point="5"]')?.getAttribute("fill-opacity")).toBe("1");
  });
});
