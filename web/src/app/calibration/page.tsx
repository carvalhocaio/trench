import type { Metadata } from "next";

import { getCalibration } from "@/lib/api/queries";
import { parseFloatParam } from "@/lib/calibration";
import { currentSeason, parseIntParam } from "@/lib/season";
import { CalibrationCard } from "@/components/calibration/calibration-card";
import { CalibrationParamsForm } from "@/components/calibration/params-form";

export const metadata: Metadata = {
  title: "Calibração",
};

export default async function CalibrationPage({
  searchParams,
}: PageProps<"/calibration">) {
  const params = await searchParams;
  const season = parseIntParam(params.season) ?? currentSeason();

  const data = await getCalibration({
    season,
    shrinkageGames: parseFloatParam(params.shrinkage_games),
    homeFieldAdvantage: parseFloatParam(params.home_field_advantage),
    scoreMarginStddev: parseFloatParam(params.score_margin_stddev),
  });

  const hasData = data.backtest !== null || data.live.length > 0;

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-zinc-900">Calibração</h1>

      <CalibrationParamsForm season={season} parameters={data.parameters} />

      <section className="rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-600">
        <p>
          <strong className="text-zinc-900">Backtest</strong>: todos os jogos já
          disputados, previstos usando apenas os jogos anteriores; serve para comparar
          parâmetros.
        </p>
        <p className="mt-2">
          <strong className="text-zinc-900">Ao vivo</strong>: os snapshots registrados
          antes de cada kickoff; é a prova real.
        </p>
      </section>

      {hasData ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.backtest && <CalibrationCard title="Backtest" report={data.backtest} />}
          {data.live.map((entry) => (
            <CalibrationCard
              key={entry.model_version}
              title={`Ao vivo · v${entry.model_version}`}
              report={entry.report}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500">
          Ainda não há jogos finalizados para avaliar.
        </p>
      )}
    </div>
  );
}
