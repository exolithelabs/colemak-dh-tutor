export interface BackendConnection {
  baseUrl: string;
  token: string;
}

// Inject the transport for deterministic tests without a running desktop shell.
export function createApiFetch(
  getConnection: () => Promise<BackendConnection>,
  fetcher: typeof fetch = fetch,
  pause = (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),
) {
  let ready: Promise<BackendConnection> | undefined;

  async function request(backend: BackendConnection, path: string, init: RequestInit = {}, timeout = 5000) {
    const controller = new AbortController();
    const cancel = () => controller.abort();
    init.signal?.addEventListener('abort', cancel, { once: true });
    if (init.signal?.aborted) cancel();
    const timer = setTimeout(cancel, timeout);
    const headers = new Headers(init.headers);
    headers.set('X-App-Token', backend.token);
    try {
      return await fetcher(`${backend.baseUrl}${path}`, {
        ...init, headers, signal: controller.signal, redirect: 'error', cache: 'no-store',
      });
    } finally {
      clearTimeout(timer);
      init.signal?.removeEventListener('abort', cancel);
    }
  }

  async function connect() {
    const backend = await getConnection();
    // Only readiness checks are retried. Repeating a POST after a lost response
    // could create a duplicate progress entry.
    for (let attempt = 0; attempt < 20; attempt += 1) {
      try {
        const response = await request(backend, '/api/health', {}, 1000);
        if (response.ok) return backend;
        if (response.status === 401 || response.status === 403) {
          throw new Error('Unable to authenticate with the local service. Restart the app.');
        }
      } catch (error) {
        if (error instanceof Error && error.message.includes('authenticate')) throw error;
      }
      await pause(250);
    }
    throw new Error('The local service could not start. Check free disk space, then retry or restart the app.');
  }

  return async (path: string, init: RequestInit = {}): Promise<Response> => {
    if (!path.startsWith('/api/')) throw new Error('Invalid API path');
    ready ??= connect().catch(error => { ready = undefined; throw error; });
    const backend = await ready;
    try {
      const response = await request(backend, path, init);
      if (!response.ok) {
        throw new Error(`The request failed (${response.status}). Please try again.`);
      }
      return response;
    } catch (error) {
      ready = undefined;
      throw error;
    }
  };
}
