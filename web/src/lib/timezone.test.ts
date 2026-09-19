import { describe, expect, it } from "vitest";

import { toZonedOffsetISOString } from "@/lib/timezone";

describe("toZonedOffsetISOString", () => {
  it("uses a fixed offset for a timezone without daylight saving", () => {
    expect(toZonedOffsetISOString("2026-09-06T17:00", "America/Cuiaba")).toBe(
      "2026-09-06T17:00:00-04:00",
    );
  });

  it("uses standard time offset in winter for a DST-observing timezone", () => {
    expect(toZonedOffsetISOString("2026-01-15T10:00", "America/New_York")).toBe(
      "2026-01-15T10:00:00-05:00",
    );
  });

  it("uses daylight saving offset in summer for a DST-observing timezone", () => {
    expect(toZonedOffsetISOString("2026-07-15T10:00", "America/New_York")).toBe(
      "2026-07-15T10:00:00-04:00",
    );
  });

  it("preserves the wall-clock date and time regardless of offset", () => {
    const result = toZonedOffsetISOString("2026-12-31T23:45", "America/Cuiaba");
    expect(result.startsWith("2026-12-31T23:45:00")).toBe(true);
  });
});
