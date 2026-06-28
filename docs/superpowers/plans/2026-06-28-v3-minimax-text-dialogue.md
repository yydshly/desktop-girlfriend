# V3 MiniMax Text Dialogue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable V3 text dialogue loop: user text input, Prompt Registry assembly, Chat Provider response, UI reply rendering, and state/error transitions.

**Architecture:** Keep V3 aligned with the existing V1/V2 layering. UI publishes user input and renders state/replies; Core routes events and owns state transitions; Brain owns prompt assembly, chat provider contracts, MiniMax integration, and dialogue orchestration. TTS, ASR, Memory, Tool Router, Agent planning, and Avatar behavior remain outside this implementation.

**Tech Stack:** Python 3.11+, PySide6, python-dotenv, pytest, ruff, mypy.

---

## Source Spec

- `docs/superpowers/specs/2026-06-28-v3-minimax-text-dialogue-design.md`

## File Structure

Create:

- `app/brain/dialogue_controller.py`: subscribes to user text events, coordinates state transitions, prompt registry, provider call, assistant reply event, and error path.
- `app/brain/providers/chat.py`: provider-neutral request/response dataclasses, provider protocol, provider error classes, and deterministic fake provider.
- `app/brain/providers/minimax.py`: real MiniMax provider implementation using standard-library HTTP calls.
- `app/brain/prompts/registry.py`: minimal Prompt Registry for default system prompt and provider request assembly.
- `app/tests/test_chat_provider.py`: fake provider and provider contract tests.
- `app/tests/test_prompt_registry.py`: Prompt Registry tests.
- `app/tests/test_dialogue_controller.py`: dialogue orchestration tests.
- `app/tests/test_minimax_provider.py`: config validation and response parsing tests for MiniMax provider without live network calls.

Modify:

- `app/contracts/events.py`: add `ASSISTANT_TEXT_RECEIVED`.
- `app/contracts/payloads.py`: add serializable payload dataclasses for user text, assistant text, and system errors if needed.
- `app/core/config.py`: add MiniMax configuration values and provider selection.
- `app/ui/view_model.py`: track assistant replies and error text.
- `app/ui/window.py`: add text input, send button, reply display, and send-state behavior.
- `app/main.py`: wire DialogueController, Prompt Registry, and provider selection into app startup.
- `.env.example`: ensure MiniMax fields and provider mode are documented.
- `docs/ROADMAP.md`: mark V3 text loop as the active first slice only after implementation passes local checks.

Do not modify:

- TTS, ASR, Memory, Tool Router, or Avatar modules.
- Existing V1/V2 behavior except where needed to connect text dialogue events.

---

## Task 1: Event And Payload Contracts

**Files:**
- Modify: `app/contracts/events.py`
- Modify: `app/contracts/payloads.py`
- Test: `app/tests/test_contracts.py`

- [ ] **Step 1: Add failing tests for assistant event and payload serialization**

Add these imports and tests to `app/tests/test_contracts.py`:

```python
from app.contracts.events import ASSISTANT_TEXT_RECEIVED
from app.contracts.payloads import AssistantTextReceivedPayload, UserTextSubmittedPayload


def test_assistant_text_received_event_constant() -> None:
    assert ASSISTANT_TEXT_RECEIVED == "assistant.text_received"


def test_user_text_submitted_payload_to_event_payload() -> None:
    payload = UserTextSubmittedPayload(text="hello")

    assert payload.to_event_payload() == {"text": "hello"}


def test_assistant_text_received_payload_to_event_payload() -> None:
    payload = AssistantTextReceivedPayload(text="hi there")

    assert payload.to_event_payload() == {"text": "hi there"}
```

- [ ] **Step 2: Run contract tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_contracts.py -q
```

Expected: FAIL with import errors or missing names for `ASSISTANT_TEXT_RECEIVED`, `UserTextSubmittedPayload`, and `AssistantTextReceivedPayload`.

- [ ] **Step 3: Add the event constant**

In `app/contracts/events.py`, add:

```python
ASSISTANT_TEXT_RECEIVED = "assistant.text_received"
```

The event constants block should contain:

```python
USER_TEXT_SUBMITTED = "user.text_submitted"
ASSISTANT_TEXT_RECEIVED = "assistant.text_received"
STATE_CHANGE_REQUESTED = "state.change_requested"
STATE_CHANGED = "state.changed"
SYSTEM_ERROR = "system.error"
```

- [ ] **Step 4: Add serializable payload dataclasses**

In `app/contracts/payloads.py`, add:

```python
@dataclass
class UserTextSubmittedPayload:
    """Payload for user text submission events."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}


@dataclass
class AssistantTextReceivedPayload:
    """Payload for assistant text response events."""

    text: str

    def to_event_payload(self) -> Payload:
        """Convert the payload to an event-safe dictionary."""
        return {"text": self.text}
```

- [ ] **Step 5: Run contract tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_contracts.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/contracts/events.py app/contracts/payloads.py app/tests/test_contracts.py
git commit -m "feat: add dialogue event contracts"
```

---

## Task 2: Prompt Registry

**Files:**
- Create: `app/brain/prompts/registry.py`
- Modify: `app/brain/prompts/__init__.py`
- Test: `app/tests/test_prompt_registry.py`

- [ ] **Step 1: Write failing Prompt Registry tests**

Create `app/tests/test_prompt_registry.py`:

```python
"""Tests for Prompt Registry."""

from app.brain.prompts.registry import PromptMessage, PromptRegistry


def test_default_prompt_registry_has_system_prompt() -> None:
    registry = PromptRegistry()

    assert registry.default_system_prompt
    assert "desktop" in registry.default_system_prompt.lower()


def test_build_chat_messages_includes_system_and_user_text() -> None:
    registry = PromptRegistry(default_system_prompt="You are a concise companion.")

    messages = registry.build_chat_messages("Hello")

    assert messages == [
        PromptMessage(role="system", content="You are a concise companion."),
        PromptMessage(role="user", content="Hello"),
    ]


def test_build_chat_messages_trims_user_text() -> None:
    registry = PromptRegistry(default_system_prompt="system")

    messages = registry.build_chat_messages("  Hello  ")

    assert messages[-1] == PromptMessage(role="user", content="Hello")
```

- [ ] **Step 2: Run Prompt Registry tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_prompt_registry.py -q
```

Expected: FAIL because `app.brain.prompts.registry` does not exist.

- [ ] **Step 3: Implement Prompt Registry**

Create `app/brain/prompts/registry.py`:

```python
"""Prompt registry for dialogue prompts."""

from dataclasses import dataclass


DEFAULT_SYSTEM_PROMPT = (
    "You are a warm, concise desktop AI companion. "
    "Respond naturally and helpfully in the user's language."
)


@dataclass(frozen=True)
class PromptMessage:
    """Provider-neutral prompt message."""

    role: str
    content: str


class PromptRegistry:
    """Central registry for prompt text and chat message assembly."""

    def __init__(self, default_system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> None:
        self.default_system_prompt = default_system_prompt

    def build_chat_messages(self, user_text: str) -> list[PromptMessage]:
        """Build provider-neutral chat messages for a user utterance."""
        return [
            PromptMessage(role="system", content=self.default_system_prompt),
            PromptMessage(role="user", content=user_text.strip()),
        ]
```

- [ ] **Step 4: Export Prompt Registry names**

Modify `app/brain/prompts/__init__.py`:

```python
"""Prompt registry exports."""

from app.brain.prompts.registry import DEFAULT_SYSTEM_PROMPT, PromptMessage, PromptRegistry

__all__ = ["DEFAULT_SYSTEM_PROMPT", "PromptMessage", "PromptRegistry"]
```

- [ ] **Step 5: Run Prompt Registry tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_prompt_registry.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/brain/prompts/__init__.py app/brain/prompts/registry.py app/tests/test_prompt_registry.py
git commit -m "feat: add prompt registry"
```

---

## Task 3: Chat Provider Contract And Fake Provider

**Files:**
- Create: `app/brain/providers/chat.py`
- Modify: `app/brain/providers/__init__.py`
- Test: `app/tests/test_chat_provider.py`

- [ ] **Step 1: Write failing Chat Provider tests**

Create `app/tests/test_chat_provider.py`:

```python
"""Tests for chat provider contracts."""

import pytest

from app.brain.prompts.registry import PromptMessage
from app.brain.providers.chat import (
    ChatRequest,
    ChatResponse,
    FakeChatProvider,
    ProviderResponseError,
)


def test_fake_chat_provider_returns_deterministic_response() -> None:
    provider = FakeChatProvider(response_text="fake reply")
    request = ChatRequest(messages=[PromptMessage(role="user", content="hello")])

    response = provider.generate(request)

    assert response == ChatResponse(text="fake reply")


def test_fake_chat_provider_can_echo_last_user_message() -> None:
    provider = FakeChatProvider()
    request = ChatRequest(messages=[PromptMessage(role="user", content="hello")])

    response = provider.generate(request)

    assert response.text == "Echo: hello"


def test_fake_chat_provider_rejects_missing_user_message() -> None:
    provider = FakeChatProvider()
    request = ChatRequest(messages=[PromptMessage(role="system", content="system")])

    with pytest.raises(ProviderResponseError, match="No user message"):
        provider.generate(request)
```

- [ ] **Step 2: Run provider tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_chat_provider.py -q
```

Expected: FAIL because `app.brain.providers.chat` does not exist.

- [ ] **Step 3: Implement provider contract and fake provider**

Create `app/brain/providers/chat.py`:

```python
"""Chat provider contracts and test providers."""

from dataclasses import dataclass
from typing import Protocol

from app.brain.prompts.registry import PromptMessage


@dataclass(frozen=True)
class ChatRequest:
    """Provider-neutral chat request."""

    messages: list[PromptMessage]


@dataclass(frozen=True)
class ChatResponse:
    """Provider-neutral chat response."""

    text: str


class ProviderError(Exception):
    """Base error for chat provider failures."""


class ProviderConfigError(ProviderError):
    """Raised when a provider is missing required configuration."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns unusable content."""


class ChatProvider(Protocol):
    """Interface for chat providers."""

    def generate(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat response."""


class FakeChatProvider:
    """Deterministic local chat provider for tests and demos."""

    def __init__(self, response_text: str | None = None) -> None:
        self._response_text = response_text

    def generate(self, request: ChatRequest) -> ChatResponse:
        """Generate a deterministic fake response."""
        if self._response_text is not None:
            return ChatResponse(text=self._response_text)

        for message in reversed(request.messages):
            if message.role == "user":
                return ChatResponse(text=f"Echo: {message.content}")

        raise ProviderResponseError("No user message found in chat request")
```

- [ ] **Step 4: Export provider names**

Modify `app/brain/providers/__init__.py`:

```python
"""Chat provider exports."""

from app.brain.providers.chat import (
    ChatProvider,
    ChatRequest,
    ChatResponse,
    FakeChatProvider,
    ProviderConfigError,
    ProviderError,
    ProviderResponseError,
)

__all__ = [
    "ChatProvider",
    "ChatRequest",
    "ChatResponse",
    "FakeChatProvider",
    "ProviderConfigError",
    "ProviderError",
    "ProviderResponseError",
]
```

- [ ] **Step 5: Run provider tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_chat_provider.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/brain/providers/__init__.py app/brain/providers/chat.py app/tests/test_chat_provider.py
git commit -m "feat: add chat provider contract"
```

---

## Task 4: Dialogue Controller

**Files:**
- Create: `app/brain/dialogue_controller.py`
- Modify: `app/brain/__init__.py`
- Test: `app/tests/test_dialogue_controller.py`

- [ ] **Step 1: Write failing controller tests**

Create `app/tests/test_dialogue_controller.py`:

```python
"""Tests for dialogue controller orchestration."""

from app.brain.dialogue_controller import DialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.chat import ChatRequest, ChatResponse, FakeChatProvider, ProviderError
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.states import AppState
from app.core.event_bus import EventBus


class FailingProvider:
    def generate(self, request: ChatRequest) -> ChatResponse:
        raise ProviderError("provider failed")


def test_dialogue_controller_publishes_state_changes_and_reply() -> None:
    bus = EventBus()
    controller = DialogueController(
        event_bus=bus,
        prompt_registry=PromptRegistry(default_system_prompt="system"),
        chat_provider=FakeChatProvider(response_text="hello user"),
    )
    events: list[BaseEvent] = []
    bus.subscribe(STATE_CHANGE_REQUESTED, events.append)
    bus.subscribe(ASSISTANT_TEXT_RECEIVED, events.append)
    controller.start()

    bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req1",
            source="test",
            payload={"text": "hi"},
        )
    )

    controller.stop()
    assert [event.event_type for event in events] == [
        STATE_CHANGE_REQUESTED,
        ASSISTANT_TEXT_RECEIVED,
        STATE_CHANGE_REQUESTED,
    ]
    assert events[0].payload["target_state"] == AppState.THINKING.value
    assert events[1].payload == {"text": "hello user"}
    assert events[2].payload["target_state"] == AppState.IDLE.value


def test_dialogue_controller_ignores_empty_text() -> None:
    bus = EventBus()
    controller = DialogueController(
        event_bus=bus,
        prompt_registry=PromptRegistry(),
        chat_provider=FakeChatProvider(),
    )
    events: list[BaseEvent] = []
    bus.subscribe(STATE_CHANGE_REQUESTED, events.append)
    bus.subscribe(ASSISTANT_TEXT_RECEIVED, events.append)
    controller.start()

    bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req2",
            source="test",
            payload={"text": "   "},
        )
    )

    controller.stop()
    assert events == []


def test_dialogue_controller_publishes_error_on_provider_failure() -> None:
    bus = EventBus()
    controller = DialogueController(
        event_bus=bus,
        prompt_registry=PromptRegistry(),
        chat_provider=FailingProvider(),
    )
    events: list[BaseEvent] = []
    bus.subscribe(STATE_CHANGE_REQUESTED, events.append)
    bus.subscribe(SYSTEM_ERROR, events.append)
    controller.start()

    bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req3",
            source="test",
            payload={"text": "hi"},
        )
    )

    controller.stop()
    assert [event.event_type for event in events] == [
        STATE_CHANGE_REQUESTED,
        SYSTEM_ERROR,
        STATE_CHANGE_REQUESTED,
    ]
    assert events[0].payload["target_state"] == AppState.THINKING.value
    assert events[1].payload["message"] == "provider failed"
    assert events[2].payload["target_state"] == AppState.ERROR.value
```

- [ ] **Step 2: Run controller tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_dialogue_controller.py -q
```

Expected: FAIL because `app.brain.dialogue_controller` does not exist.

- [ ] **Step 3: Implement DialogueController**

Create `app/brain/dialogue_controller.py`:

```python
"""Dialogue orchestration for text chat."""

from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.chat import ChatProvider, ChatRequest, ProviderError
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGE_REQUESTED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import AssistantTextReceivedPayload
from app.contracts.states import AppState
from app.core.event_bus import EventBus


class DialogueController:
    """Coordinates user text, prompts, providers, and state events."""

    def __init__(
        self,
        event_bus: EventBus,
        prompt_registry: PromptRegistry,
        chat_provider: ChatProvider,
    ) -> None:
        self._event_bus = event_bus
        self._prompt_registry = prompt_registry
        self._chat_provider = chat_provider

    def start(self) -> None:
        """Start listening for user text submissions."""
        self._event_bus.subscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def stop(self) -> None:
        """Stop listening for user text submissions."""
        self._event_bus.unsubscribe(USER_TEXT_SUBMITTED, self._on_user_text_submitted)

    def _on_user_text_submitted(self, event: BaseEvent) -> None:
        text = str(event.payload.get("text", "")).strip()
        if not text:
            return

        self._publish_state(event.request_id, AppState.THINKING, "user text submitted")

        try:
            messages = self._prompt_registry.build_chat_messages(text)
            response = self._chat_provider.generate(ChatRequest(messages=messages))
        except ProviderError as exc:
            self._publish_error(event.request_id, str(exc))
            self._publish_state(event.request_id, AppState.ERROR, "dialogue provider failed")
            return

        self._event_bus.publish(
            BaseEvent(
                event_type=ASSISTANT_TEXT_RECEIVED,
                request_id=event.request_id,
                source="dialogue_controller",
                payload=AssistantTextReceivedPayload(text=response.text).to_event_payload(),
            )
        )
        self._publish_state(event.request_id, AppState.IDLE, "assistant response received")

    def _publish_state(self, request_id: str, state: AppState, reason: str) -> None:
        self._event_bus.publish(
            BaseEvent(
                event_type=STATE_CHANGE_REQUESTED,
                request_id=request_id,
                source="dialogue_controller",
                payload={"target_state": state.value, "reason": reason},
            )
        )

    def _publish_error(self, request_id: str, message: str) -> None:
        self._event_bus.publish(
            BaseEvent(
                event_type=SYSTEM_ERROR,
                request_id=request_id,
                source="dialogue_controller",
                payload={"message": message},
            )
        )
```

- [ ] **Step 4: Export DialogueController**

Modify `app/brain/__init__.py`:

```python
"""Brain layer exports."""

from app.brain.dialogue_controller import DialogueController

__all__ = ["DialogueController"]
```

- [ ] **Step 5: Run controller tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_dialogue_controller.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/brain/__init__.py app/brain/dialogue_controller.py app/tests/test_dialogue_controller.py
git commit -m "feat: add dialogue controller"
```

---

## Task 5: App Config And MiniMax Provider

**Files:**
- Modify: `app/core/config.py`
- Create: `app/brain/providers/minimax.py`
- Modify: `app/brain/providers/__init__.py`
- Modify: `.env.example`
- Test: `app/tests/test_minimax_provider.py`

- [ ] **Step 1: Write failing MiniMax provider tests**

Create `app/tests/test_minimax_provider.py`:

```python
"""Tests for MiniMax provider."""

import json
from urllib.error import HTTPError

import pytest

from app.brain.prompts.registry import PromptMessage
from app.brain.providers.chat import ChatRequest, ProviderConfigError, ProviderResponseError
from app.brain.providers.minimax import MiniMaxChatProvider, MiniMaxConfig


def test_minimax_config_requires_api_key() -> None:
    config = MiniMaxConfig(api_key="", group_id="group", base_url="https://api.example")
    provider = MiniMaxChatProvider(config=config)

    with pytest.raises(ProviderConfigError, match="MINIMAX_API_KEY"):
        provider.generate(ChatRequest(messages=[PromptMessage(role="user", content="hi")]))


def test_minimax_config_requires_group_id() -> None:
    config = MiniMaxConfig(api_key="key", group_id="", base_url="https://api.example")
    provider = MiniMaxChatProvider(config=config)

    with pytest.raises(ProviderConfigError, match="MINIMAX_GROUP_ID"):
        provider.generate(ChatRequest(messages=[PromptMessage(role="user", content="hi")]))


def test_minimax_parse_response_text() -> None:
    payload = {"choices": [{"message": {"content": "hello"}}]}

    assert MiniMaxChatProvider.parse_response_text(payload) == "hello"


def test_minimax_rejects_empty_response_text() -> None:
    payload = {"choices": [{"message": {"content": "   "}}]}

    with pytest.raises(ProviderResponseError, match="empty"):
        MiniMaxChatProvider.parse_response_text(payload)
```

- [ ] **Step 2: Run MiniMax provider tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_minimax_provider.py -q
```

Expected: FAIL because `app.brain.providers.minimax` does not exist.

- [ ] **Step 3: Add config values**

Modify `app/core/config.py` inside `AppConfig.__init__`:

```python
self.chat_provider: str = os.getenv("CHAT_PROVIDER", "fake")
self.minimax_api_key: str = os.getenv("MINIMAX_API_KEY", "")
self.minimax_group_id: str = os.getenv("MINIMAX_GROUP_ID", "")
self.minimax_base_url: str = os.getenv(
    "MINIMAX_BASE_URL",
    "https://api.minimax.chat/v1/text/chatcompletion_v2",
)
self.minimax_model: str = os.getenv("MINIMAX_MODEL", "abab6.5-chat")
self.minimax_timeout_seconds: float = float(os.getenv("MINIMAX_TIMEOUT_SECONDS", "30"))
```

- [ ] **Step 4: Implement MiniMax provider**

Create `app/brain/providers/minimax.py`:

```python
"""MiniMax chat provider."""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.brain.providers.chat import (
    ChatRequest,
    ChatResponse,
    ProviderConfigError,
    ProviderResponseError,
)


@dataclass(frozen=True)
class MiniMaxConfig:
    """Configuration for MiniMax chat provider."""

    api_key: str
    group_id: str
    base_url: str
    model: str = "abab6.5-chat"
    timeout_seconds: float = 30


class MiniMaxChatProvider:
    """Network-backed MiniMax chat provider."""

    def __init__(self, config: MiniMaxConfig) -> None:
        self._config = config

    def generate(self, request: ChatRequest) -> ChatResponse:
        """Generate a response with MiniMax."""
        self._validate_config()
        response_payload = self._post_chat_completion(request)
        return ChatResponse(text=self.parse_response_text(response_payload))

    @staticmethod
    def parse_response_text(payload: dict[str, object]) -> str:
        """Extract response text from a MiniMax-compatible response payload."""
        try:
            choices = payload["choices"]
            first_choice = choices[0]  # type: ignore[index]
            message = first_choice["message"]  # type: ignore[index]
            content = str(message["content"]).strip()  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderResponseError("MiniMax response payload is malformed") from exc

        if not content:
            raise ProviderResponseError("MiniMax response text is empty")
        return content

    def _validate_config(self) -> None:
        if not self._config.api_key:
            raise ProviderConfigError("MINIMAX_API_KEY is required for MiniMax provider")
        if not self._config.group_id:
            raise ProviderConfigError("MINIMAX_GROUP_ID is required for MiniMax provider")
        if not self._config.base_url:
            raise ProviderConfigError("MINIMAX_BASE_URL is required for MiniMax provider")

    def _post_chat_completion(self, request: ChatRequest) -> dict[str, object]:
        url = f"{self._config.base_url}?GroupId={self._config.group_id}"
        body = {
            "model": self._config.model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
        }
        http_request = Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(http_request, timeout=self._config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError) as exc:
            raise ProviderResponseError(f"MiniMax request failed: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("MiniMax response was not valid JSON") from exc
```

- [ ] **Step 5: Export MiniMax names**

Modify `app/brain/providers/__init__.py` to include:

```python
from app.brain.providers.minimax import MiniMaxChatProvider, MiniMaxConfig
```

and add `"MiniMaxChatProvider"` and `"MiniMaxConfig"` to `__all__`.

- [ ] **Step 6: Update `.env.example`**

Ensure `.env.example` contains:

```text
APP_ENV=dev
CHAT_PROVIDER=fake
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
MINIMAX_BASE_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
MINIMAX_MODEL=abab6.5-chat
MINIMAX_TIMEOUT_SECONDS=30
```

- [ ] **Step 7: Run MiniMax provider tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_minimax_provider.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add .env.example app/core/config.py app/brain/providers/__init__.py app/brain/providers/minimax.py app/tests/test_minimax_provider.py
git commit -m "feat: add minimax chat provider"
```

---

## Task 6: ViewModel Dialogue State

**Files:**
- Modify: `app/ui/view_model.py`
- Test: `app/tests/test_view_model.py`

- [ ] **Step 1: Add failing ViewModel tests for assistant replies and errors**

Add these imports and tests to `app/tests/test_view_model.py`:

```python
from app.contracts.events import ASSISTANT_TEXT_RECEIVED, SYSTEM_ERROR


def test_handle_assistant_text_received_updates_reply_text() -> None:
    vm = DesktopViewModel()
    event = BaseEvent(
        event_type=ASSISTANT_TEXT_RECEIVED,
        request_id="req8",
        source="test",
        payload={"text": "Hello from assistant"},
    )

    vm.handle_assistant_text_received(event)

    assert vm.last_assistant_text == "Hello from assistant"


def test_handle_system_error_updates_error_text() -> None:
    vm = DesktopViewModel()
    event = BaseEvent(
        event_type=SYSTEM_ERROR,
        request_id="req9",
        source="test",
        payload={"message": "provider failed"},
    )

    vm.handle_system_error(event)

    assert vm.error_text == "provider failed"
```

- [ ] **Step 2: Run ViewModel tests and verify they fail**

Run:

```bash
python -m pytest app/tests/test_view_model.py -q
```

Expected: FAIL because `last_assistant_text`, `error_text`, `handle_assistant_text_received`, and `handle_system_error` do not exist.

- [ ] **Step 3: Implement ViewModel dialogue fields and handlers**

Modify `DesktopViewModel.__init__` in `app/ui/view_model.py`:

```python
self.last_assistant_text: str = ""
self.error_text: str = ""
```

Add methods to `DesktopViewModel`:

```python
def handle_assistant_text_received(self, event: BaseEvent) -> None:
    """Handle assistant.text_received event and update reply text."""
    if event.event_type != ASSISTANT_TEXT_RECEIVED:
        return

    self.last_assistant_text = str(event.payload.get("text", ""))
    self.error_text = ""

def handle_system_error(self, event: BaseEvent) -> None:
    """Handle system.error event and update error text."""
    if event.event_type != SYSTEM_ERROR:
        return

    self.error_text = str(event.payload.get("message", ""))
```

Also update imports in `app/ui/view_model.py`:

```python
from app.contracts.events import ASSISTANT_TEXT_RECEIVED, STATE_CHANGED, SYSTEM_ERROR, BaseEvent
```

- [ ] **Step 4: Run ViewModel tests and verify they pass**

Run:

```bash
python -m pytest app/tests/test_view_model.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/ui/view_model.py app/tests/test_view_model.py
git commit -m "feat: display dialogue view state"
```

---

## Task 7: UI Text Input And App Wiring

**Files:**
- Modify: `app/ui/window.py`
- Modify: `app/main.py`
- Test: `app/tests/test_dialogue_controller.py`

- [ ] **Step 1: Add a controller-level integration test that uses StateController**

Add this test to `app/tests/test_dialogue_controller.py`:

```python
from app.core.state_controller import StateController
from app.core.state_machine import StateMachine


def test_dialogue_controller_integrates_with_state_controller() -> None:
    bus = EventBus()
    state_machine = StateMachine()
    state_controller = StateController(bus, state_machine)
    dialogue_controller = DialogueController(
        event_bus=bus,
        prompt_registry=PromptRegistry(default_system_prompt="system"),
        chat_provider=FakeChatProvider(response_text="reply"),
    )
    replies: list[BaseEvent] = []
    bus.subscribe(ASSISTANT_TEXT_RECEIVED, replies.append)
    state_controller.start()
    dialogue_controller.start()

    bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id="req4",
            source="test",
            payload={"text": "hi"},
        )
    )

    dialogue_controller.stop()
    state_controller.stop()
    assert replies[0].payload == {"text": "reply"}
    assert state_machine.get_state() == AppState.IDLE
```

- [ ] **Step 2: Run the controller integration test**

Run:

```bash
python -m pytest app/tests/test_dialogue_controller.py::test_dialogue_controller_integrates_with_state_controller -q
```

Expected: PASS if prior tasks were implemented correctly. If it fails, fix the controller before editing UI.

- [ ] **Step 3: Add UI controls and submit callback**

Modify `app/ui/window.py` imports:

```python
from collections.abc import Callable

from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
```

Change `DesktopWindow.__init__` signature:

```python
def __init__(
    self,
    view_model: DesktopViewModel,
    on_user_text_submitted: Callable[[str], None] | None = None,
) -> None:
```

Inside `__init__`, assign:

```python
self._on_user_text_submitted = on_user_text_submitted
```

After the state label is added, add:

```python
self._reply_display = QTextEdit()
self._reply_display.setReadOnly(True)
self._reply_display.setPlaceholderText("Assistant replies will appear here.")
layout.addWidget(self._reply_display)

self._input = QLineEdit()
self._input.setPlaceholderText("Type a message...")
self._input.returnPressed.connect(self._submit_user_text)
layout.addWidget(self._input)

self._send_button = QPushButton("Send")
self._send_button.clicked.connect(self._submit_user_text)
layout.addWidget(self._send_button)
```

Add this method to `DesktopWindow`:

```python
def _submit_user_text(self) -> None:
    text = self._input.text().strip()
    if not text or self._on_user_text_submitted is None:
        return

    self._input.clear()
    self._on_user_text_submitted(text)
```

Update `update_from_view_model`:

```python
def update_from_view_model(self) -> None:
    """Update UI from view model state."""
    self._state_label.setText(self._view_model.display_text)
    self._reply_display.setPlainText(self._view_model.last_assistant_text)
    self._send_button.setEnabled(self._view_model.state != AppState.THINKING)
    if self._view_model.error_text:
        self._reply_display.setPlainText(self._view_model.error_text)
```

Also import `AppState` from `app.contracts.states`.

- [ ] **Step 4: Wire DialogueController and UI events in app startup**

Modify `app/main.py` imports:

```python
import uuid

from app.brain.dialogue_controller import DialogueController
from app.brain.prompts.registry import PromptRegistry
from app.brain.providers.chat import FakeChatProvider
from app.brain.providers.minimax import MiniMaxChatProvider, MiniMaxConfig
from app.contracts.events import (
    ASSISTANT_TEXT_RECEIVED,
    STATE_CHANGED,
    SYSTEM_ERROR,
    USER_TEXT_SUBMITTED,
    BaseEvent,
)
from app.contracts.payloads import UserTextSubmittedPayload
```

Add a provider factory near `main`:

```python
def build_chat_provider(config: object) -> object:
    """Build the configured chat provider."""
    if getattr(config, "chat_provider", "fake") == "minimax":
        return MiniMaxChatProvider(
            MiniMaxConfig(
                api_key=getattr(config, "minimax_api_key"),
                group_id=getattr(config, "minimax_group_id"),
                base_url=getattr(config, "minimax_base_url"),
                model=getattr(config, "minimax_model"),
                timeout_seconds=getattr(config, "minimax_timeout_seconds"),
            )
        )
    return FakeChatProvider()
```

Inside `main`, create the controller before the window callback:

```python
prompt_registry = PromptRegistry()
chat_provider = build_chat_provider(config)
dialogue_controller = DialogueController(event_bus, prompt_registry, chat_provider)
```

Create the submit callback before constructing `DesktopWindow`:

```python
def on_user_text_submitted(text: str) -> None:
    event_bus.publish(
        BaseEvent(
            event_type=USER_TEXT_SUBMITTED,
            request_id=str(uuid.uuid4()),
            source="desktop_window",
            payload=UserTextSubmittedPayload(text=text).to_event_payload(),
        )
    )
```

Construct the window with the callback:

```python
window = DesktopWindow(view_model, on_user_text_submitted=on_user_text_submitted)
```

Add subscriptions:

```python
def on_assistant_text_received(event: BaseEvent) -> None:
    view_model.handle_assistant_text_received(event)
    window.update_from_view_model()

def on_system_error(event: BaseEvent) -> None:
    view_model.handle_system_error(event)
    window.update_from_view_model()

event_bus.subscribe(ASSISTANT_TEXT_RECEIVED, on_assistant_text_received)
event_bus.subscribe(SYSTEM_ERROR, on_system_error)
```

Start dialogue controller after `state_controller.start()`:

```python
dialogue_controller.start()
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m pytest app/tests/test_dialogue_controller.py app/tests/test_view_model.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/ui/window.py app/main.py app/tests/test_dialogue_controller.py
git commit -m "feat: wire text dialogue UI"
```

---

## Task 8: Quality Gate And Documentation Update

**Files:**
- Modify: `docs/ROADMAP.md`

- [ ] **Step 1: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected: PASS.

- [ ] **Step 2: Run ruff**

Run:

```bash
python -m ruff check .
```

Expected: PASS.

- [ ] **Step 3: Attempt mypy**

Run:

```bash
python -m mypy app
```

Expected: PASS when the local virtual environment is valid. If it fails because `.venv` points to a missing Python runtime, record the exact error in the final implementation summary and do not hide it.

- [ ] **Step 4: Check architecture constraints manually**

Run:

```bash
rg "MiniMax|MiniMaxChatProvider|minimax" app/ui app/contracts app/core
```

Expected: no UI-to-MiniMax direct call. Matches in `app/core/config.py` are acceptable because config owns environment values.

Run:

```bash
rg "You are|system prompt|Prompt" app/ui app/core app/contracts
```

Expected: no prompt text outside `app/brain/prompts`.

- [ ] **Step 5: Update roadmap status**

In `docs/ROADMAP.md`, update the V3 section to show the text loop slice completed while keeping TTS unchecked:

```markdown
- [x] MiniMax Provider implementation
- [x] Text dialogue interface
- [ ] TTS voice output
- [x] Prompt Registry initialization
```

If the existing file still has encoding damage, make the smallest possible V3-section-only edit and avoid rewriting unrelated content.

- [ ] **Step 6: Run final diff checks**

Run:

```bash
git diff --check
```

Expected: no output.

Run:

```bash
git status --short
```

Expected: only the intended implementation and roadmap files are modified.

- [ ] **Step 7: Final commit**

```bash
git add docs/ROADMAP.md
git commit -m "docs: mark v3 text dialogue slice"
```

---

## Execution Notes

- Use the existing branch unless the user asks for a new branch.
- Keep commits task-sized.
- Do not push without explicit user approval.
- Use `CHAT_PROVIDER=fake` as the local default.
- Do not require real MiniMax credentials for default tests.
- Do not add TTS, ASR, Memory, Tool Router, Agent planning, or Avatar behavior while executing this plan.

## Self-Review

Spec coverage:

- Text input and reply display: Task 7.
- Prompt Registry: Task 2.
- Chat Provider protocol and fake provider: Task 3.
- MiniMax provider and config: Task 5.
- Dialogue orchestration and state transitions: Task 4 and Task 7.
- Error path through `SYSTEM_ERROR`: Task 4 and Task 6.
- Tests and quality gates: Tasks 1 through 8.
- Scope exclusions: Execution Notes and per-task boundaries.

Placeholder scan:

- No placeholder markers are present.
- Steps include concrete file paths, commands, and expected results.

Type consistency:

- `PromptMessage`, `ChatRequest`, `ChatResponse`, and `ChatProvider.generate()` names are introduced before use.
- `ASSISTANT_TEXT_RECEIVED` is introduced before controller and ViewModel usage.
- `UserTextSubmittedPayload` and `AssistantTextReceivedPayload` serialize to plain event dictionaries.
