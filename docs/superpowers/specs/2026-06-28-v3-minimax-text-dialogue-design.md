# V3 MiniMax Text Dialogue Design

Date: 2026-06-28

## Purpose

V3 should deliver the first usable AI dialogue loop without expanding into the full long-term vision too early.

The first V3 slice is:

1. User enters text in the desktop UI.
2. The app moves into a thinking state.
3. Brain Layer builds a prompt through Prompt Registry.
4. A Chat Provider returns an assistant reply.
5. UI displays the reply.
6. The app returns to idle, or enters error state when the request fails.

This slice intentionally excludes TTS, ASR, Memory, Tool Router, Agent planning, and Avatar behavior.

## Chosen Approach

Use a contract-first text dialogue loop.

The implementation should define stable contracts before wiring the UI to MiniMax:

- A `ChatProvider` interface for dialogue generation.
- A MiniMax provider implementation behind that interface.
- A fake provider for deterministic tests and local UI checks.
- A minimal Prompt Registry that owns system/persona prompts.
- Event contracts for user input, assistant output, and failures.
- UI controls for text input and reply display.

This approach costs slightly more upfront than a UI-only prototype, but it protects the project boundaries already established in V1 and V2.

## Architecture

V3 keeps the existing layer responsibilities:

| Layer | V3 responsibility |
| --- | --- |
| UI Layer | Collect user text, publish user input events, render dialogue state and assistant replies. |
| Core Layer | Route events, manage state transitions, expose configuration. |
| Brain Layer | Own prompt assembly, provider interface, MiniMax provider, and dialogue orchestration. |
| Expression Layer | Out of scope for this slice; TTS starts after the text loop is stable. |

The UI must not call MiniMax directly. The UI talks through EventBus and/or a controller boundary. MiniMax access stays behind Brain Layer provider abstractions.

## Components

### Chat Provider

Define a small provider contract that accepts a text request and returns a text response.

The contract should avoid leaking MiniMax-specific request shapes into the rest of the app. MiniMax-specific fields belong in the MiniMax provider implementation or config.

Expected implementations:

- `FakeChatProvider`: deterministic local provider used by tests and safe demos.
- `MiniMaxChatProvider`: real network-backed provider used when credentials are configured.

### Prompt Registry

Prompt Registry is the only place where base prompts and persona prompts live.

The first version should stay minimal:

- Provide a default system prompt.
- Provide a method for building the messages/context needed by `ChatProvider`.
- Avoid long-term memory and external tools.

Prompt text must not be scattered through UI, controller, or provider code.

### Dialogue Controller

Add a Brain/Core-facing orchestration point for the dialogue loop.

Its job is to:

- Receive user text from the event/controller boundary.
- Ignore or reject empty text.
- Request `THINKING` state.
- Build the provider request via Prompt Registry.
- Call `ChatProvider`.
- Publish an assistant reply event.
- Return to `IDLE`.
- Publish a system error and enter `ERROR` when the provider fails.

The controller should be testable without a Qt event loop.

### UI

Extend the desktop window with a compact text dialogue surface:

- Text input.
- Send action.
- Conversation/reply display.
- Disabled send state while thinking.
- Error display using the existing error path where possible.

The UI should remain simple and functional. This is not the final companion experience.

## Data Flow

```text
User text
  -> UI Layer
  -> USER_TEXT_SUBMITTED event
  -> Dialogue Controller
  -> StateController requests THINKING
  -> Prompt Registry builds messages
  -> ChatProvider.generate()
  -> ASSISTANT_TEXT_RECEIVED event
  -> UI renders reply
  -> StateController requests IDLE
```

Failure flow:

```text
Provider/config/prompt failure
  -> Dialogue Controller catches known error
  -> SYSTEM_ERROR event
  -> StateController requests ERROR
  -> UI renders error state
```

## Event Contracts

Keep events serializable and explicit.

Add one new dialogue output event:

- `ASSISTANT_TEXT_RECEIVED`

Provider and prompt failures should use the existing `SYSTEM_ERROR` path in this slice. Do not add a separate assistant failure event unless implementation proves that `SYSTEM_ERROR` cannot represent the UI need cleanly.

Payloads should use dataclasses or small typed structures that convert cleanly to event payload dictionaries. Avoid passing raw exceptions, provider objects, or Qt objects through EventBus.

## Configuration

Extend app configuration with MiniMax settings:

- `MINIMAX_API_KEY`
- `MINIMAX_GROUP_ID`
- `MINIMAX_BASE_URL`
- Optional model name if required by the selected MiniMax endpoint

Missing credentials should not break tests or local fake-provider mode. Real MiniMax calls should fail with a clear configuration error before attempting a network request.

## Error Handling

Handle these cases explicitly:

- Empty or whitespace-only user input.
- Missing MiniMax credentials in real-provider mode.
- Provider timeout or network error.
- Provider returns malformed or empty content.

Errors should be visible to the UI and covered by unit tests. Unknown exceptions should not crash the Qt window during normal dialogue attempts.

## Testing

Add tests at the contract and controller level first:

- Prompt Registry returns stable default prompt content.
- Fake provider returns deterministic output.
- Dialogue controller publishes assistant reply on success.
- Dialogue controller moves state to thinking then idle on success.
- Dialogue controller publishes system error and error state on provider failure.
- UI-level test only where it adds confidence without becoming brittle.

Real MiniMax network tests should not be part of the default test suite. They can be added later as opt-in integration checks.

## Scope Boundaries

In scope:

- Text input and reply display.
- Prompt Registry minimum viable implementation.
- Chat Provider protocol.
- Fake provider.
- MiniMax provider skeleton and real call path when configured.
- Unit tests for the dialogue loop.

Out of scope:

- TTS playback.
- Streaming response UI.
- ASR or microphone input.
- Memory.
- Tool calling.
- Agent planning.
- Avatar animation.
- Multi-character/persona management.

## Quality Gates

Before the implementation is considered complete:

- `ruff check .` passes.
- `pytest -q` passes.
- `mypy app` is attempted; if blocked by the local Python environment, document the exact blocker.
- The V3 implementation obeys the architecture checklist in `docs/REVIEW_GUIDE.md`.
- No UI-to-MiniMax direct call exists.
- Prompt text is not scattered outside Prompt Registry.

## Open Decisions Already Resolved

- First V3 slice prioritizes text dialogue over TTS.
- Superpowers is used as workflow assistance, not as a runtime dependency.
- Project-specific custom skills are deferred until repeated local workflow patterns become stable.
- The implementation should proceed through a written plan before code changes.
