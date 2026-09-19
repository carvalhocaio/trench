import { describe, expect, it } from "vitest";

import {
  formatReliabilityRange,
  isGoodBrier,
  isSmallSample,
  parseFloatParam,
} from "@/lib/calibration";

describe("isSmallSample", () => {
  it("flags samples below the threshold", () => {
    expect(isSmallSample(99)).toBe(true);
    expect(isSmallSample(100)).toBe(false);
    expect(isSmallSample(150)).toBe(false);
  });
});

describe("isGoodBrier", () => {
  it("flags scores better than guessing 50%", () => {
    expect(isGoodBrier(0.2)).toBe(true);
    expect(isGoodBrier(0.25)).toBe(false);
    expect(isGoodBrier(0.3)).toBe(false);
  });
});

describe("formatReliabilityRange", () => {
  it("renders a percentage range", () => {
    expect(formatReliabilityRange(0.6, 0.7)).toBe("60–70%");
    expect(formatReliabilityRange(0.9, 1.0)).toBe("90–100%");
  });
});

describe("parseFloatParam", () => {
  it("parses a valid decimal string", () => {
    expect(parseFloatParam("1.7")).toBe(1.7);
  });

  it("takes the first value from a repeated query param", () => {
    expect(parseFloatParam(["3.5", "4"])).toBe(3.5);
  });

  it("returns undefined for missing, empty or non-numeric values", () => {
    expect(parseFloatParam(undefined)).toBeUndefined();
    expect(parseFloatParam("")).toBeUndefined();
    expect(parseFloatParam("abc")).toBeUndefined();
  });
});
