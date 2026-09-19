import { describe, expect, it } from "vitest";

import { ApiError, apiErrorToFormState, translateErrorCode } from "@/lib/api/errors";

function formData(entries: Record<string, string>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(entries)) {
    data.append(key, value);
  }
  return data;
}

describe("translateErrorCode", () => {
  it("translates known codes to pt-BR messages", () => {
    expect(translateErrorCode("schedule_conflict", "raw")).toBe(
      "Um dos times já tem jogo nesta semana.",
    );
    expect(translateErrorCode("game_not_started", "raw")).toBe(
      "O jogo ainda não começou: placar e estatísticas ficam liberados após o kickoff.",
    );
    expect(translateErrorCode("not_found", "raw")).toBe("Registro não encontrado.");
    expect(translateErrorCode("conflict", "raw")).toBe(
      "Já existe um registro com esses dados.",
    );
  });

  it("falls back to the detail message for an unknown code", () => {
    expect(translateErrorCode("something_else", "raw detail")).toBe("raw detail");
    expect(translateErrorCode(undefined, "raw detail")).toBe("raw detail");
  });
});

describe("apiErrorToFormState", () => {
  it("echoes the submitted field values", () => {
    const error = new ApiError(409, "erro", "conflict");

    const state = apiErrorToFormState(error, formData({ season: "2026", week: "3" }));

    expect(state.values).toEqual({ season: "2026", week: "3" });
    expect(state.success).toBe(false);
  });

  it("drops keys that start with $ACTION", () => {
    const error = new ApiError(409, "erro", "conflict");

    const state = apiErrorToFormState(
      error,
      formData({ season: "2026", $ACTION_ID_abc: "xyz" }),
    );

    expect(state.values).toEqual({ season: "2026" });
  });

  it("translates a string-detail error using its code", () => {
    const error = new ApiError(409, "raw detail", "schedule_conflict");

    const state = apiErrorToFormState(error, formData({}));

    expect(state.formError).toBe("Um dos times já tem jogo nesta semana.");
  });

  it("falls back to the raw detail for an unknown code", () => {
    const error = new ApiError(422, "algo deu errado", "unknown_code");

    const state = apiErrorToFormState(error, formData({}));

    expect(state.formError).toBe("algo deu errado");
  });

  it("maps a list-shaped detail to field errors instead of a form error", () => {
    const error = new ApiError(
      422,
      [{ loc: ["body", "season"], msg: "Field required", type: "missing" }],
      undefined,
    );

    const state = apiErrorToFormState(error, formData({ week: "3" }));

    expect(state.fieldErrors).toEqual({ season: "Field required" });
    expect(state.formError).toBeNull();
    expect(state.values).toEqual({ week: "3" });
  });
});
