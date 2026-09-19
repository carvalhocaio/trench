import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import { ApiError } from "@/lib/api/client";
import {
  getGame,
  getGameStats,
  listAbsences,
  listTeamPlayers,
  listTeams,
} from "@/lib/api/queries";
import { formatKickoff } from "@/lib/format";
import { indexTeams, teamOf } from "@/lib/teams";
import { ScoreForm } from "@/components/admin/score-form";
import { TeamStatsForm } from "@/components/admin/team-stats-form";
import { PlayerStatsSection } from "@/components/admin/player-stats-section";
import { AbsencesSection } from "@/components/admin/absences-section";

export async function generateMetadata({
  params,
}: PageProps<"/admin/games/[id]">): Promise<Metadata> {
  const { id } = await params;
  const game = await getGame(id).catch(() => null);
  if (!game) {
    return {};
  }
  const teams = indexTeams(await listTeams());
  const home = teamOf(teams, game.home_team_id);
  const away = teamOf(teams, game.away_team_id);
  return { title: `Cadastro: ${away.abbreviation} @ ${home.abbreviation}` };
}

export default async function AdminGamePage({
  params,
}: PageProps<"/admin/games/[id]">) {
  const { id } = await params;

  let game;
  try {
    game = await getGame(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  const [teams, gameStats, absences] = await Promise.all([
    listTeams(),
    getGameStats(id),
    listAbsences(id),
  ]);
  const teamIndex = indexTeams(teams);
  const home = teamOf(teamIndex, game.home_team_id);
  const away = teamOf(teamIndex, game.away_team_id);

  const [homePlayers, awayPlayers] = await Promise.all([
    listTeamPlayers(home.id),
    listTeamPlayers(away.id),
  ]);
  const players = [...awayPlayers, ...homePlayers].sort((a, b) =>
    a.name.localeCompare(b.name, "pt-BR"),
  );

  const homeStats = gameStats.team_stats.find((stats) => stats.team_id === home.id);
  const awayStats = gameStats.team_stats.find((stats) => stats.team_id === away.id);

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs tabular-nums text-zinc-500">
          {formatKickoff(game.kickoff)}
        </p>
        <h1 className="text-lg font-semibold text-zinc-900">
          {away.abbreviation} @ {home.abbreviation}
        </h1>
        <Link href={`/games/${id}`} className="text-sm text-nfl-navy hover:underline">
          Ver página do jogo →
        </Link>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-900">Placar</h2>
        <ScoreForm
          gameId={id}
          game={game}
          homeLabel={home.abbreviation}
          awayLabel={away.abbreviation}
        />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-900">
          Estatísticas dos times
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <TeamStatsForm gameId={id} team={away} stats={awayStats} />
          <TeamStatsForm gameId={id} team={home} stats={homeStats} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-900">
          Estatísticas dos jogadores
        </h2>
        <PlayerStatsSection gameId={id} players={players} stats={gameStats.player_stats} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-zinc-900">Injury report</h2>
        <AbsencesSection
          gameId={id}
          players={players}
          absences={absences}
          teams={teamIndex}
        />
      </section>
    </div>
  );
}
