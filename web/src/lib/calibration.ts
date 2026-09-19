export const SMALL_SAMPLE_THRESHOLD = 100;
export const GOOD_BRIER_THRESHOLD = 0.25;

export function isSmallSample(forecasts: number): boolean {
  return forecasts < SMALL_SAMPLE_THRESHOLD;
}

export function isGoodBrier(brier: number): boolean {
  return brier < GOOD_BRIER_THRESHOLD;
}

export function formatReliabilityRange(lower: number, upper: number): string {
  return `${Math.round(lower * 100)}–${Math.round(upper * 100)}%`;
}

export function parseFloatParam(value: string | string[] | undefined): number | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw === undefined || raw.trim() === "") {
    return undefined;
  }
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : undefined;
}
