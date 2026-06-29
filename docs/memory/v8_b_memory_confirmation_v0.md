# V8-B Memory Confirmation v0

## 目标

建立"记忆确认机制"的第一版：

```
MemoryCandidate
  -> PendingMemory
  -> 用户确认 / 拒绝 / 忽略
  -> ConfirmedMemory 或 RejectedMemory
```

本阶段**不接入主对话链路**，不自动影响 prompt，不持久化到磁盘。

核心原则：**候选记忆不能直接变成可用记忆。必须经过确认状态机。**

## 为什么不能自动保存 MemoryCandidate

V8-A 的 `DeterministicMemoryExtractor` 是保守的、基于规则的抽取器。它可能会：

1. 误抽取不重要的信息
2. 抽取用户不想记住的内容（即使有 boundary 保护）
3. 抽取不够准确的记忆

因此，**所有 MemoryCandidate 都必须经过用户（或系统代理）明确确认**，才能成为可用记忆。

## 状态说明

### PendingMemory

等待确认的候选记忆。用户（或系统）尚未决定是否保存。

```python
@dataclass(frozen=True)
class PendingMemory:
    id: str                    # 唯一标识符
    candidate: MemoryCandidate # 原始候选
    created_at: datetime       # 创建时间（UTC）
```

### ConfirmedMemory

已确认的记忆。用户同意保存，可用于后续对话。

```python
@dataclass(frozen=True)
class ConfirmedMemory:
    id: str
    candidate: MemoryCandidate
    created_at: datetime       # 首次创建时间
    confirmed_at: datetime      # 确认时间
```

### RejectedMemory

已拒绝的记忆。用户明确拒绝保存，不会成为可用记忆。

```python
@dataclass(frozen=True)
class RejectedMemory:
    id: str
    candidate: MemoryCandidate
    created_at: datetime
    rejected_at: datetime
    reason: str = ""            # 拒绝原因（可选）
```

## InMemory Store 说明

`InMemoryMemoryConfirmationStore` 是**本地临时状态**，仅存在于内存中：

- **不持久化**：进程结束，数据丢失
- **不写磁盘**：无 SQLite、无 JSON 文件
- **不联网**：纯本地操作
- **用途**：测试、本地 probe、UI 未接入前的过渡阶段

未来将替换为持久化 store（V8-D 阶段）。

## 用户确认机制

V8-B 不包含 UI，所以"用户确认/拒绝"通过 `MemoryConfirmationService` 方法模拟：

```python
service.submit_candidates(candidates)  # 提交候选
service.confirm(memory_id)               # 确认某个记忆
service.reject(memory_id, reason)        # 拒绝某个记忆
service.list_pending()                   # 查看待确认
service.list_confirmed()                 # 查看已确认
service.list_rejected()                  # 查看已拒绝
```

未来接入 UI 后，用户将通过界面按钮确认/拒绝。

## 隐私原则

1. **不自动保存**：MemoryCandidate 不会自动成为可用记忆
2. **边界保护**：boundary candidate 也可以进入 pending，用于后续让系统知道用户希望"不记住"
3. **用户控制**：所有记忆都必须经过用户（或代理）明确确认
4. **拒绝不恢复**：已拒绝的记忆不会再次出现

## 后续阶段规划

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制（当前）
V8-C：当前会话内记忆注入
V8-D：本地持久化
V8-E：记忆管理 UI
```

### V8-C：当前会话内记忆注入

将 ConfirmedMemory 注入到当前对话的 prompt context 中，实现短期会话记忆。

### V8-D：本地持久化

将 ConfirmedMemory 持久化到本地存储（如 SQLite），支持跨会话记忆。

### V8-E：记忆管理 UI

提供 UI 让用户查看、编辑、删除已确认的记忆，实现完整的记忆管理。

## 文件结构

```
app/brain/memory/
├── __init__.py          # 导出所有类型
├── confirmation.py      # V8-B: 确认类型、Store、Service
├── extractor.py         # V8-A: 候选记忆抽取
├── probe_cases.py       # V8-A: Probe 测试用例
└── types.py             # V8-A: MemoryCandidate 等基础类型

scripts/
└── probe_memory_confirmation.py  # V8-B: 确认机制 probe 脚本
```
