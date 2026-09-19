import Link from "next/link";

import { FIELD_CLASS, FormField } from "@/components/admin/form-field";
import type { CalibrationParametersRead } from "@/lib/api/types";

export function CalibrationParamsForm({
  season,
  parameters,
}: {
  season: number;
  parameters: CalibrationParametersRead;
}) {
  return (
    <form method="get" className="flex flex-wrap items-end gap-4">
      <FormField label="Temporada" htmlFor="season">
        <input
          type="number"
          id="season"
          name="season"
          defaultValue={season}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField label="Shrinkage (jogos)" htmlFor="shrinkage_games">
        <input
          type="number"
          step="0.1"
          min={0.1}
          id="shrinkage_games"
          name="shrinkage_games"
          defaultValue={parameters.shrinkage_games}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField label="Vantagem de casa" htmlFor="home_field_advantage">
        <input
          type="number"
          step="0.1"
          min={-10}
          max={10}
          id="home_field_advantage"
          name="home_field_advantage"
          defaultValue={parameters.home_field_advantage}
          className={FIELD_CLASS}
        />
      </FormField>
      <FormField label="Desvio do placar" htmlFor="score_margin_stddev">
        <input
          type="number"
          step="0.1"
          min={0.1}
          id="score_margin_stddev"
          name="score_margin_stddev"
          defaultValue={parameters.score_margin_stddev}
          className={FIELD_CLASS}
        />
      </FormField>
      <button
        type="submit"
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Aplicar
      </button>
      <Link
        href={`/calibration?season=${season}`}
        className="text-sm text-zinc-500 hover:underline"
      >
        Restaurar padrão
      </Link>
    </form>
  );
}
