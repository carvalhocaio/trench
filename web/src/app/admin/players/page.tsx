import type { Metadata } from "next";

import { listTeamPlayers, listTeams } from "@/lib/api/queries";
import { FIELD_CLASS, FormField } from "@/components/admin/form-field";
import { PlayerForm } from "@/components/admin/player-form";

export const metadata: Metadata = {
  title: "Jogadores",
};

export default async function PlayersAdminPage({
  searchParams,
}: PageProps<"/admin/players">) {
  const params = await searchParams;
  const teams = await listTeams();
  const sortedTeams = [...teams].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  const rawTeam = params.team;
  const teamParam = Array.isArray(rawTeam) ? rawTeam[0] : rawTeam;
  const selectedTeamId = teamParam ?? sortedTeams[0]?.id ?? "";

  const roster = selectedTeamId ? await listTeamPlayers(selectedTeamId) : [];
  const sortedRoster = [...roster].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  return (
    <div className="space-y-8">
      <h1 className="text-lg font-semibold text-zinc-900">Jogadores</h1>

      <form method="get" className="flex flex-wrap items-end gap-4">
        <FormField label="Time" htmlFor="team">
          <select
            id="team"
            name="team"
            defaultValue={selectedTeamId}
            className={FIELD_CLASS}
          >
            {sortedTeams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
        </FormField>
        <button
          type="submit"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:border-nfl-navy"
        >
          Ver elenco
        </button>
      </form>

      <PlayerForm teams={sortedTeams} roster={sortedRoster} />
    </div>
  );
}
