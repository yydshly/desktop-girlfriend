# Live2D Desktop Smoke - 2026-07-02

Branch: `codex/live2d-model-mainline`

## Scope

Validate the real desktop launch path after the Live2D coordinator extraction:

- Main app startup
- Live2D bridge server lifecycle
- Live2D desktop child process launch
- Web runtime status return path
- Runtime status visibility in the main window
- Process cleanup observations

## Commands

```powershell
.\.venv\Scripts\python.exe -m app.main
```

For this smoke run, the app was launched with stdout/stderr redirected to:

```text
.tmp/smoke-app.out.log
.tmp/smoke-app.err.log
```

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Main app starts | Pass | Log: `Starting Desktop Girlfriend`, then `Application started successfully`. |
| Model catalog scans | Pass | Log: `packages=2 selected_model_id=sample/Hiyori`. |
| Bridge server starts | Pass | Log: `Live2D bridge server started url=ws://127.0.0.1:8879`. |
| Live2D desktop child process starts | Pass | Log: `Live2D desktop process started pid=45020`. |
| Web runtime connects back | Pass | Log: `live2d.runtime_ready`. |
| Model loads in Web runtime | Pass | Log: `live2d.model_loaded`. |
| Runtime activity returns | Pass | Log: repeated `live2d.motion_played`. |
| Runtime status reaches coordinator | Pass | Log: `Live2D runtime status updated type=...`. |
| Scale / opacity / visibility / model switch callbacks | Automated pass | Covered by `app/tests/test_live2d_desktop_coordinator.py` and `app/tests/test_desktop_presence_shell.py`. |
| Real GUI button clicks | Manual follow-up | Current tool session cannot reliably click the PySide6 desktop window. |
| Graceful app quit cleanup | Manual follow-up | Requires user-level window close/tray quit interaction. |
| Forced parent process kill cleanup | Risk observed | Hard-killing the main process left the Live2D child process running; this bypasses Qt `aboutToQuit`. |

## Notes

- The smoke run confirmed the important runtime chain: Python main app -> bridge server -> Live2D child process -> Web runtime -> Python runtime status.
- A hard process kill is not the same as a normal app quit. The child process remaining after `Stop-Process` is a Windows forced-termination risk, not proof that the normal coordinator shutdown path failed.
- Follow-up polish added clearer status reporting for bridge failures and desktop process health.
