import type { ApiErrorBody } from '@/lib/types/api';

const DEFAULT_API_URL = 'http://localhost:8000';
type AccessTokenProvider = (forceRefresh?: boolean) => Promise<string | null>;

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiClient {
  request<T>(path: string, init?: RequestInit): Promise<T>;
  requestRaw(path: string, init?: RequestInit): Promise<Response>;
}

interface CreateApiClientOptions {
  baseUrl?: string;
  getAccessToken: AccessTokenProvider;
}

interface CreatePublicApiClientOptions {
  baseUrl?: string;
}

export function createApiClient({
  baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL,
  getAccessToken,
}: CreateApiClientOptions): ApiClient {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, '');

  async function requestRaw(path: string, init: RequestInit = {}): Promise<Response> {
    const accessToken = await getAccessToken();
    if (!accessToken) {
      throw new ApiError('A signed-in session is required.', 401, 'SESSION_REQUIRED');
    }

    const headers = new Headers(init.headers);
    headers.set('Authorization', `Bearer ${accessToken}`);

    if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const url = `${normalizedBaseUrl}${normalizePath(path)}`;
    let response = await fetch(url, {
      ...init,
      headers,
    });
    if (response.status === 401) {
      const refreshedToken = await getAccessToken(true);
      if (refreshedToken) {
        headers.set('Authorization', `Bearer ${refreshedToken}`);
        response = await fetch(url, { ...init, headers });
      }
    }
    return response;
  }

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await requestRaw(path, init);
    if (!response.ok) {
      throw await apiErrorFromResponse(response);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  }

  return { request, requestRaw };
}

export function createPublicApiClient({
  baseUrl = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL,
}: CreatePublicApiClientOptions = {}): ApiClient {
  const normalizedBaseUrl = baseUrl.replace(/\/$/, '');

  async function requestRaw(path: string, init: RequestInit = {}): Promise<Response> {
    const headers = new Headers(init.headers);
    if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }
    return fetch(`${normalizedBaseUrl}${normalizePath(path)}`, { ...init, headers });
  }

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await requestRaw(path, init);
    if (!response.ok) throw await apiErrorFromResponse(response);
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }

  return { request, requestRaw };
}

function normalizePath(path: string): string {
  return path.startsWith('/') ? path : `/${path}`;
}

export async function apiErrorFromResponse(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as Partial<ApiErrorBody>;
    if (body.error?.code && body.error.message) {
      return new ApiError(
        body.error.message,
        response.status,
        body.error.code,
        body.error.details,
      );
    }
  } catch {
    // Upstream HTML and empty bodies are normalized below.
  }

  return new ApiError(
    `API request failed with status ${response.status}.`,
    response.status,
    'API_REQUEST_FAILED',
  );
}
