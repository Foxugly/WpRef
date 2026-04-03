import {environment} from '../../../environments/environment';

type RuntimeApiWindow = typeof globalThis & {
  __WPREF_API_BASE_URL?: string;
};

function resolveLocalDevApiBaseUrl(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const {hostname, protocol} = window.location;
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return null;
  }

  const apiProtocol = protocol === 'https:' ? 'https:' : 'http:';
  return `${apiProtocol}//${hostname}:8000`;
}

export function resolveApiBaseUrl(): string {
  return (
    (globalThis as RuntimeApiWindow).__WPREF_API_BASE_URL
    ?? resolveLocalDevApiBaseUrl()
    ?? environment.apiBaseUrl
  );
}

export function isApiUrl(url: string): boolean {
  const base = resolveApiBaseUrl().replace(/\/+$/, '');
  const cleaned = url.replace(/\/+$/, '');

  return cleaned.startsWith(base) || cleaned.startsWith('/api/');
}
