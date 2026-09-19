import "server-only";

import { cache } from "react";

import { api, ApiError, unwrap } from "@/lib/api/client";
import type {
  AbsenceRead,
  GameRead,
  GameStatsRead,
  HighlightsRead,
  PlayerRead,
  PredictionRead,
  PreviewRead,
  SnapshotRead,
  TeamRead,
} from "@/lib/api/types";

export async function listTeams(): Promise<TeamRead[]> {
  return unwrap(await api.GET("/teams"));
}

export async function listTeamPlayers(teamId: string): Promise<PlayerRead[]> {
  return unwrap(
    await api.GET("/teams/{team_id}/players", { params: { path: { team_id: teamId } } }),
  );
}

export async function getGameStats(gameId: string): Promise<GameStatsRead> {
  return unwrap(
    await api.GET("/games/{game_id}/stats", { params: { path: { game_id: gameId } } }),
  );
}

export async function listAbsences(gameId: string): Promise<AbsenceRead[]> {
  return unwrap(
    await api.GET("/games/{game_id}/absences", { params: { path: { game_id: gameId } } }),
  );
}

export const getGame = cache(async (gameId: string): Promise<GameRead> => {
  return unwrap(
    await api.GET("/games/{game_id}", { params: { path: { game_id: gameId } } }),
  );
});

export async function listGames(params: {
  season: number;
  week?: number;
  teamId?: string;
}): Promise<GameRead[]> {
  return unwrap(
    await api.GET("/games", {
      params: {
        query: { season: params.season, week: params.week, team_id: params.teamId },
      },
    }),
  );
}

export async function seasonHighlights(season: number): Promise<HighlightsRead> {
  return unwrap(await api.GET("/highlights", { params: { query: { season } } }));
}

export async function predictWeek(
  season: number,
  week: number,
): Promise<PredictionRead[] | null> {
  try {
    return unwrap(
      await api.GET("/predictions", { params: { query: { season, week } } }),
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      return null;
    }
    throw error;
  }
}

export async function getPrediction(gameId: string): Promise<PredictionRead | null> {
  try {
    return unwrap(
      await api.GET("/games/{game_id}/prediction", {
        params: { path: { game_id: gameId } },
      }),
    );
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      return null;
    }
    throw error;
  }
}

export async function getPredictionHistory(gameId: string): Promise<SnapshotRead[]> {
  return unwrap(
    await api.GET("/games/{game_id}/prediction/history", {
      params: { path: { game_id: gameId } },
    }),
  );
}

export async function getPreview(gameId: string): Promise<PreviewRead> {
  return unwrap(
    await api.GET("/games/{game_id}/preview", {
      params: { path: { game_id: gameId } },
    }),
  );
}
