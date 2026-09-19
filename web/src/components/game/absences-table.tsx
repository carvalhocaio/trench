import { formatSignedPoints } from "@/lib/format";
import { ABSENCE_STATUS_LABELS } from "@/lib/labels";
import { teamOf, type TeamIndex } from "@/lib/teams";
import type { AbsenceImpactRead } from "@/lib/api/types";

export function AbsencesTable({
  absences,
  teams,
}: {
  absences: AbsenceImpactRead[];
  teams: TeamIndex;
}) {
  if (absences.length === 0) {
    return null;
  }

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-zinc-900">Desfalques</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500">
            <th className="pb-2 font-medium">Jogador</th>
            <th className="pb-2 font-medium">Posição</th>
            <th className="pb-2 font-medium">Status</th>
            <th className="pb-2 font-medium">Time</th>
            <th className="pb-2 text-right font-medium">Impacto</th>
          </tr>
        </thead>
        <tbody>
          {absences.map((absence) => {
            const team = teamOf(teams, absence.affected_team_id);
            return (
              <tr key={absence.player.id} className="border-t border-zinc-100">
                <td className="py-2 font-medium text-zinc-900">
                  {absence.player.name}
                </td>
                <td className="py-2 text-zinc-600">{absence.player.position}</td>
                <td className="py-2 text-zinc-600">
                  {ABSENCE_STATUS_LABELS[absence.status]}
                </td>
                <td className="py-2 text-zinc-600">{team.abbreviation}</td>
                <td className="py-2 text-right tabular-nums text-zinc-900">
                  {formatSignedPoints(absence.points_delta)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
