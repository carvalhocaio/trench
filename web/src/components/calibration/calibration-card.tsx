import { isGoodBrier, isSmallSample } from "@/lib/calibration";
import { formatMetric, formatPercent } from "@/lib/format";
import { ReliabilityTable } from "@/components/calibration/reliability-table";
import type { CalibrationReportRead } from "@/lib/api/types";

export function CalibrationCard({
  title,
  report,
}: {
  title: string;
  report: CalibrationReportRead;
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <h3 className="font-semibold text-zinc-900">{title}</h3>
      <dl className="mt-3 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-zinc-500">Previsões</dt>
          <dd className="tabular-nums text-zinc-900">{report.forecasts}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Brier score</dt>
          <dd
            className={`tabular-nums ${isGoodBrier(report.brier_score) ? "text-emerald-600" : "text-zinc-900"}`}
          >
            {formatMetric(report.brier_score)}
          </dd>
          <p className="text-xs text-zinc-400">0,250 = chutar 50%</p>
        </div>
        <div>
          <dt className="text-zinc-500">Log loss</dt>
          <dd className="tabular-nums text-zinc-900">{formatMetric(report.log_loss)}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Acerto do favorito</dt>
          <dd className="tabular-nums text-zinc-900">
            {formatPercent(report.favorite_accuracy)}
          </dd>
        </div>
      </dl>

      {isSmallSample(report.forecasts) && (
        <p className="mt-3 text-xs text-zinc-400">
          Amostra pequena: diferenças de Brier abaixo de ~0,01 tendem a ser ruído.
        </p>
      )}

      <ReliabilityTable bins={report.reliability} />
    </div>
  );
}
