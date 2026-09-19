import { formatPercent } from "@/lib/format";

export function ProbabilityBar({
  topLabel,
  topProbability,
  bottomLabel,
  bottomProbability,
}: {
  topLabel: string;
  topProbability: number;
  bottomLabel: string;
  bottomProbability: number;
}) {
  const topIsFavorite = topProbability >= bottomProbability;

  return (
    <div
      role="img"
      aria-label={`${topLabel} com ${formatPercent(topProbability)} de chance de vitória, ${bottomLabel} com ${formatPercent(bottomProbability)} de chance de vitória`}
    >
      <div className="flex h-2 w-full overflow-hidden rounded-full">
        <div
          className={topIsFavorite ? "bg-nfl-navy" : "bg-zinc-300"}
          style={{ width: `${topProbability * 100}%` }}
        />
        <div
          className={topIsFavorite ? "bg-zinc-300" : "bg-nfl-navy"}
          style={{ width: `${bottomProbability * 100}%` }}
        />
      </div>
      <div className="mt-1 flex justify-between text-xs tabular-nums text-zinc-500">
        <span>
          {topLabel} {formatPercent(topProbability)}
        </span>
        <span>
          {bottomLabel} {formatPercent(bottomProbability)}
        </span>
      </div>
    </div>
  );
}
