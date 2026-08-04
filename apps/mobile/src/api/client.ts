import { ErrorResponseSchema } from "./schemas";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiRequestError(0, "NETWORK_ERROR", "Could not reach the CalmPath server.");
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const parsedError = ErrorResponseSchema.safeParse(body);
    if (parsedError.success) {
      throw new ApiRequestError(response.status, parsedError.data.error.code, parsedError.data.error.message);
    }
    throw new ApiRequestError(response.status, "UNKNOWN_ERROR", "Something went wrong. Please try again.");
  }

  return body as T;
}

export function postRouteCompare(payload: unknown): Promise<unknown> {
  return request<unknown>("/routes/compare", { method: "POST", body: JSON.stringify(payload) });
}

export function getRouteDetail(routeId: string): Promise<unknown> {
  return request<unknown>(`/routes/${encodeURIComponent(routeId)}`);
}

export function getRefuges(routeId: string): Promise<unknown> {
  return request<unknown>(`/refuges?route_id=${encodeURIComponent(routeId)}`);
}

export function getRefugeDetail(placeId: string, routeId: string): Promise<unknown> {
  return request<unknown>(`/refuges/${encodeURIComponent(placeId)}?route_id=${encodeURIComponent(routeId)}`);
}

export function searchPlaces(query: string): Promise<unknown> {
  return request<unknown>(`/places/search?query=${encodeURIComponent(query)}`);
}

export function resolvePlace(placeId: string): Promise<unknown> {
  return request<unknown>(`/places/resolve?place_id=${encodeURIComponent(placeId)}`);
}
