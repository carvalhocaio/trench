import { formatPercent, formatPoints } from "@/lib/format";
import type { PredictionRead, SideRead, TeamRead } from "@/lib/api/types";

function SideCard({ team, side }: { team: TeamRead; side: SideRead }) {
  const { rating } = side;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <h3 className="font-semibold text-zinc-900">{team.name}</h3>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex justify-between">
          <dt className="text-zinc-500">Pontos projetados</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPoints(side.projected_points)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Probabilidade de vitória</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPercent(side.win_probability)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Jogos disputados</dt>
          <dd className="tabular-nums text-zinc-900">{rating.games_played}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Retrospecto</dt>
          <dd className="tabular-nums text-zinc-900">
            {rating.wins}-{rating.losses}
            {rating.ties > 0 ? `-${rating.ties}` : ""}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Média de pontos feitos</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPoints(rating.points_for_avg)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Média de pontos sofridos</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPoints(rating.points_against_avg)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Força de ataque</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPoints(rating.offense_strength)}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-zinc-500">Força de defesa</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPoints(rating.defense_strength)}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export function GameSides({
  prediction,
  home,
  away,
}: {
  prediction: PredictionRead;
  home: TeamRead;
  away: TeamRead;
}) {
  return (
    <div>
      <div className="grid gap-4 sm:grid-cols-2">
        <SideCard team={away} side={prediction.away} />
        <SideCard team={home} side={prediction.home} />
      </div>
      <p className="mt-2 text-xs text-zinc-400">
        Força de defesa acima de 1,0 indica que a defesa sofre mais pontos do que a
        média da liga.
      </p>
    </div>
  );
}
