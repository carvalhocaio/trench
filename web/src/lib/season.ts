import { TIMEZONE } from "@/lib/format";
import { MAX_WEEK, MIN_WEEK } from "@/lib/season-constants";
import type { GameRead } from "@/lib/api/types";

export { MAX_WEEK, MIN_WEEK };

const yearMonthFormatter = new Intl.DateTimeFormat("en-US", {
  timeZone: TIMEZONE,
  year: "numeric",
  month: "numeric",
});

function partsInTimezone(now: Date): { year: number; month: number } {
  const parts = yearMonthFormatter.formatToParts(now);
  const year = Number(parts.find((part) => part.type === "year")?.value);
  const month = Number(parts.find((part) => part.type === "month")?.value);
  return { year, month };
}

export function currentSeason(now: Date = new Date()): number {
  const { year, month } = partsInTimezone(now);
  return month <= 2 ? year - 1 : year;
}

export function currentWeek(games: Pick<GameRead, "week" | "status">[]): number {
  const scheduledWeeks = games
    .filter((game) => game.status === "SCHEDULED")
    .map((game) => game.week);
  if (scheduledWeeks.length > 0) {
    return Math.min(...scheduledWeeks);
  }
  const weeks = games.map((game) => game.week);
  return weeks.length > 0 ? Math.max(...weeks) : 1;
}

export function parseIntParam(value: string | string[] | undefined): number | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw === undefined || raw.trim() === "") {
    return undefined;
  }
  const parsed = Number(raw);
  return Number.isInteger(parsed) ? parsed : undefined;
}

export function clampWeek(week: number): number {
  return Math.min(MAX_WEEK, Math.max(MIN_WEEK, week));
}
