import "server-only";

import createClient from "openapi-fetch";

import type { paths } from "@/lib/api/schema";
import type { ValidationError } from "@/lib/api/types";
import type { FormState } from "@/lib/form-state";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : `request failed with status ${status}`);
    this.name = "ApiError";
  }
}

export const api = createClient<paths>({
  baseUrl: process.env.TRENCH_API_URL ?? "http://localhost:8000",
  cache: "no-store",
});

type ApiResponse<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

export function unwrap<T>({ data, error, response }: ApiResponse<T>): T {
  if (response.ok) {
    return data as T;
  }
  const detail =
    error && typeof error === "object" && "detail" in error
      ? (error as { detail: unknown }).detail
      : error;
  throw new ApiError(response.status, detail);
}

export function apiErrorToFormState(error: unknown): FormState {
  if (!(error instanceof ApiError)) {
    throw error;
  }
  if (Array.isArray(error.detail)) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of error.detail as ValidationError[]) {
      const field = issue.loc.at(-1);
      if (typeof field === "string") {
        fieldErrors[field] = issue.msg;
      }
    }
    return { fieldErrors, formError: null, success: false };
  }
  if (typeof error.detail === "string") {
    return { fieldErrors: {}, formError: error.detail, success: false };
  }
  throw error;
}
