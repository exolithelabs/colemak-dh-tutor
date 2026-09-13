import { invoke } from '@tauri-apps/api/core';

interface BackendConnection {
  baseUrl: string;
  token: string;
}

let connectionPromise: Promise<BackendConnection> | undefined;

const connection = () => {
  connectionPromise ??= invoke<BackendConnection>('backend_connection');
  return connectionPromise;
};

const pause = (milliseconds: number) => new Promise(resolve => setTimeout(resolve, milliseconds));

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const backend = await connection();
  const headers = new Headers(init.headers);
  headers.set('X-App-Token', backend.token);

  let lastError: unknown;
  for (let attempt = 0; attempt < 30; attempt += 1) {
    try {
      const response = await fetch(`${backend.baseUrl}${path}`, { ...init, headers });
      if (!response.ok) {
        throw new Error(`Backend request failed with status ${response.status}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      if (!(error instanceof TypeError) || attempt === 29) throw error;
      await pause(100);
    }
  }
  throw lastError instanceof Error ? lastError : new Error('The local backend did not start');
}

export const stopApplication = () => invoke<void>('stop_application');
export const restartApplication = () => invoke<void>('restart_application');
