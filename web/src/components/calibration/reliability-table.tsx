import { formatReliabilityRange } from "@/lib/calibration";
import { formatPercent } from "@/lib/format";
import type { ReliabilityBinRead } from "@/lib/api/types";

export function ReliabilityTable({ bins }: { bins: ReliabilityBinRead[] }) {
  if (bins.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-zinc-500">
            <th className="pb-2 font-medium">Faixa</th>
            <th className="pb-2 text-right font-medium">Jogos</th>
            <th className="pb-2 text-right font-medium">Prob. prevista</th>
            <th className="pb-2 text-right font-medium">Taxa real</th>
            <th className="pb-2 pl-3 font-medium">Comparação</th>
          </tr>
        </thead>
        <tbody>
          {bins.map((bin) => (
            <tr key={`${bin.lower}-${bin.upper}`} className="border-t border-zinc-100">
              <td className="py-2 text-zinc-900">
                {formatReliabilityRange(bin.lower, bin.upper)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-600">
                {bin.forecasts}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPercent(bin.mean_probability)}
              </td>
              <td className="py-2 text-right tabular-nums text-zinc-900">
                {formatPercent(bin.observed_rate)}
              </td>
              <td className="py-2 pl-3">
                <div className="relative h-2 w-24 rounded-full bg-zinc-100">
                  <div
                    className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2 bg-zinc-400"
                    style={{ left: `${bin.mean_probability * 100}%` }}
                  />
                  <div
                    className="absolute top-1/2 h-3 w-0.5 -translate-y-1/2 bg-nfl-navy"
                    style={{ left: `${bin.observed_rate * 100}%` }}
                  />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-zinc-400">
        Barra: cinza é a probabilidade média prevista, azul-marinho é a taxa real
        observada.
      </p>
    </div>
  );
}
