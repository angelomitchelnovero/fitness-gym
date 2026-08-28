import axios, { AxiosError, type AxiosInstance } from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 15_000,
});

const TOKEN_KEY = 'fg_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface ApiError {
  status: number;
  message: string;
}

export function toApiError(err: unknown): ApiError {
  if (err instanceof AxiosError) {
    const data = err.response?.data as { detail?: string | unknown[] } | undefined;
    let message = err.message;
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        const first = data.detail[0] as { msg?: unknown } | undefined;
        if (first && typeof first.msg === 'string') {
          message = first.msg;
        }
      }
    }
    return { status: err.response?.status ?? 0, message };
  }
  return { status: 0, message: err instanceof Error ? err.message : 'Unknown error' };
}
