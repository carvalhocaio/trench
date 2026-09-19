import type { Metadata } from "next";

import { listGames, listTeams, predictWeek } from "@/lib/api/queries";
import { clampWeek, currentSeason, currentWeek, parseIntParam } from "@/lib/season";
import { indexTeams } from "@/lib/teams";
import { GameCard } from "@/components/game-card";
import { WeekNav } from "@/components/week-nav";

// The root layout's title template does not apply to a page in the same
// route segment, so the composed title is spelled out here.
export const metadata: Metadata = {
  title: "Semana · Trench",
};

export default async function HomePage({ searchParams }: PageProps<"/">) {
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
  const predictions = await predictWeek(season, week);
  const predictionByGameId = new Map(
    (predictions ?? []).map((prediction) => [prediction.game.id, prediction]),
  );
  const teamIndex = indexTeams(teams);

  return (
    <div>
      <WeekNav season={season} week={week} />
      {weekGames.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Nenhum jogo agendado para esta semana.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {weekGames.map((game) => (
            <GameCard
              key={game.id}
              game={game}
              teams={teamIndex}
              prediction={predictionByGameId.get(game.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
