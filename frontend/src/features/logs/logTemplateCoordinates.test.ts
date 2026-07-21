import { describe, expect, it } from "vitest";

import { GRID, minuteToX, rowYFor } from "./logTemplateCoordinates";

describe("minuteToX", () => {
  it("maps midnight to the grid start", () => {
    expect(minuteToX(0)).toBe(GRID.startX);
  });

  it("maps end-of-day to the grid end", () => {
    expect(minuteToX(1440)).toBe(GRID.endX);
  });

  it("maps noon to the grid midpoint", () => {
    const mid = (GRID.startX + GRID.endX) / 2;
    expect(minuteToX(720)).toBeCloseTo(mid, 5);
  });

  it("is linear for a known segment (08:00 -> 480 min)", () => {
    const expected = GRID.startX + (480 / 1440) * (GRID.endX - GRID.startX);
    expect(minuteToX(480)).toBeCloseTo(expected, 5);
  });

  it("clamps out-of-range minutes", () => {
    expect(minuteToX(-100)).toBe(GRID.startX);
    expect(minuteToX(5000)).toBe(GRID.endX);
  });
});

describe("rowYFor", () => {
  it("returns distinct rows in top-to-bottom order", () => {
    expect(rowYFor("OFF_DUTY")).toBeLessThan(rowYFor("SLEEPER_BERTH"));
    expect(rowYFor("SLEEPER_BERTH")).toBeLessThan(rowYFor("DRIVING"));
    expect(rowYFor("DRIVING")).toBeLessThan(rowYFor("ON_DUTY_NOT_DRIVING"));
  });
});
