import Link from "next/link";

import { MAX_WEEK, MIN_WEEK } from "@/lib/season";

function NavLink({
  basePath,
  season,
  week,
  children,
}: {
  basePath: string;
  season: number;
  week: number | null;
  children: React.ReactNode;
}) {
  if (week === null) {
    return <span className="text-sm text-zinc-300">{children}</span>;
  }
  return (
    <Link
      href={`${basePath}?season=${season}&week=${week}`}
      className="text-sm font-medium text-nfl-navy hover:underline"
    >
      {children}
    </Link>
  );
}

export function WeekNav({
  season,
  week,
  basePath = "/",
}: {
  season: number;
  week: number;
  basePath?: string;
}) {
  const previousWeek = week > MIN_WEEK ? week - 1 : null;
  const nextWeek = week < MAX_WEEK ? week + 1 : null;

  return (
    <div className="mb-6 flex items-center justify-between">
      <NavLink basePath={basePath} season={season} week={previousWeek}>
        ← Semana anterior
      </NavLink>
      <p className="text-sm font-semibold tabular-nums text-zinc-700">
        Temporada {season} · Semana {week}
      </p>
      <NavLink basePath={basePath} season={season} week={nextWeek}>
        Próxima semana →
      </NavLink>
    </div>
  );
}
