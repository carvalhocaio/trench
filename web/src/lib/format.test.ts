import { describe, expect, it } from "vitest";

import {
  formatKickoff,
  formatNumber,
  formatPercent,
  formatPoints,
  formatSignedPoints,
  pluralize,
} from "@/lib/format";

describe("formatNumber", () => {
  it("uses a comma as the decimal separator", () => {
    expect(formatNumber(24.5)).toBe("24,5");
  });
});

describe("formatPercent", () => {
  it("formats a fraction without decimals", () => {
    expect(formatPercent(0.624)).toBe("62%");
  });
});

describe("formatPoints", () => {
  it("always shows exactly one decimal place", () => {
    expect(formatPoints(23)).toBe("23,0");
    expect(formatPoints(23.456)).toBe("23,5");
  });
});

describe("formatSignedPoints", () => {
  it("shows a leading sign for positive, negative and zero values", () => {
    expect(formatSignedPoints(2.3)).toBe("+2,3");
    expect(formatSignedPoints(-2.3)).toBe("-2,3");
    expect(formatSignedPoints(0)).toBe("+0,0");
  });
});

describe("formatKickoff", () => {
  it("renders the date and time in the configured timezone", () => {
    expect(formatKickoff("2026-09-14T20:25:00Z")).toBe("14/09, 16:25");
  });
});

describe("pluralize", () => {
  it("uses the singular form for one", () => {
    expect(pluralize(1, "jogo", "jogos")).toBe("1 jogo");
  });

  it("uses the plural form otherwise", () => {
    expect(pluralize(0, "jogo", "jogos")).toBe("0 jogos");
    expect(pluralize(2, "jogo", "jogos")).toBe("2 jogos");
  });
});
