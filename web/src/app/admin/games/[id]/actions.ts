"use server";

import { revalidatePath } from "next/cache";

import { api, apiErrorToFormState, unwrap } from "@/lib/api/client";
import type { FormState } from "@/lib/form-state";
import type { AbsenceStatus } from "@/lib/api/types";

const SUCCESS_STATE: FormState = {
  fieldErrors: {},
  formError: null,
  success: true,
  values: {},
};

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
    return apiErrorToFormState(error, formData);
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
    return apiErrorToFormState(error, formData);
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
  const stat = (name: string) => Number(formData.get(name) || 0);
  try {
    unwrap(
      await api.PUT("/games/{game_id}/player-stats/{player_id}", {
        params: { path: { game_id: gameId, player_id: playerId } },
        body: {
          passing_completions: stat("passing_completions"),
          passing_attempts: stat("passing_attempts"),
          passing_yards: stat("passing_yards"),
          passing_touchdowns: stat("passing_touchdowns"),
          interceptions_thrown: stat("interceptions_thrown"),
          rushing_attempts: stat("rushing_attempts"),
          rushing_yards: stat("rushing_yards"),
          rushing_touchdowns: stat("rushing_touchdowns"),
          receiving_targets: stat("receiving_targets"),
          receptions: stat("receptions"),
          receiving_yards: stat("receiving_yards"),
          receiving_touchdowns: stat("receiving_touchdowns"),
          fumbles: stat("fumbles"),
          fumbles_lost: stat("fumbles_lost"),
          tackles: stat("tackles"),
          tackles_for_loss: stat("tackles_for_loss"),
          sacks: stat("sacks"),
          passes_defended: stat("passes_defended"),
          interceptions: stat("interceptions"),
          defensive_touchdowns: stat("defensive_touchdowns"),
          field_goals_made: stat("field_goals_made"),
          field_goals_attempted: stat("field_goals_attempted"),
          extra_points_made: stat("extra_points_made"),
          extra_points_attempted: stat("extra_points_attempted"),
          punts: stat("punts"),
          punt_yards: stat("punt_yards"),
          kick_returns: stat("kick_returns"),
          kick_return_yards: stat("kick_return_yards"),
          kick_return_touchdowns: stat("kick_return_touchdowns"),
          punt_returns: stat("punt_returns"),
          punt_return_yards: stat("punt_return_yards"),
          punt_return_touchdowns: stat("punt_return_touchdowns"),
        },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error, formData);
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
    return apiErrorToFormState(error, formData);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}

export async function clearAbsenceAction(
  gameId: string,
  playerId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    unwrap(
      await api.DELETE("/games/{game_id}/absences/{player_id}", {
        params: { path: { game_id: gameId, player_id: playerId } },
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error, formData);
  }
  revalidateGame(gameId);
  return SUCCESS_STATE;
}
