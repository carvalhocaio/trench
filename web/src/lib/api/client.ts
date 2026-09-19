import "server-only";

import createClient from "openapi-fetch";

import { ApiError } from "@/lib/api/errors";
import type { paths } from "@/lib/api/schema";

export { ApiError, apiErrorToFormState } from "@/lib/api/errors";

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
  const code =
    error && typeof error === "object" && "code" in error
      ? (error as { code: unknown }).code
      : undefined;
  throw new ApiError(response.status, detail, typeof code === "string" ? code : undefined);
}
