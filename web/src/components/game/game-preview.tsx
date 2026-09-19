import { ApiError } from "@/lib/api/client";
import { getPreview } from "@/lib/api/queries";
import type { MatchupPreview } from "@/lib/api/types";

export function GamePreviewSkeleton() {
  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <div className="h-4 w-1/3 animate-pulse rounded bg-zinc-200" />
      <div className="mt-4 space-y-2">
        <div className="h-3 w-full animate-pulse rounded bg-zinc-100" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-zinc-100" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-zinc-100" />
      </div>
    </section>
  );
}

export async function GamePreview({ gameId }: { gameId: string }) {
  let preview: MatchupPreview | null = null;
  try {
    preview = (await getPreview(gameId)).preview;
  } catch (error) {
    if (!(error instanceof ApiError && (error.status === 503 || error.status === 409))) {
      throw error;
    }
  }

  if (!preview) {
    return (
      <section className="rounded-lg border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-400">Análise indisponível no momento.</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-zinc-900">{preview.headline}</h2>
      <p className="mt-2 text-sm text-zinc-700">{preview.summary}</p>
      {preview.key_factors.length > 0 && (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-zinc-600">
          {preview.key_factors.map((factor) => (
            <li key={factor}>{factor}</li>
          ))}
        </ul>
      )}
      {preview.players_to_watch && preview.players_to_watch.length > 0 && (
        <p className="mt-3 text-xs text-zinc-500">
          Jogadores para observar: {preview.players_to_watch.join(", ")}
        </p>
      )}
    </section>
  );
}
