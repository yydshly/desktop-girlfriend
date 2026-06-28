---
name: desktop-girlfriend-guard
description: Project guard for the desktop-girlfriend repository. Use when Codex works in this repo on architecture, roadmap gates, Python/PySide6 code, MiniMax provider preparation, prompt registry work, tests, docs consistency, or any change that may cross UI/Core/Brain/Expression/Perception/Memory/Tool boundaries.
---

# Desktop Girlfriend Guard

Use this skill as the first project-specific guardrail for desktop-girlfriend work.

## Current Stage

- Treat the project as **V2 frozen / pre-V3 gate**.
- V1 and V2 may receive bugfixes, contract stabilization, tests, and docs alignment.
- Do not implement ASR, gestures, LivePortrait, Agent tools, long-term memory, or V4+ capabilities.
- Start MiniMax/TTS work only after the V3 Module Development Gate is satisfied.

## Before Editing

1. Identify the target layer:
   - `app/ui`: PySide6 window and ViewModel only.
   - `app/core`: EventBus, StateMachine, config, logging, lifecycle coordination.
   - `app/contracts`: event names, payloads, states, cross-module data contracts.
   - `app/brain`: LLM providers, prompt registry, agent decision logic.
   - `app/expression`: TTS, avatar, visual/audio expression.
   - `app/perception`: ASR, microphone, camera, gestures.
   - `app/memory`: memory and personalization.
   - `app/tools`: tool routing, permission checks, audit logs.
2. Check whether the requested work is allowed in the current roadmap stage.
3. Keep changes narrowly scoped and avoid bundling unrelated docs, code, and environment work.
4. If using external or bundled skills such as Superpowers, use them as advisory help. Do not let third-party skills read secrets, access networks, commit code, or change global config without explicit approval.

## Architecture Rules

- UI must not call MiniMax APIs, local tools, or external services directly.
- State changes must go through `StateMachine` / `StateController`.
- Cross-layer business notifications should use `EventBus`.
- Event payloads crossing module boundaries should be stable and serializable.
- External services must be wrapped behind provider interfaces.
- Prompts must live in a prompt registry or prompt asset area, not scattered through business code.
- Tool execution must eventually go through Tool Router with permissions and audit logging.

## V3 Gate Checklist

Before implementing MiniMax text dialogue or TTS, verify:

- `README.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/REVIEW_GUIDE.md`, `docs/MINIMAX_EXECUTION.md`, and `docs/SKILLS.md` agree on the current stage.
- Python is `>=3.11`.
- Tests and lint can run in a healthy environment.
- Provider interface boundaries are defined before concrete MiniMax implementation.
- API keys are read from environment/config only and are never committed.
- Prompt registry baseline exists before adding production prompts.
- Usage, privacy, and error handling are explicitly considered.

## Quality Commands

Prefer these commands after code changes:

```bash
python -m ruff check .
python -m mypy app
python -m pytest -q
```

If the local virtual environment is broken, report that clearly and run the subset that is available.

## Commit Hygiene

- Keep one conceptual change per commit.
- Commit docs-gate work separately from feature implementation.
- Commit provider contracts separately from concrete API integration.
- Do not include `.env`, local secrets, generated caches, or virtual environments.

## Response Checklist

When finishing work, report:

- Files changed.
- Tests or checks run.
- Known environment limits.
- Whether the change is V1/V2 bugfix, V3 gate work, or V3 feature work.
