import "server-only";

import createClient from "openapi-fetch";

import type { paths } from "@/lib/api/schema";

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
  if (data !== undefined) {
    return data;
  }
  const detail =
    error && typeof error === "object" && "detail" in error
      ? (error as { detail: unknown }).detail
      : error;
  throw new ApiError(response.status, detail);
}
