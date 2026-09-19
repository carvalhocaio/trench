"use server";

import { revalidatePath } from "next/cache";

import { api, apiErrorToFormState, unwrap } from "@/lib/api/client";
import type { FormState } from "@/lib/form-state";
import type { Position } from "@/lib/api/types";

const SUCCESS_STATE: FormState = { fieldErrors: {}, formError: null, success: true };

function playerPayload(formData: FormData): {
  name: string;
  team_id: string;
  position: Position;
} {
  return {
    name: String(formData.get("name") ?? ""),
    team_id: String(formData.get("team_id") ?? ""),
    position: String(formData.get("position") ?? "") as Position,
  };
}

function revalidatePlayers(): void {
  revalidatePath("/admin/players");
  revalidatePath("/highlights");
}

export async function registerPlayerAction(
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    unwrap(await api.POST("/players", { body: playerPayload(formData) }));
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidatePlayers();
  return SUCCESS_STATE;
}

export async function updatePlayerAction(
  playerId: string,
  _previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  try {
    unwrap(
      await api.PUT("/players/{player_id}", {
        params: { path: { player_id: playerId } },
        body: playerPayload(formData),
      }),
    );
  } catch (error) {
    return apiErrorToFormState(error);
  }
  revalidatePlayers();
  return SUCCESS_STATE;
}
