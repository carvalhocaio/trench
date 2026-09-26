import { ApiError } from "@/lib/api/client";
import { getPreview } from "@/lib/api/queries";
import type { MatchupPreview } from "@/lib/api/types";
import { RetryPreviewButton } from "@/components/game/retry-preview-button";

export async function GamePreview({ gameId }: { gameId: string }) {
  let preview: MatchupPreview | null = null;
  let retryable = false;
  try {
    preview = (await getPreview(gameId)).preview;
  } catch (error) {
    if (!(error instanceof ApiError && (error.status === 503 || error.status === 409))) {
      throw error;
    }
    retryable = error.status === 503;
  }

  if (!preview) {
    return (
      <section className="flex flex-col items-start gap-3 rounded-lg border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-400">
          {retryable
            ? "O Gemini não respondeu desta vez. Costuma ser momentâneo."
            : "Análise indisponível no momento."}
        </p>
        {retryable && <RetryPreviewButton />}
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
