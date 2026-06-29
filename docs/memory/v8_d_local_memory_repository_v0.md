# V8-D Local Memory Repository v0

## 目标

V8-D 的目标是新增"本地记忆持久化仓储接口与 JSON 文件实现"。

目标链路：

```
ConfirmedMemory
  -> MemoryRecord
  -> LocalJsonMemoryRepository
  -> 可 list / get / delete / clear
```

**本阶段只做 repository，不接入真实聊天主流程。**

## MemoryRecord 与 MemoryCandidate 的区别

| 字段 | MemoryCandidate | MemoryRecord |
|------|----------------|--------------|
| id | 无 | 有（uuid） |
| evidence | 有 | **无** |
| confidence | 有 | 无 |
| status | 无 | 有（ACTIVE/DELETED） |
| created_at | 无 | 有 |
| updated_at | 无 | 有 |

MemoryRecord 是持久化层的 record，专为存储设计。

## 为什么不保存 evidence

1. **隐私**：evidence 包含完整对话原文，可能有更多敏感信息
2. **最小化**：已确认的记忆只需要 text，不需要原始证据
3. **安全**：万一 JSON 文件泄露，不会暴露额外上下文

## 为什么只保存 ConfirmedMemory

- **PendingMemory**：尚未确认，可能是误抽取，不应持久化
- **RejectedMemory**：用户明确拒绝，不应再出现
- **ConfirmedMemory**：用户已确认，可以安全地持久化

## 为什么 soft delete

物理删除（直接从文件中移除）会失去审计线索。soft delete 保留记录，可以：

1. 支持"最近删除"的恢复功能（未来）
2. 保留操作审计历史
3. 避免误删后无法追溯

## JSON 文件格式

```json
{
  "version": 1,
  "records": [
    {
      "id": "uuid-string",
      "kind": "preference",
      "importance": "medium",
      "text": "用户喜欢短回复。",
      "source": "deterministic_extractor",
      "created_at": "2026-01-01T00:00:00+00:00",
      "updated_at": "2026-01-01T00:00:00+00:00",
      "status": "active"
    }
  ]
}
```

## 为什么本阶段不接入 main.py

当前阶段：

1. **没有 UI 管理入口**：用户无法查看、编辑、删除已保存的记忆
2. **没有确认流程**：需要先有 UI 才能让用户确认哪些记忆要保存
3. **Repository 接口需要验证**：先确保 repository 本身工作正常

V8-D 只提供存储能力，V8-E 会接入确认流程，V8-F 才会有 UI 管理入口。

## 后续阶段规划

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入 ✅
V8-D：本地持久化（当前）
V8-E：Memory Runtime Service（接入确认流程）
V8-F：UI / CLI 管理入口
```

### V8-E：Memory Runtime Service

将 Repository 接入到确认流程中：

1. 记忆确认后自动写入 Repository
2. SessionMemoryContextBuilder 从 Repository 读取
3. 支持记忆的查看/编辑/删除

### V8-F：UI / CLI 管理入口

提供 UI 让用户：

- 查看所有已保存记忆
- 编辑记忆内容
- 删除不需要的记忆
- 恢复误删的记忆

## 文件结构

```
app/brain/memory/
├── __init__.py            # 导出所有类型
├── confirmation.py         # V8-B: 确认类型、Store、Service
├── extractor.py           # V8-A: 候选记忆抽取
├── repository.py           # V8-D: LocalJsonMemoryRepository
├── session_context.py      # V8-C: SessionMemoryContextBuilder
├── probe_cases.py         # V8-A: Probe 测试用例
└── types.py               # V8-A: MemoryCandidate 等基础类型

scripts/
└── probe_memory_repository.py  # V8-D: Repository probe 脚本
```
