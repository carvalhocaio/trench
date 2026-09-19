"use client";

import { useActionState, useEffect, useState } from "react";

import { registerPlayerAction, updatePlayerAction } from "@/app/admin/players/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import { POSITION_OPTIONS } from "@/lib/labels";
import type { PlayerRead, TeamRead } from "@/lib/api/types";

type EditTarget = { id: string; player: PlayerRead };

function PlayerFormFields({
  teams,
  editTarget,
  onDone,
}: {
  teams: TeamRead[];
  editTarget: EditTarget | null;
  onDone: () => void;
}) {
  const action = editTarget
    ? updatePlayerAction.bind(null, editTarget.id)
    : registerPlayerAction;
  const [state, formAction, pending] = useActionState(action, initialFormState);

  useEffect(() => {
    if (editTarget && state.success) {
      onDone();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only react to a save completing
  }, [state]);

  return (
    <form action={formAction} className="max-w-md space-y-4">
      <FormFeedback
        formError={state.formError}
        success={state.success}
        successMessage={
          editTarget ? "Jogador atualizado com sucesso." : "Jogador cadastrado com sucesso."
        }
      />
      <FormField label="Nome" htmlFor="name" error={state.fieldErrors.name}>
        <input
          type="text"
          id="name"
          name="name"
          required
          defaultValue={state.values.name ?? editTarget?.player.name ?? ""}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField label="Time" htmlFor="team_id" error={state.fieldErrors.team_id}>
        <select
          id="team_id"
          name="team_id"
          required
          defaultValue={state.values.team_id ?? editTarget?.player.team_id ?? ""}
          className={FIELD_CLASS}
        >
          <option value="">Selecione um time</option>
          {teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>
      </FormField>
      <FormField label="Posição" htmlFor="position" error={state.fieldErrors.position}>
        <select
          id="position"
          name="position"
          required
          defaultValue={state.values.position ?? editTarget?.player.position ?? ""}
          className={FIELD_CLASS}
        >
          <option value="">Selecione uma posição</option>
          {POSITION_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </FormField>
      {editTarget && (
        <p className="text-xs text-zinc-500">
          Em caso de troca de time, lance as estatísticas do último jogo pelo time
          atual antes de salvar esta mudança.
        </p>
      )}
      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={pending}
          className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Salvando…" : editTarget ? "Salvar alterações" : "Cadastrar jogador"}
        </button>
        {editTarget && (
          <button
            type="button"
            onClick={onDone}
            className="text-sm text-zinc-500 hover:underline"
          >
            Cancelar edição
          </button>
        )}
      </div>
    </form>
  );
}

export function PlayerForm({
  teams,
  roster,
}: {
  teams: TeamRead[];
  roster: PlayerRead[];
}) {
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);

  return (
    <div className="space-y-6">
      {roster.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-zinc-500">
              <th className="pb-2 font-medium">Nome</th>
              <th className="pb-2 font-medium">Posição</th>
              <th className="pb-2" />
            </tr>
          </thead>
          <tbody>
            {roster.map((player) => (
              <tr key={player.id} className="border-t border-zinc-100">
                <td className="py-2 text-zinc-900">{player.name}</td>
                <td className="py-2 text-zinc-600">{player.position}</td>
                <td className="py-2 text-right">
                  <button
                    type="button"
                    onClick={() => setEditTarget({ id: player.id, player })}
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

      <h2 className="text-sm font-semibold text-zinc-900">
        {editTarget ? `Editar ${editTarget.player.name}` : "Cadastrar jogador"}
      </h2>
      <PlayerFormFields
        key={editTarget?.id ?? "new"}
        teams={teams}
        editTarget={editTarget}
        onDone={() => setEditTarget(null)}
      />
    </div>
  );
}
