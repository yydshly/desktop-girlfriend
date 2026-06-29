# v0.2.0-alpha.2

## Summary

This hotfix alpha release stabilizes the Phase 2 desktop companion experience after real GUI verification.

## Fixed

- Fixed header version display using stale hardcoded `0.1.0-rc.3` values.
- Unified companion version display with the `VERSION` metadata source.
- Fixed settings panel content visibility in real GUI usage.
- Fixed status panel and settings panel mutual exclusion.
- Prevented status/settings panels from appearing together and compressing the companion header.
- Compact mode now closes expanded status/settings panels.

## Included from v0.2.0-alpha.1

- Companion presence header
- Conversation experience polish
- Desktop window polish
- Always-on-top mode
- Compact mode
- Read-only settings panel
- System tray hide / restore
- Proactive companion UX
- Avatar expression labels

## Not Included

- Installer
- Auto start on boot
- Live2D
- Complex animation
- Dynamic provider switching from UI
- Writing settings back to `.env`

## Safety

- No `.env` write
- No API key display
- No provider runtime changes
- No memory runtime changes
- No proactive runtime strategy changes

## Verification

- Real GUI verification passed
- Target tests passed
- UI probes passed
- ruff passed
- mypy passed

---

## v0.2.0-alpha.2 Build & Tag Commands

```powershell
git checkout main
git pull origin main
git checkout -b chore/v020-alpha2-hotfix-release
# (update VERSION, app/core/version.py, tests, probes)
git add VERSION app scripts
git commit -m "chore: prepare v0.2.0-alpha.2"
git push origin chore/v020-alpha2-hotfix-release
git checkout main
git pull origin main
git merge --no-ff chore/v020-alpha2-hotfix-release -m "chore: prepare v0.2.0-alpha.2"
git push origin main
git tag v0.2.0-alpha.2
git push origin v0.2.0-alpha.2
```

## Verification Commands

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy app
.venv\Scripts\python.exe -m pytest app/tests/test_version_metadata.py app/tests/test_settings_runtime_controls.py app/tests/test_product_status_button.py app/tests/test_companion_presence.py -q
.venv\Scripts\python.exe scripts\probe_version_metadata.py
.venv\Scripts\python.exe scripts\probe_v020_alpha_readiness.py
.venv\Scripts\python.exe scripts\probe_settings_runtime_controls.py
.venv\Scripts\python.exe scripts\probe_product_status_button.py
.\scripts\run_desktop.ps1
```
