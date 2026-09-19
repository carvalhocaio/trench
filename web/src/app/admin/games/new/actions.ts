"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";

import { api, apiErrorToFormState, unwrap } from "@/lib/api/client";
import type { FormState } from "@/lib/form-state";
import { TIMEZONE } from "@/lib/format";
import { toZonedOffsetISOString } from "@/lib/timezone";

export async function scheduleGameAction(
  previousState: FormState,
  formData: FormData,
): Promise<FormState> {
  const kickoffLocal = String(formData.get("kickoff") ?? "");
  const payload = {
    season: Number(formData.get("season")),
    week: Number(formData.get("week")),
    kickoff: kickoffLocal ? toZonedOffsetISOString(kickoffLocal, TIMEZONE) : "",
    home_team_id: String(formData.get("home_team_id") ?? ""),
    away_team_id: String(formData.get("away_team_id") ?? ""),
  };

  let gameId: string;
  try {
    gameId = unwrap(await api.POST("/games", { body: payload })).id;
  } catch (error) {
    return apiErrorToFormState(error);
  }

  revalidatePath("/");
  revalidatePath("/admin");
  redirect(`/admin/games/${gameId}`);
}
