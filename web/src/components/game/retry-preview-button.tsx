"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";

export function RetryPreviewButton() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      onClick={() => startTransition(() => router.refresh())}
      disabled={pending}
      className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
    >
      {pending ? "Tentando novamente…" : "Tentar novamente"}
    </button>
  );
}
