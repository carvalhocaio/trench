import { notFound } from "next/navigation";
import { Suspense } from "react";
import type { Metadata } from "next";

import { ApiError } from "@/lib/api/client";
import {
  getGame,
  getPrediction,
  getPredictionHistory,
  listTeams,
} from "@/lib/api/queries";
import { indexTeams, teamOf } from "@/lib/teams";
import { GameHeader } from "@/components/game/game-header";
import { GameSides } from "@/components/game/game-sides";
import { AbsencesTable } from "@/components/game/absences-table";
import { PredictionHistoryTable } from "@/components/game/prediction-history-table";
import { GamePreview } from "@/components/game/game-preview";
import { GamePreviewSkeleton } from "@/components/game/game-preview-skeleton";
import { RecordPredictionButton } from "@/components/game/record-prediction-button";
import { AdminGameLink } from "@/components/game/admin-game-link";

export async function generateMetadata({
  params,
}: PageProps<"/games/[id]">): Promise<Metadata> {
  const { id } = await params;
  const game = await getGame(id).catch(() => null);
  if (!game) {
    return {};
  }
  const teams = indexTeams(await listTeams());
  const home = teamOf(teams, game.home_team_id);
  const away = teamOf(teams, game.away_team_id);
  return { title: `${away.abbreviation} @ ${home.abbreviation}` };
}

export default async function GamePage({ params }: PageProps<"/games/[id]">) {
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

  const [teams, prediction, history] = await Promise.all([
    listTeams(),
    getPrediction(id),
    getPredictionHistory(id),
  ]);
  const teamIndex = indexTeams(teams);
  const home = teamOf(teamIndex, game.home_team_id);
  const away = teamOf(teamIndex, game.away_team_id);

  return (
    <div className="space-y-6">
      <GameHeader game={game} home={home} away={away} prediction={prediction} />

      {prediction && (
        <>
          <GameSides prediction={prediction} home={home} away={away} />
          <AbsencesTable absences={prediction.absences} teams={teamIndex} />
          <Suspense fallback={<GamePreviewSkeleton />}>
            <GamePreview gameId={id} />
          </Suspense>
          <RecordPredictionButton gameId={id} />
        </>
      )}

      <PredictionHistoryTable snapshots={history} home={home} away={away} />

      <AdminGameLink gameId={id} />
    </div>
  );
}
