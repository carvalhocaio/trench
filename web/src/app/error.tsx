"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-lg border border-zinc-200 bg-white p-8 text-center">
      <h1 className="text-lg font-semibold text-nfl-red">
        Algo deu errado
      </h1>
      <p className="text-sm text-zinc-600">{error.message}</p>
      <button
        type="button"
        onClick={reset}
        className="rounded-md bg-nfl-navy px-4 py-2 text-sm font-medium text-white hover:opacity-90"
      >
        Tentar novamente
      </button>
    </div>
  );
}
