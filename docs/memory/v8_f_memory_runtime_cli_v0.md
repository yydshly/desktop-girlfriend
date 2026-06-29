# V8-F Memory Runtime CLI v0

## 目标

V8-F 的目标新增一个本地 CLI 管理入口，用来验证完整 memory runtime 闭环。

CLI 不是 UI，不接入真实聊天主流程。

## CLI 是调试/管理入口，不是正式 UI

V8-F CLI 是本地调试 / probe 入口，不是用户正式 UI。

设计原则：

- 不联网
- 不调用 LLM
- 不打开麦克风
- 不接入 main.py
- 不自动读取真实聊天
- 不自动保存用户聊天
- 所有文件路径必须显式传入
- 测试和 probe 必须使用 tmp_path / tempfile

## 为什么 --path 必须显式传入

所有命令必须显式传 `--path <json_path>`。不提供时报错。

这是设计选择，确保：
1. 用户明确知道在操作哪个文件
2. 不会误操作真实用户数据
3. 测试可以完全隔离

## 哪些命令跨进程有效

V8-F CLI 命令分两类：

### 持久化可跨进程命令

这些命令操作 repository，文件持久化，跨进程有效：

- `list-active` — 读取 repository.list_active()
- `list-all` — 读取 repository.list_all()
- `delete <record_id>` — 调用 runtime.delete_record()
- `context` — 调用 runtime.build_session_context()
- `clear` — 调用 repository.clear()

### 单进程调试命令

这些命令操作 in-memory confirmation store，进程重启后丢失：

- `submit <text>` — 提交用户文本生成 pending
- `list-pending` — 列出当前进程内的 pending
- `confirm <pending_id>` — 确认单个 pending
- `reject <pending_id>` — 拒绝单个 pending
- `snapshot` — 打印 pending/active/rejected 数量

## 为什么 pending/rejected 不跨进程

`pending` 和 `rejected` 状态存储在 `InMemoryMemoryConfirmationStore` 中。

这是 V8-B 的设计选择 — confirmation store 是有意设计为内存态的：
1. pending 是临时状态，不需要持久化
2. rejection 不需要持久化
3. 避免引入 session file 的复杂性

V8-F 不引入 session file，保持简单。

## demo 子命令如何验证完整闭环

`demo` 子命令在同一进程内完成完整闭环：

```
1. submit "我喜欢你回复短一点。"
2. submit "我女朋友叫红红，这件事不要记住。"
3. confirm 第一条非 boundary pending
4. reject boundary pending
5. list active
6. build context
7. delete active
8. build context again
```

demo 输出摘要数字，不打印完整敏感文本。

## 为什么不接入 main.py

CLI 是调试工具，不是集成点。接入 main.py 会：

1. 引入不必要的依赖
2. 难以隔离测试
3. 可能影响真实聊天流程

V8-G 才会接入主流程。

## 为什么不自动保存聊天

V8-F CLI 只接受显式 `submit <text>` 命令，不会自动读取聊天或自动保存。

自动保存需要：
1. UI 确认入口
2. 隐私考量
3. 主流程集成

这些属于 V8-G 及后续阶段。

## 后续 V8-G 主流程接入计划

```
V8-A：候选记忆抽取 ✅
V8-B：记忆确认/拒绝机制 ✅
V8-C：当前会话内记忆注入 ✅
V8-D：本地持久化 ✅
V8-E：Memory Runtime Service ✅
V8-F：CLI / Probe 管理入口（当前）
V8-G：主流程接入
```

V8-G 计划：
1. UI 让用户 confirm/reject pending 记忆
2. 确认后自动持久化
3. `build_session_context()` 结果传给 PromptRegistry
4. 接入 AsyncDialogueController

## 文件结构

```
app/brain/memory/
├── __init__.py            # V8-F: 导出 build_parser, run_memory_cli
├── cli.py                 # V8-F: Memory CLI 实现

scripts/
├── memory_cli.py          # V8-F: CLI 薄包装入口
└── probe_memory_cli.py    # V8-F: CLI probe 脚本

app/tests/
└── test_memory_cli.py     # V8-F: CLI 测试

docs/memory/
└── v8_f_memory_runtime_cli_v0.md
```
