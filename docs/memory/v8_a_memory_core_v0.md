# V8-A Memory Core v0

## 1. Overview

V8-A establishes the first layer of the "小云 memory system": extracting structured memory candidates from user input without automatic persistence.

**What V8-A does:**
- Receives a user text input
- Determines if there is "memorable information"
- Generates structured `MemoryCandidate` objects
- Candidates can be inspected via probe / tests

**What V8-A does NOT do:**
- Long-term memory persistence
- Automatic prompt injection
- Changing reply behavior
- Writing to databases or vector stores
- RAG retrieval

## 2. MemoryCandidate Structure

```python
@dataclass(frozen=True)
class MemoryCandidate:
    kind: MemoryKind           # Type of memory
    importance: MemoryImportance  # LOW / MEDIUM / HIGH
    text: str                 # Summarized candidate text (max 160 chars)
    evidence: str             # Original triggering snippet (max 160 chars)
    confidence: float         # 0.0–1.0
    source: str = "deterministic_extractor"
```

## 3. MemoryKind

| Kind | Description |
|------|-------------|
| `identity` | User's self-description |
| `preference` | User's stated preferences |
| `relationship` | User's relationships (explicit facts only) |
| `project` | User's projects or work |
| `health` | User's health mentions (no diagnosis) |
| `emotion_pattern` | Recurring emotional patterns |
| `boundary` | User's explicit requests not to remember something |
| `other` | Catch-all for other types |

## 4. MemoryImportance

| Level | When to use |
|-------|-------------|
| `LOW` | Minor, easily forgotten |
| `MEDIUM` | Normal preferences, projects |
| `HIGH` | Health, relationships, explicit boundaries |

## 5. DeterministicMemoryExtractor Rules

The extractor uses rule-based pattern matching (no LLM).

### 5.1 PREFERENCE

**Triggers:** 我喜欢, 我不喜欢, 我更喜欢, 我讨厌, 我偏好, 我习惯
**Importance:** MEDIUM | **Confidence:** 0.75

### 5.2 PROJECT

**Triggers:** 我正在做, 我在做, 我的项目, 这个项目
**Importance:** MEDIUM | **Confidence:** 0.70

### 5.3 RELATIONSHIP

**Triggers:** 我女朋友, 我妈, 我爸, 我朋友, 我同事, etc.
**Importance:** HIGH | **Confidence:** 0.80

Note: Only captures explicit relationship facts stated by the user.

### 5.4 HEALTH

**Triggers:** 我头疼, 我睡不着, 我焦虑, 我抑郁, etc.
**Importance:** HIGH | **Confidence:** 0.75

Note: Does NOT diagnose. Only records "user mentioned discomfort."

### 5.5 EMOTION_PATTERN

**Triggers:** 我最近总是, 我经常觉得, 我总觉得, 我害怕, etc.
**Importance:** MEDIUM | **Confidence:** 0.70

### 5.6 BOUNDARY

**Triggers:** 不要记住, 别记住, 不要提醒我, 别说, etc.
**Importance:** HIGH | **Confidence:** 0.85

Note: Generates a boundary candidate without storing the specific content.

## 6. Non-Extraction Rules

The following should NOT generate candidates:
- Empty or whitespace-only input
- Small talk: 你好, 在吗, 谢谢, 好的, 哈哈, 继续
- Text exceeding 160 chars for text/evidence fields

Maximum 3 candidates per input to avoid over-extraction.

## 7. Privacy Principles

- V8-A does NOT save anything automatically
- Candidates are for inspection only
- Health information is tagged HIGH importance but not persisted without user consent
- Boundary requests generate candidates but do not store the specific content

## 8. Future Roadmap

| Phase | Goal |
|-------|------|
| V8-A | Memory candidate extraction (this phase) |
| V8-B | Memory confirmation/rejection mechanism |
| V8-C | In-session memory injection |
| V8-D | Local persistence |
| V8-E | Memory management UI |
