import Link from "next/link";

import { formatKickoff, formatPoints } from "@/lib/format";
import { ProbabilityBar } from "@/components/probability-bar";
import { teamOf, type TeamIndex } from "@/lib/teams";
import type { GameRead, PredictionRead } from "@/lib/api/types";

function TeamRow({
  name,
  isHome,
  projectedPoints,
  score,
}: {
  name: string;
  isHome: boolean;
  projectedPoints: number | undefined;
  score: number | undefined;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="font-medium text-zinc-900">
        {isHome && <span className="mr-1 text-zinc-400">@</span>}
        {name}
      </span>
      <span className="flex items-center gap-3 tabular-nums">
        {projectedPoints !== undefined && (
          <span className="text-sm text-zinc-500">{formatPoints(projectedPoints)}</span>
        )}
        {score !== undefined && (
          <span className="text-lg font-semibold text-zinc-900">{score}</span>
        )}
      </span>
    </div>
  );
}

export function GameCard({
  game,
  teams,
  prediction,
}: {
  game: GameRead;
  teams: TeamIndex;
  prediction?: PredictionRead;
}) {
  const home = teamOf(teams, game.home_team_id);
  const away = teamOf(teams, game.away_team_id);
  const isFinal = game.status === "FINAL";

  return (
    <Link
      href={`/games/${game.id}`}
      className="block rounded-lg border border-zinc-200 bg-white p-4 transition hover:border-nfl-navy hover:shadow-sm"
    >
      <p className="mb-3 text-xs tabular-nums text-zinc-500">
        {formatKickoff(game.kickoff)}
      </p>
      <div className="space-y-2">
        <TeamRow
          name={away.name}
          isHome={false}
          projectedPoints={prediction?.away.projected_points}
          score={isFinal ? game.score?.away : undefined}
        />
        <TeamRow
          name={home.name}
          isHome
          projectedPoints={prediction?.home.projected_points}
          score={isFinal ? game.score?.home : undefined}
        />
      </div>
      {prediction && (
        <div className="mt-4">
          <ProbabilityBar
            topLabel={away.abbreviation}
            topProbability={prediction.away.win_probability}
            bottomLabel={home.abbreviation}
            bottomProbability={prediction.home.win_probability}
          />
        </div>
      )}
    </Link>
  );
}
