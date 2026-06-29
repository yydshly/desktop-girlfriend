# v0.2.0-alpha.1

## Summary

This alpha release upgrades the desktop girlfriend app from a release-candidate technical baseline into a more complete desktop companion experience.

## Included

- Companion presence header (Phase 2-A)
- Conversation experience polish (Phase 2-B)
- Desktop window visual polish (Phase 2-C)
- Desktop presence shell: always-on-top mode (Phase 2-D)
- Desktop presence shell: compact mode (Phase 2-D)
- Settings runtime controls (Phase 2-E)
- System tray hide / restore (Phase 2-F)
- Proactive companion UX polish (Phase 2-G)
- Avatar expression labels (Phase 2-H)
- Existing chat / TTS / ASR / memory / proactive runtime retained

## Not Included

- Installer
- Auto start on boot
- Live2D
- Complex animation
- Dynamic provider switching from UI
- Writing settings back to .env

## Safety

- No .env write
- No API key display
- No provider runtime changes
- No memory runtime changes
- No proactive runtime strategy changes

## Verification

- ruff
- mypy
- target tests
- UI probes
- full pytest before tag

## Git Tag Plan

```bash
git tag v0.2.0-alpha.1
git push origin v0.2.0-alpha.1
```
