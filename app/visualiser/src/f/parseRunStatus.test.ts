import { describe, expect, it } from "vitest";
import { parseRunStatus } from "./parseRunStatus";

describe("parseRunStatus", () => {
  it("parses a running status with counts and dates", () => {
    const s = parseRunStatus({ run_id: "tarrawarra-abc", status: "running", days_written: 12, n_days: 432, rows: 72, cols: 97, dates: ["1995-09-25", "1995-09-26"], meta: {} });
    expect(s).toEqual({ runId: "tarrawarra-abc", status: "running", daysWritten: 12, nDays: 432, rows: 72, cols: 97, dates: ["1995-09-25", "1995-09-26"] });
  });

  it("fills zeros and an empty list for a missing run", () => {
    expect(parseRunStatus({ run_id: "x", status: "missing" })).toEqual({ runId: "x", status: "missing", daysWritten: 0, nDays: 0, rows: 0, cols: 0, dates: [] });
  });

  it("rejects bad ids, unknown statuses, negative counts and non-string dates", () => {
    expect(() => parseRunStatus({ run_id: "", status: "running" })).toThrow("run_id");
    expect(() => parseRunStatus({ run_id: "x", status: "paused" })).toThrow("status must be one of");
    expect(() => parseRunStatus({ run_id: "x", status: "running", days_written: -1 })).toThrow("days_written");
    expect(() => parseRunStatus({ run_id: "x", status: "running", n_days: 1.5 })).toThrow("n_days");
    expect(() => parseRunStatus({ run_id: "x", status: "running", dates: [1] })).toThrow("dates");
    expect(() => parseRunStatus("nope")).toThrow("JSON object");
  });
});
