import type { Metadata } from "next";

import { listTeams } from "@/lib/api/queries";
import { currentSeason } from "@/lib/season";
import { ScheduleGameForm } from "@/components/admin/schedule-game-form";

// No searchParams or dynamic segment on this route, so Next would otherwise
// try to prerender it at build time and fail fetching the team list.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Agendar jogo",
};

export default async function NewGamePage() {
  const teams = await listTeams();
  const sortedTeams = [...teams].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-lg font-semibold text-zinc-900">Agendar jogo</h1>
      <ScheduleGameForm teams={sortedTeams} defaultSeason={currentSeason()} />
    </div>
  );
}
