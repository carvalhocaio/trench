const LOCALE = "pt-BR";

export const TIMEZONE = process.env.TRENCH_TIMEZONE ?? "America/Cuiaba";

const numberFormatter = new Intl.NumberFormat(LOCALE, {
  maximumFractionDigits: 1,
});

const percentFormatter = new Intl.NumberFormat(LOCALE, {
  style: "percent",
  maximumFractionDigits: 0,
});

const pointsFormatter = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const signedPointsFormatter = new Intl.NumberFormat(LOCALE, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
  signDisplay: "always",
});

const kickoffFormatter = new Intl.DateTimeFormat(LOCALE, {
  timeZone: TIMEZONE,
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

const dateTimeFormatter = new Intl.DateTimeFormat(LOCALE, {
  timeZone: TIMEZONE,
  dateStyle: "short",
  timeStyle: "short",
});

export function formatNumber(value: number): string {
  return numberFormatter.format(value);
}

export function formatPercent(fraction: number): string {
  return percentFormatter.format(fraction);
}

export function formatPoints(value: number): string {
  return pointsFormatter.format(value);
}

export function formatSignedPoints(value: number): string {
  return signedPointsFormatter.format(value);
}

export function formatKickoff(isoDate: string): string {
  return kickoffFormatter.format(new Date(isoDate));
}

export function formatDateTime(isoDate: string): string {
  return dateTimeFormatter.format(new Date(isoDate));
}

export function pluralize(count: number, singular: string, plural: string): string {
  return `${count} ${count === 1 ? singular : plural}`;
}
