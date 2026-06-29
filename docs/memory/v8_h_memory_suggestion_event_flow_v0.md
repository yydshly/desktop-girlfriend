# V8-H Memory Suggestion Event Flow v0

## 目标

V8-H 的目标是新增"记忆候选建议事件流"。

也就是说，当用户输入一句话时，系统可以：

```
user.text_submitted
  -> MemorySuggestionController
  -> MemoryRuntimeService.submit_user_text()
  -> 生成 PendingMemory
  -> 发布 memory.suggestions_detected 事件
```

然后外部可以通过事件确认或拒绝：

```
memory.confirm_requested
  -> confirm_pending()
  -> repository.add()
  -> memory.confirmed

memory.reject_requested
  -> reject_pending()
  -> memory.rejected
```

**注意：V8-H 仍然不是 UI。V8-H 只做事件层、控制器和测试闭环。**

## 为什么本阶段是事件流，不是 UI

V8-H 专注于事件层的协调逻辑：

1. **职责分离**：控制器负责事件协调，UI 负责展示和交互
2. **可测试**：事件流可以在没有 UI 的情况下测试
3. **可组合**：任何监听这些事件的组件都可以参与记忆确认流程

V8-I 才会实现 UI 记忆候选展示与确认按钮。

## MEMORY_SUGGESTIONS_ENABLED 为什么默认 false

`MEMORY_SUGGESTIONS_ENABLED` 默认为 `false`，因为：

1. **用户必须有意识开启**：记忆候选建议是可选功能
2. **避免意外行为**：没有 UI 确认入口时，不应该生成 pending 记忆
3. **隐私考量**：用户需要明确同意后才会在 prompt 中注入记忆

## user.text_submitted 如何生成 pending

当 `USER_TEXT_SUBMITTED` 事件被 `MemorySuggestionController` 收到时：

1. 从事件 payload 中提取 `text`
2. 调用 `runtime.submit_user_text(text)`
3. `submit_user_text` 调用 `DeterministicMemoryExtractor.extract()` 生成候选
4. 候选通过 `MemoryConfirmationService.submit_candidates()` 变成 `PendingMemory`
5. 发布 `MEMORY_SUGGESTIONS_DETECTED` 事件，包含 pending 列表

## 为什么 pending 不自动保存

`submit_user_text()` 只创建 `PendingMemory`，不自动确认或持久化。这是因为：

1. **误抽取**：规则抽取可能产生不重要的候选
2. **用户意图**：用户可能随口说说，不想记住
3. **确认原则**：所有记忆必须经过用户（或代理）明确确认

## confirm_requested 为什么才写 repository

`confirm_pending()` 才会：

1. 调用 `confirmation_service.confirm()` 确认
2. 将 `ConfirmedMemory` 转为 `MemoryRecord`
3. 写入 `repository.add(record)`

只有明确确认的记忆才会持久化。

## reject_requested 为什么不写 repository

`reject_pending()` 只调用 `confirmation_service.reject()`，返回 `RejectedMemory`。

已拒绝的记忆不应该再次出现，所以不需要持久化。

## MEMORY_ERROR 为什么不影响聊天主流程

`MemorySuggestionController` 对所有异常进行捕获并发布 `MEMORY_ERROR` 事件：

```python
except Exception:
    logger.exception("Memory suggestion extraction failed")
    self._dispatch_memory_error("Memory suggestion extraction failed")
    return
```

`AsyncDialogueController` 不订阅 `MEMORY_ERROR`，因此不影响聊天主流程。

## 为什么 payload 不包含 evidence

`suggestions` payload 只包含：

- `pending_id`
- `kind`
- `importance`
- `text`

不包含 `evidence`，因为：

1. **隐私**：evidence 可能包含原始对话内容
2. **简洁**：UI 只需要显示 text，不需要 evidence
3. **安全**：避免在事件中泄露敏感信息

## 后续 V8-I：UI 记忆候选展示与确认按钮

V8-H 计划：

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入 ✅
V8-D：本地持久化 ✅
V8-E：Memory Runtime Service ✅
V8-F：CLI / Probe 管理入口 ✅
V8-G：只读 Memory Context 接入 ✅
V8-H：Memory Suggestion Event Flow（当前）
V8-I：UI 记忆候选展示与确认按钮
```

V8-I 计划：
1. DesktopWindow 展示 memory.suggestions_detected 事件
2. 用户可以 confirm 或 reject pending 记忆
3. 发布 memory.confirm_requested 或 memory.reject_requested 事件
4. Controller 处理事件并更新 repository

## 文件结构

```
app/brain/memory/
├── __init__.py            # V8-H: 导出 MemorySuggestionController
├── controller.py           # V8-H: MemorySuggestionController

app/contracts/
├── events.py              # V8-H: 新增 memory.* 事件常量
├── payloads.py            # V8-H: 新增 memory payload 类型

app/core/
└── config.py              # V8-H: 新增 MEMORY_SUGGESTIONS_ENABLED

app/main.py                # V8-H: 接入 MemorySuggestionController

scripts/
└── probe_memory_suggestion_events.py  # V8-H: probe 脚本

app/tests/
└── test_memory_suggestion_controller.py  # V8-H: 测试
```
