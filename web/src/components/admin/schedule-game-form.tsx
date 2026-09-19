"use client";

import { useActionState, useState } from "react";

import { scheduleGameAction } from "@/app/admin/games/new/actions";
import { FIELD_CLASS, FormFeedback, FormField } from "@/components/admin/form-field";
import { initialFormState } from "@/lib/form-state";
import { MAX_WEEK, MIN_WEEK } from "@/lib/season-constants";
import type { TeamRead } from "@/lib/api/types";

export function ScheduleGameForm({
  teams,
  defaultSeason,
}: {
  teams: TeamRead[];
  defaultSeason: number;
}) {
  const [state, formAction, pending] = useActionState(
    scheduleGameAction,
    initialFormState,
  );
  const [homeTeamId, setHomeTeamId] = useState("");
  const [awayTeamId, setAwayTeamId] = useState("");
  const sameTeam = homeTeamId !== "" && homeTeamId === awayTeamId;

  return (
    <form action={formAction} className="space-y-4">
      <FormFeedback
        formError={state.formError}
        success={state.success}
        successMessage="Jogo agendado com sucesso."
      />

      <FormField label="Temporada" htmlFor="season" error={state.fieldErrors.season}>
        <input
          type="number"
          id="season"
          name="season"
          required
          defaultValue={state.values.season ?? defaultSeason}
          className={FIELD_CLASS}
        />
      </FormField>

      <FormField label="Semana" htmlFor="week" error={state.fieldErrors.week}>
        <input
          type="number"
          id="week"
          name="week"
          required
          min={MIN_WEEK}
          max={MAX_WEEK}
          defaultValue={state.values.week}
          className={FIELD_CLASS}
        />
      </FormField>

      <FormField label="Data e hora" htmlFor="kickoff" error={state.fieldErrors.kickoff}>
        <input
          type="datetime-local"
          id="kickoff"
          name="kickoff"
          required
          defaultValue={state.values.kickoff}
          className={FIELD_CLASS}
        />
      </FormField>

      <FormField
        label="Visitante"
        htmlFor="away_team_id"
        error={state.fieldErrors.away_team_id}
      >
        <select
          id="away_team_id"
          name="away_team_id"
          required
          value={awayTeamId}
          onChange={(event) => setAwayTeamId(event.target.value)}
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

      <FormField
        label="Mandante"
        htmlFor="home_team_id"
        error={state.fieldErrors.home_team_id}
      >
        <select
          id="home_team_id"
          name="home_team_id"
          required
          value={homeTeamId}
          onChange={(event) => setHomeTeamId(event.target.value)}
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

      {sameTeam && (
        <p className="text-sm text-nfl-red">
          Mandante e visitante devem ser diferentes.
        </p>
      )}

      <button
        type="submit"
        disabled={pending || sameTeam}
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Agendando…" : "Agendar jogo"}
      </button>
    </form>
  );
}
