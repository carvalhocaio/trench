import { describe, expect, it } from "vitest";

import { currentSeason, currentWeek } from "@/lib/season";
import type { GameRead } from "@/lib/api/types";

function game(week: number, status: GameRead["status"]): Pick<GameRead, "week" | "status"> {
  return { week, status };
}

describe("currentSeason", () => {
  it("uses the current year outside January and February", () => {
    expect(currentSeason(new Date("2026-03-15T12:00:00Z"))).toBe(2026);
    expect(currentSeason(new Date("2026-12-01T12:00:00Z"))).toBe(2026);
  });

  it("falls back to the previous year during January and February", () => {
    expect(currentSeason(new Date("2026-01-15T12:00:00Z"))).toBe(2025);
    expect(currentSeason(new Date("2026-02-28T12:00:00Z"))).toBe(2025);
  });
});

describe("currentWeek", () => {
  it("picks the smallest scheduled week", () => {
    const games = [game(3, "FINAL"), game(5, "SCHEDULED"), game(4, "SCHEDULED")];
    expect(currentWeek(games)).toBe(4);
  });

  it("falls back to the largest week when nothing is scheduled", () => {
    const games = [game(1, "FINAL"), game(3, "FINAL"), game(2, "FINAL")];
    expect(currentWeek(games)).toBe(3);
  });

  it("defaults to week 1 when there are no games", () => {
    expect(currentWeek([])).toBe(1);
  });
});
