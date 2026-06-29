# V8-C Session Memory Injection v0

## 目标

V8-C 的目标是实现"当前会话内 confirmed memory 的 prompt 注入能力"。

链路是：

```
ConfirmedMemory
  -> SessionMemoryContextBuilder
  -> PromptRegistry 可选注入
  -> ChatRequest messages 中出现一段 session memory context
```

**本阶段仍然不是长期记忆。**

## 为什么只注入 ConfirmedMemory

只有经过用户确认的记忆才会被注入：

- **PendingMemory**：尚未确认，可能是误抽取，不应影响对话
- **RejectedMemory**：用户明确拒绝，不应再出现
- **ConfirmedMemory**：用户已确认，可以安全地用于理解对话上下文

## 为什么 context 不能说"我记得"

禁止使用"我记得……"这类表达，因为这会让模型主动暴露记忆，容易让用户产生被监控感。

V8-C 使用的安全表达是：

```
已确认的用户会话记忆，仅用于理解当前对话，不要主动逐条复述：
- 用户喜欢短回复。
- 用户正在做一个桌面女友项目。
```

## 为什么默认排除 BOUNDARY

BOUNDARY 是用户"不要记住"的信号。默认注入 BOUNDARY 会让模型主动提醒用户违反了边界，造成尴尬。

只有在用户主动查询"你记住了什么"时，才应该展示 BOUNDARY 信息。

## Prompt message 顺序

```
1. system persona prompt (小云的系统提示)
2. system memory_context (已确认的会话记忆)  <-- 新增
3. user history turn(s) (历史对话)
4. user current_message (当前用户输入)
```

## 为什么 main.py 暂不接入

当前阶段：

1. **没有 UI 确认入口**：用户无法确认或拒绝记忆
2. **没有持久化管理入口**：无法查看、编辑、删除已确认的记忆
3. **V8-D 尚未完成**：没有本地持久化，进程重启后记忆全失

V8-C 只预留注入能力，让未来的 V8-D/V8-E 可以安全接入，而不会默认影响当前对话。

## 隐私原则

1. **不自动注入**：所有注入必须经过 MemoryConfirmationService 确认
2. **用户控制**：只有 ConfirmedMemory 才会被格式化注入
3. **最小化暴露**：context 使用安全表达，不暴露证据细节
4. **可关闭**：通过 `include_boundary=False` 可排除边界类记忆

## 后续阶段规划

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入（当前）
V8-D：本地持久化
V8-E：记忆管理 UI
```

### V8-D：本地持久化

将 ConfirmedMemory 持久化到本地存储（SQLite），支持：

- 查看所有已确认记忆
- 编辑记忆内容
- 删除不需要的记忆
- 隐私边界管理

### V8-E：记忆管理 UI

提供 UI 让用户：

- 查看待确认记忆（PendingMemory）
- 确认或拒绝候选记忆
- 管理已确认记忆（查看/编辑/删除）
- 设置隐私边界

## 文件结构

```
app/brain/memory/
├── __init__.py            # 导出所有类型
├── confirmation.py         # V8-B: 确认类型、Store、Service
├── extractor.py            # V8-A: 候选记忆抽取
├── session_context.py      # V8-C: SessionMemoryContextBuilder
├── probe_cases.py          # V8-A: Probe 测试用例
└── types.py                # V8-A: MemoryCandidate 等基础类型

scripts/
└── probe_session_memory_injection.py  # V8-C: 注入 probe 脚本
```
