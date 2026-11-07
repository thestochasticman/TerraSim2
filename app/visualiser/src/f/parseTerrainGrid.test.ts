import { describe, expect, it } from "vitest";
import { parseTerrainGrid } from "./parseTerrainGrid";

const valid = {
  rows: 2,
  cols: 3,
  cell_size: 10,
  elevation: [
    [1, 2, 3],
    [4, 5, 6],
  ],
};

describe("parseTerrainGrid", () => {
  it("returns dimensions, cell size and a row-major Float64Array", () => {
    const grid = parseTerrainGrid(valid);
    expect(grid.rows).toBe(2);
    expect(grid.cols).toBe(3);
    expect(grid.cellSize).toBe(10);
    expect(grid.elevation).toBeInstanceOf(Float64Array);
    expect(Array.from(grid.elevation)).toEqual([1, 2, 3, 4, 5, 6]);
    expect(grid.elevation[1 * grid.cols + 2]).toBe(6);
    expect(grid.capacity).toBeUndefined();
  });

  it("reads capacity when present, with the same layout", () => {
    const grid = parseTerrainGrid({ ...valid, capacity: [[100, 100, 80], [100, 90, 100]] });
    expect(Array.from(grid.capacity ?? [])).toEqual([100, 100, 80, 100, 90, 100]);
  });

  it("reads free capacity when present and treats null as absent", () => {
    expect(Array.from(parseTerrainGrid({ ...valid, free_capacity: [[60, 60, 60], [70, 70, 70]] }).freeCapacity ?? [])).toEqual([60, 60, 60, 70, 70, 70]);
    expect(parseTerrainGrid({ ...valid, free_capacity: null }).freeCapacity).toBeUndefined();
  });

  it("reads vegetation with its class names when present, treats null as absent, and refuses an index without a name", () => {
    const grid = parseTerrainGrid({ ...valid, vegetation: [[0, 1, -1], [1, 1, 0]], vegetation_classes: ["grass", "tree"] });
    expect(Array.from(grid.vegetation ?? [])).toEqual([0, 1, -1, 1, 1, 0]);
    expect(grid.vegetationClasses).toEqual(["grass", "tree"]);
    expect(parseTerrainGrid({ ...valid, vegetation: null, vegetation_classes: null }).vegetation).toBeUndefined();
    expect(() => parseTerrainGrid({ ...valid, vegetation: [[0, 2, 0], [0, 0, 0]], vegetation_classes: ["grass", "tree"] })).toThrow("index 2 classes");
    expect(() => parseTerrainGrid({ ...valid, vegetation: [[0, 0, 0], [0, 0, 0]] })).toThrow("vegetation_classes");
  });

  it("reads upslope cells when present, with the same layout", () => {
    const grid = parseTerrainGrid({ ...valid, upslope_cells: [[1, 1, 1], [2, 3, 6]] });
    expect(Array.from(grid.upslopeCells ?? [])).toEqual([1, 1, 1, 2, 3, 6]);
    expect(() => parseTerrainGrid({ ...valid, upslope_cells: [[1, 1], [2, 3]] })).toThrow("upslope_cells row 0");
  });

  it("accepts integer and fractional elevations alike", () => {
    const grid = parseTerrainGrid({ ...valid, elevation: [[1, 2.5, -3], [0, 0.001, 1e6]] });
    expect(Array.from(grid.elevation)).toEqual([1, 2.5, -3, 0, 0.001, 1e6]);
  });

  it("rejects anything that is not a plain object", () => {
    for (const bad of [null, undefined, 42, "grid", [1, 2]]) {
      expect(() => parseTerrainGrid(bad)).toThrow("must be a JSON object");
    }
  });

  it("rejects rows and cols that are not positive integers", () => {
    expect(() => parseTerrainGrid({ ...valid, rows: 0 })).toThrow("rows must be a positive integer");
    expect(() => parseTerrainGrid({ ...valid, rows: 2.5 })).toThrow("rows must be a positive integer");
    expect(() => parseTerrainGrid({ ...valid, cols: "3" })).toThrow("cols must be a positive integer");
    const { cols: _dropped, ...noCols } = valid;
    void _dropped;
    expect(() => parseTerrainGrid(noCols)).toThrow("cols must be a positive integer");
  });

  it("rejects a cell size that is not a positive finite number", () => {
    for (const bad of [0, -1, Infinity, "10", undefined]) {
      expect(() => parseTerrainGrid({ ...valid, cell_size: bad })).toThrow("cell_size must be a positive finite number");
    }
  });

  it("rejects elevation with the wrong number of rows", () => {
    expect(() => parseTerrainGrid({ ...valid, elevation: [[1, 2, 3]] })).toThrow("elevation must be an array of 2 rows");
    expect(() => parseTerrainGrid({ ...valid, elevation: "flat" })).toThrow("elevation must be an array of 2 rows");
  });

  it("rejects an elevation row with the wrong number of columns", () => {
    expect(() => parseTerrainGrid({ ...valid, elevation: [[1, 2, 3], [4, 5]] })).toThrow(
      "elevation row 1 must be an array of 3 values",
    );
  });

  it("rejects non-numeric or non-finite values and names the field and cell", () => {
    expect(() => parseTerrainGrid({ ...valid, elevation: [[1, 2, 3], [4, null, 6]] })).toThrow(
      "elevation[1][1] must be a finite number",
    );
    expect(() => parseTerrainGrid({ ...valid, capacity: [[1, "2", 3], [4, 5, 6]] })).toThrow(
      "capacity[0][1] must be a finite number",
    );
    expect(() => parseTerrainGrid({ ...valid, capacity: [[1, 2, 3]] })).toThrow("capacity must be an array of 2 rows");
  });
});
