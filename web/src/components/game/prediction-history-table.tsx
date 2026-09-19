import { formatDateTime, formatPercent, formatPoints } from "@/lib/format";
import type { SnapshotRead, TeamRead } from "@/lib/api/types";

export function PredictionHistoryTable({
  snapshots,
  home,
  away,
}: {
  snapshots: SnapshotRead[];
  home: TeamRead;
  away: TeamRead;
}) {
  if (snapshots.length === 0) {
    return null;
  }

  const sorted = [...snapshots].sort((a, b) => b.as_of.localeCompare(a.as_of));

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-zinc-900">
        Histórico de previsões
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500">
            <th className="pb-2 font-medium">Data e hora</th>
            <th className="pb-2 text-right font-medium">Prob. {home.abbreviation}</th>
            <th className="pb-2 text-right font-medium">Prob. {away.abbreviation}</th>
            <th className="pb-2 text-right font-medium">Pontos {home.abbreviation}</th>
            <th className="pb-2 text-right font-medium">Pontos {away.abbreviation}</th>
            <th className="pb-2 text-right font-medium">Modelo</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((snapshot) => (
            <tr key={snapshot.id} className="border-t border-zinc-100">
              <td className="py-2 tabular-nums text-zinc-600">
                {formatDateTime(snapshot.as_of)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPercent(snapshot.home_win_probability)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPercent(snapshot.away_win_probability)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPoints(snapshot.home_projected_points)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPoints(snapshot.away_projected_points)}
              </td>
              <td className="py-2 text-right text-zinc-500">
                {snapshot.model_version}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
