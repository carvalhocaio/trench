import Link from "next/link";

const MIN_WEEK = 1;
const MAX_WEEK = 22;

function NavLink({
  season,
  week,
  children,
}: {
  season: number;
  week: number | null;
  children: React.ReactNode;
}) {
  if (week === null) {
    return <span className="text-sm text-zinc-300">{children}</span>;
  }
  return (
    <Link
      href={`/?season=${season}&week=${week}`}
      className="text-sm font-medium text-nfl-navy hover:underline"
    >
      {children}
    </Link>
  );
}

export function WeekNav({ season, week }: { season: number; week: number }) {
  const previousWeek = week > MIN_WEEK ? week - 1 : null;
  const nextWeek = week < MAX_WEEK ? week + 1 : null;

  return (
    <div className="mb-6 flex items-center justify-between">
      <NavLink season={season} week={previousWeek}>
        ← Semana anterior
      </NavLink>
      <h1 className="text-sm font-semibold tabular-nums text-zinc-700">
        Temporada {season} · Semana {week}
      </h1>
      <NavLink season={season} week={nextWeek}>
        Próxima semana →
      </NavLink>
    </div>
  );
}
