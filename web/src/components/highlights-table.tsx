import { teamOf, type TeamIndex } from "@/lib/teams";
import type { PlayerSeasonRead } from "@/lib/api/types";

export function HighlightsTable({
  title,
  rows,
  teams,
  valueHeader,
  formatValue,
  formatDetail,
}: {
  title: string;
  rows: PlayerSeasonRead[];
  teams: TeamIndex;
  valueHeader: string;
  formatValue: (row: PlayerSeasonRead) => string;
  formatDetail: (row: PlayerSeasonRead) => string;
}) {
  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-zinc-900">{title}</h2>
      {rows.length === 0 ? (
        <p className="text-sm text-zinc-500">Sem dados suficientes.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-zinc-500">
              <th className="pb-2 font-medium">Jogador</th>
              <th className="pb-2 font-medium">Time</th>
              <th className="pb-2 text-right font-medium">{valueHeader}</th>
              <th className="pb-2 text-right font-medium">Detalhe</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const team = teamOf(teams, row.player.team_id);
              return (
                <tr key={row.player.id} className="border-t border-zinc-100">
                  <td className="py-2 font-medium text-zinc-900">
                    {row.player.name}
                  </td>
                  <td className="py-2 text-zinc-600">{team.abbreviation}</td>
                  <td className="py-2 text-right tabular-nums">
                    {formatValue(row)}
                  </td>
                  <td className="py-2 text-right tabular-nums text-zinc-500">
                    {formatDetail(row)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}
