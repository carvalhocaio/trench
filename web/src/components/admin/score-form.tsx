"use client";

import { useActionState } from "react";

import { recordScoreAction } from "@/app/admin/games/[id]/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import type { GameRead } from "@/lib/api/types";

export function ScoreForm({
  gameId,
  game,
  homeLabel,
  awayLabel,
}: {
  gameId: string;
  game: GameRead;
  homeLabel: string;
  awayLabel: string;
}) {
  const [state, formAction, pending] = useActionState(
    recordScoreAction.bind(null, gameId),
    initialFormState,
  );

  return (
    <form action={formAction} className="space-y-4">
      <FormFeedback
        formError={state.formError}
        success={state.success}
        successMessage="Placar salvo com sucesso."
      />
      <div className="flex flex-wrap items-end gap-4">
        <FormField
          label={`Pontos ${awayLabel}`}
          htmlFor="away"
          error={state.fieldErrors.away}
        >
          <input
            type="number"
            id="away"
            name="away"
            min={0}
            required
            defaultValue={game.score?.away}
            className={FIELD_CLASS}
          />
        </FormField>
        <FormField
          label={`Pontos ${homeLabel}`}
          htmlFor="home"
          error={state.fieldErrors.home}
        >
          <input
            type="number"
            id="home"
            name="home"
            min={0}
            required
            defaultValue={game.score?.home}
            className={FIELD_CLASS}
          />
        </FormField>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Salvando…" : "Salvar placar"}
        </button>
      </div>
    </form>
  );
}
