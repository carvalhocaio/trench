"use client";

import { useActionState } from "react";

import { recordTeamStatsAction } from "@/app/admin/games/[id]/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import type { TeamRead, TeamStatsRead } from "@/lib/api/types";

export function TeamStatsForm({
  gameId,
  team,
  stats,
}: {
  gameId: string;
  team: TeamRead;
  stats: TeamStatsRead | undefined;
}) {
  const [state, formAction, pending] = useActionState(
    recordTeamStatsAction.bind(null, gameId, team.id),
    initialFormState,
  );
  const prefix = team.id;

  return (
    <form
      action={formAction}
      className="space-y-3 rounded-lg border border-zinc-200 bg-white p-4"
    >
      <h3 className="font-semibold text-zinc-900">{team.name}</h3>
      <FormFeedback
        formError={state.formError}
        success={state.success}
        successMessage="Estatísticas salvas com sucesso."
      />
      <FormField
        label="Jogadas ofensivas"
        htmlFor={`offensive_plays_${prefix}`}
        error={state.fieldErrors.offensive_plays}
      >
        <input
          type="number"
          id={`offensive_plays_${prefix}`}
          name="offensive_plays"
          min={0}
          required
          defaultValue={stats?.offensive_plays ?? 0}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField
        label="Jardas de passe"
        htmlFor={`passing_yards_${prefix}`}
        error={state.fieldErrors.passing_yards}
      >
        <input
          type="number"
          id={`passing_yards_${prefix}`}
          name="passing_yards"
          required
          defaultValue={stats?.passing_yards ?? 0}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField
        label="Jardas de corrida"
        htmlFor={`rushing_yards_${prefix}`}
        error={state.fieldErrors.rushing_yards}
      >
        <input
          type="number"
          id={`rushing_yards_${prefix}`}
          name="rushing_yards"
          required
          defaultValue={stats?.rushing_yards ?? 0}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField
        label="Turnovers"
        htmlFor={`turnovers_${prefix}`}
        error={state.fieldErrors.turnovers}
      >
        <input
          type="number"
          id={`turnovers_${prefix}`}
          name="turnovers"
          min={0}
          required
          defaultValue={stats?.turnovers ?? 0}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField label="Sacks" htmlFor={`sacks_${prefix}`} error={state.fieldErrors.sacks}>
        <input
          type="number"
          id={`sacks_${prefix}`}
          name="sacks"
          min={0}
          required
          defaultValue={stats?.sacks ?? 0}
          className={FIELD_CLASS}
        />
      </FormField>
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Salvando…" : "Salvar"}
      </button>
    </form>
  );
}
