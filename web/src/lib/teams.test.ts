import { describe, expect, it } from "vitest";

import { indexTeams, teamOf } from "@/lib/teams";
import type { TeamRead } from "@/lib/api/types";

const chiefs: TeamRead = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "Kansas City Chiefs",
  abbreviation: "KC",
  conference: "AFC",
  division: "WEST",
};

describe("indexTeams / teamOf", () => {
  it("indexes teams by id", () => {
    const teams = indexTeams([chiefs]);
    expect(teamOf(teams, chiefs.id)).toEqual(chiefs);
  });

  it("throws when the team does not exist", () => {
    const teams = indexTeams([chiefs]);
    expect(() => teamOf(teams, "missing-id")).toThrow(/missing-id/);
  });
});
