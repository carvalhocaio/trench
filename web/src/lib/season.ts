import { TIMEZONE } from "@/lib/format";
import type { GameRead } from "@/lib/api/types";

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
