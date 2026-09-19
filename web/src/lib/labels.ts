import type { AbsenceStatus, Position } from "@/lib/api/types";

export const ABSENCE_STATUS_LABELS: Record<AbsenceStatus, string> = {
  OUT: "Fora",
  DOUBTFUL: "Dúvida",
  QUESTIONABLE: "Questionável",
};

export const POSITION_LABELS: Record<Position, string> = {
  QB: "QB — Quarterback",
  RB: "RB — Corredor",
  WR: "WR — Recebedor aberto",
  TE: "TE — Ala",
  OL: "OL — Linha ofensiva",
  DL: "DL — Linha defensiva",
  EDGE: "EDGE — Ponta de ataque",
  LB: "LB — Linebacker",
  CB: "CB — Cornerback",
  S: "S — Safety",
  K: "K — Chutador",
  P: "P — Punter",
};

export const POSITION_OPTIONS: { value: Position; label: string }[] = (
  Object.entries(POSITION_LABELS) as [Position, string][]
).map(([value, label]) => ({ value, label }));
