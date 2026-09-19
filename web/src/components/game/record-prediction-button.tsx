"use client";

import { useActionState } from "react";

import { recordPredictionAction } from "@/app/games/[id]/actions";

export function RecordPredictionButton({ gameId }: { gameId: string }) {
  const [state, formAction, pending] = useActionState(
    recordPredictionAction.bind(null, gameId),
    null,
  );

  return (
    <form action={formAction} className="flex flex-col items-start gap-2">
      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Registrando…" : "Registrar previsão"}
      </button>
      {state?.error && <p className="text-sm text-nfl-red">{state.error}</p>}
    </form>
  );
}
