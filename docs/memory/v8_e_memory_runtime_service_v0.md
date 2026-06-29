# V8-E Memory Runtime Service v0

## 目标

V8-E 的目标是把 V8-A/B/C/D 的底层模块串成一个统一的 runtime service。

已有模块：

- **V8-A**：DeterministicMemoryExtractor → MemoryCandidate
- **V8-B**：MemoryConfirmationService → Pending / Confirmed / Rejected
- **V8-C**：SessionMemoryContextBuilder → prompt-safe memory context
- **V8-D**：LocalJsonMemoryRepository → local MemoryRecord persistence

V8-E 新增：

- **MemoryRuntimeService**：串联上述所有模块
- **create_local_memory_runtime()**：默认工厂函数

## RuntimeService 串联链路

```
用户文本
  -> extract_candidates()      # V8-A: 抽取候选
  -> submit_user_text()       # V8-B: 提交 pending
  -> confirm_pending()         # V8-B + V8-D: 确认 + 持久化
  -> reject_pending()          # V8-B: 拒绝
  -> list_active_records()     # V8-D: 查询
  -> delete_record()           # V8-D: 软删除
  -> build_session_context()   # V8-C + V8-D: 构建 prompt context
  -> snapshot()               # 全局状态快照
```

## submit_user_text 为什么不自动保存

`submit_user_text()` 只创建 PendingMemory，不自动确认或持久化。这是因为：

1. **误抽取**：规则抽取可能产生不重要的候选
2. **用户意图**：用户可能随口说说，不想记住
3. **确认原则**：所有记忆必须经过用户（或代理）明确确认

## confirm_pending 为什么才写 Repository

`confirm_pending()` 才会：

1. 调用 `confirmation_service.confirm()` 确认
2. 将 `ConfirmedMemory` 转为 `MemoryRecord`
3. 写入 `repository.add(record)`

只有明确确认的记忆才会持久化。

## reject_pending 为什么不持久化

`reject_pending()` 只调用 `confirmation_service.reject()`，返回 `RejectedMemory`。

已拒绝的记忆不应该再次出现，所以不需要持久化。

## build_session_context 为什么只用 active records

只有 `ACTIVE` 状态的记录才会被格式化注入：

- **已删除**（DELETED）的记录不注入
- **待确认**（Pending）的记录不注入
- **已拒绝**（Rejected）的记录不注入

## 为什么 deleted 不注入

软删除（soft delete）的记录标记为 `DELETED` 状态，但仍然保留在 repository 中。

这些记录不应该再影响对话上下文，所以 `build_session_context()` 只读取 `list_active()`。

## 为什么 boundary 默认不注入

`BOUNDARY` 是用户"不要记住"的信号。如果默认注入，会让模型主动提醒用户违反了边界，造成尴尬。

只有显式开启 `include_boundary=True` 时才注入边界记忆。

## 为什么本阶段不接入 main.py

当前阶段：

1. **没有 UI 确认入口**：用户无法确认或拒绝记忆
2. **没有管理入口**：无法查看、编辑、删除已保存的记忆
3. **Runtime 需要验证**：先确保 runtime 本身工作正常

V8-E 提供完整的 runtime 能力，V8-F 会提供 CLI/Probe 管理入口，V8-G 才会接入主流程。

## 后续阶段规划

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入 ✅
V8-D：本地持久化 ✅
V8-E：Memory Runtime Service（当前）
V8-F：CLI / Probe 管理入口
V8-G：主流程接入
```

### V8-F：CLI / Probe 管理入口

提供 CLI 工具或 probe 脚本让用户：

- 查看所有 pending / active / rejected 记忆
- 手动 confirm 或 reject pending 记忆
- 删除不需要的 active 记忆
- 查看 session memory context 预览

### V8-G：主流程接入

将 MemoryRuntimeService 接入 AsyncDialogueController：

1. 每次用户输入后调用 `submit_user_text()`
2. 可选的 UI 让用户 confirm/reject pending 记忆
3. 确认后自动持久化
4. `build_session_context()` 结果传给 PromptRegistry

## 文件结构

```
app/brain/memory/
├── __init__.py            # 导出所有类型
├── confirmation.py         # V8-B: 确认类型、Store、Service
├── extractor.py           # V8-A: 候选记忆抽取
├── repository.py           # V8-D: LocalJsonMemoryRepository
├── runtime.py              # V8-E: MemoryRuntimeService
├── session_context.py      # V8-C: SessionMemoryContextBuilder
├── probe_cases.py         # V8-A: Probe 测试用例
└── types.py               # V8-A: MemoryCandidate 等基础类型

scripts/
└── probe_memory_runtime.py  # V8-E: Runtime probe 脚本
```
