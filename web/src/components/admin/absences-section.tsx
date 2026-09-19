"use client";

import { useActionState } from "react";

import { clearAbsenceAction, reportAbsenceAction } from "@/app/admin/games/[id]/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import { ABSENCE_STATUS_LABELS } from "@/lib/labels";
import { teamOf, type TeamIndex } from "@/lib/teams";
import type { AbsenceRead, AbsenceStatus, PlayerRead } from "@/lib/api/types";

const STATUS_OPTIONS = Object.keys(ABSENCE_STATUS_LABELS) as AbsenceStatus[];

function ClearAbsenceButton({ gameId, playerId }: { gameId: string; playerId: string }) {
  const [state, formAction, pending] = useActionState(
    clearAbsenceAction.bind(null, gameId, playerId),
    initialFormState,
  );

  return (
    <form action={formAction} className="flex flex-col items-end gap-1">
      <button
        type="submit"
        disabled={pending}
        className="text-sm text-nfl-red hover:underline disabled:opacity-50"
      >
        {pending ? "Removendo…" : "Remover"}
      </button>
      {state.formError && <p className="text-xs text-nfl-red">{state.formError}</p>}
    </form>
  );
}

export function AbsencesSection({
  gameId,
  players,
  absences,
  teams,
}: {
  gameId: string;
  players: PlayerRead[];
  absences: AbsenceRead[];
  teams: TeamIndex;
}) {
  const [state, formAction, pending] = useActionState(
    reportAbsenceAction.bind(null, gameId),
    initialFormState,
  );
  const playerById = new Map(players.map((player) => [player.id, player]));

  return (
    <div className="space-y-4">
      {absences.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-zinc-500">
              <th className="pb-2 font-medium">Jogador</th>
              <th className="pb-2 font-medium">Time</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody>
            {absences.map((absence) => {
              const player = playerById.get(absence.player_id);
              const team = player ? teamOf(teams, player.team_id) : null;
              return (
                <tr key={absence.player_id} className="border-t border-zinc-100">
                  <td className="py-2 text-zinc-900">
                    {player?.name ?? absence.player_id}
                  </td>
                  <td className="py-2 text-zinc-600">{team?.abbreviation ?? "—"}</td>
                  <td className="py-2 text-zinc-600">
                    {ABSENCE_STATUS_LABELS[absence.status]}
                  </td>
                  <td className="py-2 text-right">
                    <ClearAbsenceButton gameId={gameId} playerId={absence.player_id} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <form action={formAction} className="space-y-4">
        <FormFeedback
          formError={state.formError}
          success={state.success}
          successMessage="Desfalque registrado com sucesso."
        />
        <div className="flex flex-wrap items-end gap-4">
          <FormField
            label="Jogador"
            htmlFor="player_id"
            error={state.fieldErrors.player_id}
          >
            <select
              id="player_id"
              name="player_id"
              required
              defaultValue={state.values.player_id ?? ""}
              className={FIELD_CLASS}
            >
              <option value="">Selecione um jogador</option>
              {players.map((player) => (
                <option key={player.id} value={player.id}>
                  {player.name}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Status" htmlFor="status" error={state.fieldErrors.status}>
            <select
              id="status"
              name="status"
              required
              defaultValue={state.values.status ?? ""}
              className={FIELD_CLASS}
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {ABSENCE_STATUS_LABELS[status]}
                </option>
              ))}
            </select>
          </FormField>
          <button
            type="submit"
            disabled={pending}
            className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {pending ? "Salvando…" : "Registrar"}
          </button>
        </div>
      </form>
    </div>
  );
}
