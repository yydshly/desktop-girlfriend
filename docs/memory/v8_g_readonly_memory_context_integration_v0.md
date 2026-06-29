# V8-G Read-only Memory Context Integration v0

## 目标

V8-G 的目标是把"已保存的 active memory"以只读方式接入主聊天 prompt。

只做：

```
LocalJsonMemoryRepository.list_active()
  -> SessionMemoryContextBuilder.build_from_records()
  -> AsyncDialogueController.session_memory_context_provider
  -> PromptRegistry 第二条 system message
```

明确不做：

- 不自动抽取用户输入
- 不自动生成 pending
- 不自动 confirm
- 不自动写 repository
- 不自动保存用户聊天
- 不接 UI 记忆确认
- 不做后台记忆任务

也就是说，V8-G 只让小云"读取已经存在的 active memory"，不让她自己新增记忆。

## 为什么本阶段只读 active memory

V8-A 到 V8-F 已经完成了：

- 记忆抽取（V8-A）
- 记忆确认/拒绝机制（V8-B）
- CLI 管理入口（V8-F）

V8-G 的重点是**接入主流程**，而不是再添加新功能。只读 active memory 是最简单、最安全的接入方式：

1. **已有记忆才能注入**：没有确认的记忆不应该出现在 prompt 里
2. **最小侵入性**：不需要改变现有 runtime 架构
3. **风险可控**：只读操作，不会意外修改或删除记忆

## 为什么默认 MEMORY_CONTEXT_ENABLED=false

`MEMORY_CONTEXT_ENABLED` 默认为 `false`，因为：

1. **用户必须有意识开启**：记忆上下文注入是可选功能
2. **隐私考量**：用户需要明确同意后才会在 prompt 中注入记忆
3. **避免意外行为**：没有通过 CLI 管理记忆的用户不应看到意外的 prompt 变化

## 为什么不自动抽取用户输入

自动抽取需要：

1. 每次用户输入都调用 `runtime.submit_user_text()`
2. 产生 pending 记忆需要 UI 确认
3. 没有 UI 确认的情况下，无法决定 confirm 还是 reject

V8-H 会实现用户确认入口。

## 为什么不自动保存聊天

自动保存聊天涉及：

1. 需要明确的用户同意
2. 需要 UI 交互来 confirm/reject
3. 隐私合规问题

V8-H 会实现用户确认入口。

## 为什么不自动 confirm

所有记忆必须经过用户明确确认（V8-B 设计原则）。自动 confirm 违背了这一原则。

## memory context provider 如何接入 AsyncDialogueController

V8-C 已经在 `AsyncDialogueController` 预留了 `session_memory_context_provider` 参数：

```python
dialogue_controller = AsyncDialogueController(
    ...
    session_memory_context_provider=session_memory_context_provider,
)
```

`create_readonly_memory_context_provider` 返回一个 `Callable[[], str]`，每次对话时调用一次，返回值作为 `memory_context` 传入 `PromptRegistry`。

## memory 文件不存在时的行为

`LocalJsonMemoryRepository` 在文件不存在时返回空列表 `[]`。因此：

- `repository.list_active()` 返回 `()`
- `context_builder.build_from_records(())` 返回 `""`
- Prompt 中不注入任何记忆上下文
- 聊天不受影响

## memory provider 异常时为什么不影响聊天

`AsyncDialogueController` 已经对 provider 调用做了异常兜底：

```python
if self._session_memory_context_provider is not None:
    try:
        session_memory_context = self._session_memory_context_provider()
    except Exception:
        logger.exception("Session memory context provider failed")
        session_memory_context = None
```

即使 provider 抛出异常，聊天仍会正常进行，只是没有记忆上下文。

## 后续 V8-H：用户确认入口 / UI 管理入口

V8-H 计划：

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入 ✅
V8-D：本地持久化 ✅
V8-E：Memory Runtime Service ✅
V8-F：CLI / Probe 管理入口 ✅
V8-G：只读 Memory Context 接入（当前）
V8-H：用户确认入口 / UI 管理入口
```

V8-H 计划：
1. UI 让用户 confirm/reject pending 记忆
2. UI 管理已保存的记忆（查看/删除）
3. 自动从用户输入抽取并生成 pending

## 文件结构

```
app/brain/memory/
├── __init__.py            # 新增导出
├── integration.py         # V8-G: read-only provider

app/core/
└── config.py              # V8-G: 新增 memory 配置

app/main.py                # V8-G: 接入 provider

scripts/
└── probe_memory_readonly_integration.py  # V8-G: probe 脚本

app/tests/
└── test_memory_readonly_integration.py  # V8-G: 测试
```
