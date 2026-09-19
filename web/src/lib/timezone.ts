function offsetFor(timeZone: string, year: number, month: number, day: number, hour: number, minute: number): string {
  const proxyInstant = new Date(Date.UTC(year, month - 1, day, hour, minute));
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    timeZoneName: "longOffset",
  }).formatToParts(proxyInstant);
  const raw = parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT+00:00";
  const match = /GMT([+-]\d{2}:\d{2})/.exec(raw);
  return match ? match[1] : "+00:00";
}

export function toZonedOffsetISOString(localValue: string, timeZone: string): string {
  const [datePart, timePart] = localValue.split("T");
  const [year, month, day] = datePart.split("-").map(Number);
  const [hour, minute] = timePart.split(":").map(Number);
  const offset = offsetFor(timeZone, year, month, day, hour, minute);
  return `${datePart}T${timePart}:00${offset}`;
}
