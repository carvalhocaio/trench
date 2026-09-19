import "server-only";

import { api, ApiError, unwrap } from "@/lib/api/client";
import type {
  GameRead,
  HighlightsRead,
  PredictionRead,
  TeamRead,
} from "@/lib/api/types";

export async function listTeams(): Promise<TeamRead[]> {
  return unwrap(await api.GET("/teams"));
}

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
