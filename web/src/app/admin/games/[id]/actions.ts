"use server";

import { revalidatePath } from "next/cache";

import { api, apiErrorToFormState, unwrap } from "@/lib/api/client";
import type { FormState } from "@/lib/form-state";
import type { AbsenceStatus } from "@/lib/api/types";

const SUCCESS_STATE: FormState = { fieldErrors: {}, formError: null, success: true };

function revalidateGame(gameId: string): void {
  revalidatePath(`/admin/games/${gameId}`);
  revalidatePath(`/games/${gameId}`);
  revalidatePath("/");
}

export async function recordScoreAction(
  gameId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    unwrap(
      await api.PUT("/games/{game_id}/score", {
        params: { path: { game_id: gameId } },
        body: {
          home: Number(formData.get("home")),
          away: Number(formData.get("away")),
        },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}

export async function recordTeamStatsAction(
  gameId: string,
  teamId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    unwrap(
      await api.PUT("/games/{game_id}/team-stats/{team_id}", {
        params: { path: { game_id: gameId, team_id: teamId } },
        body: {
          offensive_plays: Number(formData.get("offensive_plays")),
          passing_yards: Number(formData.get("passing_yards")),
          rushing_yards: Number(formData.get("rushing_yards")),
          turnovers: Number(formData.get("turnovers")),
          sacks: Number(formData.get("sacks")),
        },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}

export async function recordPlayerStatsAction(
  gameId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  const playerId = String(formData.get("player_id") ?? "");
  try {
    unwrap(
      await api.PUT("/games/{game_id}/player-stats/{player_id}", {
        params: { path: { game_id: gameId, player_id: playerId } },
        body: {
          passing_touchdowns: Number(formData.get("passing_touchdowns") || 0),
          rushing_attempts: Number(formData.get("rushing_attempts") || 0),
          rushing_yards: Number(formData.get("rushing_yards") || 0),
          sacks: Number(formData.get("sacks") || 0),
        },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}

export async function reportAbsenceAction(
  gameId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  const playerId = String(formData.get("player_id") ?? "");
  const status = String(formData.get("status") ?? "") as AbsenceStatus;
  try {
    unwrap(
      await api.PUT("/games/{game_id}/absences/{player_id}", {
        params: { path: { game_id: gameId, player_id: playerId } },
        body: { status },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}

export async function clearAbsenceAction(
  gameId: string,
  playerId: string,
  _previousState: FormState,
): Promise<FormState> {
  try {
    unwrap(
      await api.DELETE("/games/{game_id}/absences/{player_id}", {
        params: { path: { game_id: gameId, player_id: playerId } },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}
