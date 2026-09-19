import type { TeamRead } from "@/lib/api/types";

export type TeamIndex = Map<string, TeamRead>;

export function indexTeams(teams: TeamRead[]): TeamIndex {
  return new Map(teams.map((team) => [team.id, team]));
}

export function teamOf(teams: TeamIndex, teamId: string): TeamRead {
  const team = teams.get(teamId);
  if (!team) {
    throw new Error(`team ${teamId} not found`);
  }
  return team;
}
