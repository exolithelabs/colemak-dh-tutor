import { invoke } from '@tauri-apps/api/core';
import { createApiFetch, type BackendConnection } from './transport';

export const apiFetch = createApiFetch(() => invoke<BackendConnection>('backend_connection'));

export const stopApplication = () => invoke<void>('stop_application');
export const restartApplication = () => invoke<void>('restart_application');
