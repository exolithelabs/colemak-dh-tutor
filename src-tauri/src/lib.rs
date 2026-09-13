use std::{net::TcpListener, sync::Mutex};

use serde::Serialize;
use tauri::{Manager, RunEvent, State};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};
use uuid::Uuid;

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendConnection {
    base_url: String,
    token: String,
}

struct BackendState {
    connection: BackendConnection,
    child: Mutex<Option<CommandChild>>,
}

impl BackendState {
    fn terminate(&self) {
        if let Some(child) = self.child.lock().expect("backend state poisoned").take() {
            let _ = child.kill();
        }
    }
}

#[tauri::command]
fn backend_connection(state: State<'_, BackendState>) -> BackendConnection {
    state.connection.clone()
}

#[tauri::command]
fn stop_application(app: tauri::AppHandle, state: State<'_, BackendState>) {
    state.terminate();
    app.exit(0);
}

#[tauri::command]
fn restart_application(app: tauri::AppHandle, state: State<'_, BackendState>) {
    state.terminate();
    app.restart();
}

pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let listener = TcpListener::bind("127.0.0.1:0")?;
            let port = listener.local_addr()?.port();
            drop(listener);

            let token = format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple());
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;

            let sidecar = app
                .shell()
                .sidecar("colemak-backend")?
                .args(vec![
                    "--port".to_string(),
                    port.to_string(),
                    "--data-dir".to_string(),
                    data_dir.to_string_lossy().into_owned(),
                ])
                .env("COLEMAK_SIDECAR_TOKEN", &token);
            let (mut events, child) = sidecar.spawn()?;

            tauri::async_runtime::spawn(async move {
                while let Some(event) = events.recv().await {
                    if matches!(event, CommandEvent::Error(_) | CommandEvent::Terminated(_)) {
                        break;
                    }
                }
            });

            app.manage(BackendState {
                connection: BackendConnection {
                    base_url: format!("http://127.0.0.1:{port}"),
                    token,
                },
                child: Mutex::new(Some(child)),
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend_connection,
            stop_application,
            restart_application
        ])
        .build(tauri::generate_context!())
        .expect("failed to build Colemak-DH Tutor");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            app_handle.state::<BackendState>().terminate();
        }
    });
}
