"use client";

import { useActionState, useState } from "react";

import { recordPlayerStatsAction } from "@/app/admin/games/[id]/actions";
import { FIELD_CLASS, FormFeedback, FormField, NumberField } from "@/components/admin/form-field";
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
              <th className="pb-2 text-right font-medium">Recepções</th>
              <th className="pb-2 text-right font-medium">Tackles</th>
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
                <td className="py-2 text-right tabular-nums">{line.receptions}</td>
                <td className="py-2 text-right tabular-nums">{line.tackles}</td>
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
        className="max-w-2xl space-y-6"
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
            defaultValue={state.values.player_id ?? editingPlayerId ?? ""}
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

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Passe</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Passes completos"
              name="passing_completions"
              error={state.fieldErrors.passing_completions}
              defaultValue={state.values.passing_completions ?? editingLine?.passing_completions}
            />
            <NumberField
              label="Tentativas de passe"
              name="passing_attempts"
              error={state.fieldErrors.passing_attempts}
              defaultValue={state.values.passing_attempts ?? editingLine?.passing_attempts}
            />
            <NumberField
              label="Jardas de passe"
              name="passing_yards"
              allowNegative
              error={state.fieldErrors.passing_yards}
              defaultValue={state.values.passing_yards ?? editingLine?.passing_yards}
            />
            <NumberField
              label="TDs de passe"
              name="passing_touchdowns"
              error={state.fieldErrors.passing_touchdowns}
              defaultValue={
                state.values.passing_touchdowns ?? editingLine?.passing_touchdowns
              }
            />
            <NumberField
              label="Interceptações sofridas"
              name="interceptions_thrown"
              error={state.fieldErrors.interceptions_thrown}
              defaultValue={
                state.values.interceptions_thrown ?? editingLine?.interceptions_thrown
              }
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Corrida</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Corridas"
              name="rushing_attempts"
              error={state.fieldErrors.rushing_attempts}
              defaultValue={state.values.rushing_attempts ?? editingLine?.rushing_attempts}
            />
            <NumberField
              label="Jardas de corrida"
              name="rushing_yards"
              allowNegative
              error={state.fieldErrors.rushing_yards}
              defaultValue={state.values.rushing_yards ?? editingLine?.rushing_yards}
            />
            <NumberField
              label="TDs de corrida"
              name="rushing_touchdowns"
              error={state.fieldErrors.rushing_touchdowns}
              defaultValue={
                state.values.rushing_touchdowns ?? editingLine?.rushing_touchdowns
              }
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Recepção</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Alvos"
              name="receiving_targets"
              error={state.fieldErrors.receiving_targets}
              defaultValue={state.values.receiving_targets ?? editingLine?.receiving_targets}
            />
            <NumberField
              label="Recepções"
              name="receptions"
              error={state.fieldErrors.receptions}
              defaultValue={state.values.receptions ?? editingLine?.receptions}
            />
            <NumberField
              label="Jardas recebidas"
              name="receiving_yards"
              allowNegative
              error={state.fieldErrors.receiving_yards}
              defaultValue={state.values.receiving_yards ?? editingLine?.receiving_yards}
            />
            <NumberField
              label="TDs de recepção"
              name="receiving_touchdowns"
              error={state.fieldErrors.receiving_touchdowns}
              defaultValue={
                state.values.receiving_touchdowns ?? editingLine?.receiving_touchdowns
              }
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Fumbles</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Fumbles"
              name="fumbles"
              error={state.fieldErrors.fumbles}
              defaultValue={state.values.fumbles ?? editingLine?.fumbles}
            />
            <NumberField
              label="Fumbles perdidos"
              name="fumbles_lost"
              error={state.fieldErrors.fumbles_lost}
              defaultValue={state.values.fumbles_lost ?? editingLine?.fumbles_lost}
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Defesa</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Tackles"
              name="tackles"
              error={state.fieldErrors.tackles}
              defaultValue={state.values.tackles ?? editingLine?.tackles}
            />
            <NumberField
              label="Tackles para perda"
              name="tackles_for_loss"
              step={0.5}
              error={state.fieldErrors.tackles_for_loss}
              defaultValue={state.values.tackles_for_loss ?? editingLine?.tackles_for_loss}
            />
            <NumberField
              label="Sacks"
              name="sacks"
              step={0.5}
              error={state.fieldErrors.sacks}
              defaultValue={state.values.sacks ?? editingLine?.sacks}
            />
            <NumberField
              label="Passes defendidos"
              name="passes_defended"
              error={state.fieldErrors.passes_defended}
              defaultValue={state.values.passes_defended ?? editingLine?.passes_defended}
            />
            <NumberField
              label="Interceptações feitas"
              name="interceptions"
              error={state.fieldErrors.interceptions}
              defaultValue={state.values.interceptions ?? editingLine?.interceptions}
            />
            <NumberField
              label="TDs defensivos"
              name="defensive_touchdowns"
              error={state.fieldErrors.defensive_touchdowns}
              defaultValue={
                state.values.defensive_touchdowns ?? editingLine?.defensive_touchdowns
              }
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Chutes</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Field goals convertidos"
              name="field_goals_made"
              error={state.fieldErrors.field_goals_made}
              defaultValue={state.values.field_goals_made ?? editingLine?.field_goals_made}
            />
            <NumberField
              label="Tentativas de field goal"
              name="field_goals_attempted"
              error={state.fieldErrors.field_goals_attempted}
              defaultValue={
                state.values.field_goals_attempted ?? editingLine?.field_goals_attempted
              }
            />
            <NumberField
              label="Extra points convertidos"
              name="extra_points_made"
              error={state.fieldErrors.extra_points_made}
              defaultValue={state.values.extra_points_made ?? editingLine?.extra_points_made}
            />
            <NumberField
              label="Tentativas de extra point"
              name="extra_points_attempted"
              error={state.fieldErrors.extra_points_attempted}
              defaultValue={
                state.values.extra_points_attempted ?? editingLine?.extra_points_attempted
              }
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">Punt</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Punts"
              name="punts"
              error={state.fieldErrors.punts}
              defaultValue={state.values.punts ?? editingLine?.punts}
            />
            <NumberField
              label="Jardas de punt"
              name="punt_yards"
              allowNegative
              error={state.fieldErrors.punt_yards}
              defaultValue={state.values.punt_yards ?? editingLine?.punt_yards}
            />
          </div>
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="text-sm font-semibold text-zinc-900">
            Special teams (retornos)
          </legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Retornos de kickoff"
              name="kick_returns"
              error={state.fieldErrors.kick_returns}
              defaultValue={state.values.kick_returns ?? editingLine?.kick_returns}
            />
            <NumberField
              label="Jardas em retornos de kickoff"
              name="kick_return_yards"
              allowNegative
              error={state.fieldErrors.kick_return_yards}
              defaultValue={
                state.values.kick_return_yards ?? editingLine?.kick_return_yards
              }
            />
            <NumberField
              label="TDs em retorno de kickoff"
              name="kick_return_touchdowns"
              error={state.fieldErrors.kick_return_touchdowns}
              defaultValue={
                state.values.kick_return_touchdowns ?? editingLine?.kick_return_touchdowns
              }
            />
            <NumberField
              label="Retornos de punt"
              name="punt_returns"
              error={state.fieldErrors.punt_returns}
              defaultValue={state.values.punt_returns ?? editingLine?.punt_returns}
            />
            <NumberField
              label="Jardas em retornos de punt"
              name="punt_return_yards"
              allowNegative
              error={state.fieldErrors.punt_return_yards}
              defaultValue={
                state.values.punt_return_yards ?? editingLine?.punt_return_yards
              }
            />
            <NumberField
              label="TDs em retorno de punt"
              name="punt_return_touchdowns"
              error={state.fieldErrors.punt_return_touchdowns}
              defaultValue={
                state.values.punt_return_touchdowns ?? editingLine?.punt_return_touchdowns
              }
            />
          </div>
        </fieldset>

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
