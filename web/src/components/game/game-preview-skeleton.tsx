"use client";

import { useEffect, useState } from "react";

const SLOW_PREVIEW_MS = 10_000;

export function GamePreviewSkeleton() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_PREVIEW_MS);
    return () => clearTimeout(timer);
  }, []);

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4" aria-busy="true">
      <div className="h-4 w-1/3 animate-pulse rounded bg-zinc-200" />
      <div className="mt-4 space-y-2">
        <div className="h-3 w-full animate-pulse rounded bg-zinc-100" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-zinc-100" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-zinc-100" />
      </div>
      {slow && (
        <p className="mt-4 text-xs text-zinc-500" role="status">
          O Gemini está escrevendo a análise… isso pode levar até um minuto.
        </p>
      )}
    </section>
  );
}
