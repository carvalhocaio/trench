"use server";

import { revalidatePath } from "next/cache";

import { api, ApiError, unwrap } from "@/lib/api/client";

export type RecordPredictionState = { error: string } | null;

export async function recordPredictionAction(
  gameId: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- required by useActionState's signature
  previousState: RecordPredictionState,
): Promise<RecordPredictionState> {
  try {
    unwrap(
      await api.POST("/games/{game_id}/prediction", {
        params: { path: { game_id: gameId } },
      }),
    );
  } catch (error) {
    if (error instanceof ApiError) {
      return { error: typeof error.detail === "string" ? error.detail : error.message };
    }
    throw error;
  }

  revalidatePath(`/games/${gameId}`);
  return null;
}
