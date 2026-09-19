import Link from "next/link";
import type { Metadata } from "next";

import { listGames, listTeams } from "@/lib/api/queries";
import { clampWeek, currentSeason, currentWeek, parseIntParam } from "@/lib/season";
import { indexTeams, teamOf } from "@/lib/teams";
import { formatKickoff } from "@/lib/format";
import { WeekNav } from "@/components/week-nav";

export const metadata: Metadata = {
  title: "Cadastro",
};

export default async function AdminPage({ searchParams }: PageProps<"/admin">) {
  const params = await searchParams;
  const season = parseIntParam(params.season) ?? currentSeason();

  const [seasonGames, teams] = await Promise.all([
    listGames({ season }),
    listTeams(),
  ]);

  const parsedWeek = parseIntParam(params.week);
  const week =
    parsedWeek !== undefined ? clampWeek(parsedWeek) : currentWeek(seasonGames);
  const weekGames = seasonGames.filter((game) => game.week === week);
  const teamIndex = indexTeams(teams);

  return (
    <div className="space-y-8">
      <div className="flex gap-4">
        <Link
          href="/admin/games/new"
          className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Agendar jogo
        </Link>
        <Link
          href="/admin/players"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:border-nfl-navy"
        >
          Jogadores
        </Link>
      </div>

      <section>
        <WeekNav season={season} week={week} basePath="/admin" />
        {weekGames.length === 0 ? (
          <p className="text-sm text-zinc-500">
            Nenhum jogo agendado para esta semana.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200 rounded-lg border border-zinc-200 bg-white">
            {weekGames.map((game) => {
              const home = teamOf(teamIndex, game.home_team_id);
              const away = teamOf(teamIndex, game.away_team_id);
              return (
                <li key={game.id}>
                  <Link
                    href={`/admin/games/${game.id}`}
                    className="flex items-center justify-between px-4 py-3 text-sm hover:bg-zinc-50"
                  >
                    <span className="tabular-nums text-zinc-500">
                      {formatKickoff(game.kickoff)}
                    </span>
                    <span className="font-medium text-zinc-900">
                      {away.abbreviation} @ {home.abbreviation}
                    </span>
                    <span className="text-nfl-navy">Cadastrar →</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
