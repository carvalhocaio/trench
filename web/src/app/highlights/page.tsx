import { listTeams, seasonHighlights } from "@/lib/api/queries";
import { currentSeason } from "@/lib/season";
import { indexTeams } from "@/lib/teams";
import { formatNumber, pluralize } from "@/lib/format";
import { HighlightsTable } from "@/components/highlights-table";

export default async function HighlightsPage({
  searchParams,
}: PageProps<"/highlights">) {
  const params = await searchParams;
  const season = Number(params.season) || currentSeason();

  const [highlights, teams] = await Promise.all([
    seasonHighlights(season),
    listTeams(),
  ]);
  const teamIndex = indexTeams(teams);

  return (
    <div>
      <h1 className="mb-6 text-sm font-semibold tabular-nums text-zinc-700">
        Destaques da temporada {season}
      </h1>
      <div className="grid gap-4 lg:grid-cols-3">
        <HighlightsTable
          title="Passes para touchdown"
          rows={highlights.passing_touchdowns}
          teams={teamIndex}
          valueHeader="TDs"
          formatValue={(row) => formatNumber(row.passing_touchdowns)}
          formatDetail={(row) => pluralize(row.games, "jogo", "jogos")}
        />
        <HighlightsTable
          title="Jardas por corrida"
          rows={highlights.yards_per_carry}
          teams={teamIndex}
          valueHeader="Jardas/corrida"
          formatValue={(row) => formatNumber(row.yards_per_carry ?? 0)}
          formatDetail={(row) => pluralize(row.rushing_attempts, "corrida", "corridas")}
        />
        <HighlightsTable
          title="Sacks"
          rows={highlights.sacks}
          teams={teamIndex}
          valueHeader="Sacks"
          formatValue={(row) => formatNumber(row.sacks)}
          formatDetail={(row) => pluralize(row.games, "jogo", "jogos")}
        />
      </div>
    </div>
  );
}
