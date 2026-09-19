import { listGames, listTeams, predictWeek } from "@/lib/api/queries";
import { currentSeason, currentWeek } from "@/lib/season";
import { indexTeams } from "@/lib/teams";
import { GameCard } from "@/components/game-card";
import { WeekNav } from "@/components/week-nav";

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const season = Number(params.season) || currentSeason();

  const [seasonGames, teams] = await Promise.all([
    listGames({ season }),
    listTeams(),
  ]);

  const week = Number(params.week) || currentWeek(seasonGames);
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
