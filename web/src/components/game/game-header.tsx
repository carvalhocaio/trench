import { formatKickoff, formatPoints } from "@/lib/format";
import { ProbabilityBar } from "@/components/probability-bar";
import type { GameRead, PredictionRead, TeamRead } from "@/lib/api/types";

export function GameHeader({
  game,
  home,
  away,
  prediction,
}: {
  game: GameRead;
  home: TeamRead;
  away: TeamRead;
  prediction: PredictionRead | null;
}) {
  const isFinal = game.status === "FINAL";

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-6">
      <p className="text-xs tabular-nums text-zinc-500">{formatKickoff(game.kickoff)}</p>
      <h1 className="mt-1 text-xl font-semibold text-zinc-900">
        {away.abbreviation} @ {home.abbreviation}
      </h1>
      <p className="text-sm text-zinc-500">
        {away.name} @ {home.name}
      </p>

      {isFinal && game.score && (
        <p className="mt-4 text-3xl font-bold tabular-nums text-zinc-900">
          {game.score.away} – {game.score.home}
        </p>
      )}

      {prediction ? (
        <div className="mt-4 max-w-sm space-y-3">
          <div className="flex items-center justify-between text-sm tabular-nums text-zinc-700">
            <span>
              {away.abbreviation} {formatPoints(prediction.away.projected_points)}
            </span>
            <span>
              {home.abbreviation} {formatPoints(prediction.home.projected_points)}
            </span>
          </div>
          <ProbabilityBar
            topLabel={away.abbreviation}
            topProbability={prediction.away.win_probability}
            bottomLabel={home.abbreviation}
            bottomProbability={prediction.home.win_probability}
          />
        </div>
      ) : (
        <p className="mt-4 text-sm text-zinc-400">
          Projeção indisponível para esta semana.
        </p>
      )}
    </div>
  );
}
