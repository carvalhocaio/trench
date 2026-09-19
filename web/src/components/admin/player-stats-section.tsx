"use client";

import { useActionState, useState } from "react";

import { recordPlayerStatsAction } from "@/app/admin/games/[id]/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import type { PlayerRead, PlayerStatsRead } from "@/lib/api/types";

export function PlayerStatsSection({
  gameId,
  players,
  stats,
}: {
  gameId: string;
  players: PlayerRead[];
  stats: PlayerStatsRead[];
}) {
  const [state, formAction, pending] = useActionState(
    recordPlayerStatsAction.bind(null, gameId),
    initialFormState,
  );
  const [editingPlayerId, setEditingPlayerId] = useState<string | null>(null);

  const playerById = new Map(players.map((player) => [player.id, player]));
  const editingLine = stats.find((line) => line.player_id === editingPlayerId) ?? null;

  return (
    <div className="space-y-4">
      {stats.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-zinc-500">
              <th className="pb-2 font-medium">Jogador</th>
              <th className="pb-2 text-right font-medium">TDs passe</th>
              <th className="pb-2 text-right font-medium">Corridas</th>
              <th className="pb-2 text-right font-medium">Jardas</th>
              <th className="pb-2 text-right font-medium">Sacks</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody>
            {stats.map((line) => (
              <tr key={line.player_id} className="border-t border-zinc-100">
                <td className="py-2 text-zinc-900">
                  {playerById.get(line.player_id)?.name ?? line.player_id}
                </td>
                <td className="py-2 text-right tabular-nums">
                  {line.passing_touchdowns}
                </td>
                <td className="py-2 text-right tabular-nums">{line.rushing_attempts}</td>
                <td className="py-2 text-right tabular-nums">{line.rushing_yards}</td>
                <td className="py-2 text-right tabular-nums">{line.sacks}</td>
                <td className="py-2 text-right">
                  <button
                    type="button"
                    onClick={() => setEditingPlayerId(line.player_id)}
                    className="text-sm text-nfl-navy hover:underline"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form
        key={editingPlayerId ?? "new"}
        action={formAction}
        className="max-w-md space-y-4"
      >
        <FormFeedback
          formError={state.formError}
          success={state.success}
          successMessage="Estatísticas salvas com sucesso."
        />
        <FormField label="Jogador" htmlFor="player_id" error={state.fieldErrors.player_id}>
          <select
            id="player_id"
            name="player_id"
            required
            defaultValue={editingPlayerId ?? ""}
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
        <FormField
          label="TDs de passe"
          htmlFor="passing_touchdowns"
          error={state.fieldErrors.passing_touchdowns}
        >
          <input
            type="number"
            id="passing_touchdowns"
            name="passing_touchdowns"
            min={0}
            defaultValue={editingLine?.passing_touchdowns ?? 0}
            className={FIELD_CLASS}
          />
        </FormField>
        <FormField
          label="Corridas"
          htmlFor="rushing_attempts"
          error={state.fieldErrors.rushing_attempts}
        >
          <input
            type="number"
            id="rushing_attempts"
            name="rushing_attempts"
            min={0}
            defaultValue={editingLine?.rushing_attempts ?? 0}
            className={FIELD_CLASS}
          />
        </FormField>
        <FormField
          label="Jardas de corrida"
          htmlFor="rushing_yards"
          error={state.fieldErrors.rushing_yards}
        >
          <input
            type="number"
            id="rushing_yards"
            name="rushing_yards"
            defaultValue={editingLine?.rushing_yards ?? 0}
            className={FIELD_CLASS}
          />
        </FormField>
        <FormField label="Sacks" htmlFor="sacks" error={state.fieldErrors.sacks}>
          <input
            type="number"
            id="sacks"
            name="sacks"
            min={0}
            step={0.5}
            defaultValue={editingLine?.sacks ?? 0}
            className={FIELD_CLASS}
          />
        </FormField>
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Salvando…" : "Salvar estatísticas"}
        </button>
      </form>
    </div>
  );
}
