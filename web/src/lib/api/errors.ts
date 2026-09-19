import type { ErrorCode, ValidationError } from "@/lib/api/types";
import type { FormState } from "@/lib/form-state";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: unknown,
    public readonly code: string | undefined,
  ) {
    super(typeof detail === "string" ? detail : `request failed with status ${status}`);
    this.name = "ApiError";
  }
}

const ERROR_MESSAGES: Record<ErrorCode, string> = {
  validation_error: "Dados inválidos para esta operação.",
  team_not_in_game: "Esse time não participa deste jogo.",
  not_found: "Registro não encontrado.",
  schedule_conflict: "Um dos times já tem jogo nesta semana.",
  insufficient_data: "Ainda não há dados suficientes para esta operação.",
  preview_unavailable: "Análise indisponível no momento.",
  game_not_started:
    "O jogo ainda não começou: placar e estatísticas ficam liberados após o kickoff.",
  conflict: "Já existe um registro com esses dados.",
};

export function translateErrorCode(code: string | undefined, detail: string): string {
  if (code !== undefined && code in ERROR_MESSAGES) {
    return ERROR_MESSAGES[code as ErrorCode];
  }
  return detail;
}

export function apiErrorToFormState(error: unknown, formData: FormData): FormState {
  if (!(error instanceof ApiError)) {
    throw error;
  }
  const values = valuesFromFormData(formData);
  if (Array.isArray(error.detail)) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of error.detail as ValidationError[]) {
      const field = issue.loc.at(-1);
      if (typeof field === "string") {
        fieldErrors[field] = issue.msg;
      }
    }
    return { fieldErrors, formError: null, success: false, values };
  }
  if (typeof error.detail === "string") {
    return {
      fieldErrors: {},
      formError: translateErrorCode(error.code, error.detail),
      success: false,
      values,
    };
  }
  throw error;
}

function valuesFromFormData(formData: FormData): Record<string, string> {
  const values: Record<string, string> = {};
  for (const [key, value] of formData.entries()) {
    if (key.startsWith("$ACTION") || typeof value !== "string") {
      continue;
    }
    values[key] = value;
  }
  return values;
}
