# V8-I Memory Suggestion UI v0

## 目标

V8-I 的目标是让用户在桌面窗口里看到记忆候选，并可以点击"记住"或"不记"。

## 目标链路

```
memory.suggestions_detected
  -> DesktopViewModel 保存 pending suggestion
  -> DesktopWindow 显示记忆候选卡片
  -> 用户点击"记住"
  -> 发布 memory.confirm_requested
  -> MemorySuggestionController confirm_pending()
  -> repository.add()
  -> memory.confirmed
  -> UI 隐藏候选卡片

用户点击"不记"
  -> 发布 memory.reject_requested
  -> MemorySuggestionController reject_pending()
  -> memory.rejected
  -> UI 隐藏候选卡片
```

**V8-I 是 UI 确认入口，但仍然不能自动保存。**

## 为什么只展示第一条 suggestion

`suggestions_detected` 事件 payload 中的 `suggestions` 是一个列表，但 UI 只展示第一条。

原因：
1. **简化用户体验**：一次只处理一个候选，避免选择困难
2. **降低认知负担**：不需要用户一次消化多个候选
3. **降低实现复杂度**：UI 不需要处理多个候选的展示和状态

如果用户拒绝第一条，下一条会在下一次对话自然出现。

## 为什么 UI 不直接写 repository

ViewModel 和 Window 的职责是：
1. 展示状态
2. 转发用户交互事件

直接调用 repository 会：
1. 破坏分层架构
2. 使 UI 难以测试
3. 增加耦合

UI 只发布 `confirm_requested` 和 `reject_requested` 事件，由 `MemorySuggestionController` 处理实际的持久化逻辑。

## 为什么用户点击"记住"才发布 confirm_requested

系统不会自动确认记忆，必须用户明确同意后才能保存。

原因：
1. **用户自主权**：用户决定什么是重要的
2. **避免误存**：规则抽取可能产生不重要的候选
3. **隐私保护**：用户随口说说，不想被记住

## 为什么用户点击"不记"才发布 reject_requested

用户拒绝的记忆不会被保存，也不会再次出现。

## 为什么不展示 pending_id/evidence

`suggestions` payload 包含 `pending_id`、`evidence`、完整原始对话等，但 UI 只展示 `text`。

原因：
1. **pending_id**：内部标识，用户不需要知道
2. **evidence**：可能包含原始对话，隐私敏感
3. **完整原始对话**：太长，不适合卡片展示
4. **text**：简洁的摘要，适合展示

## 为什么本阶段不做完整记忆管理页

本阶段只做：
- 显示当前 pending suggestion
- 用户手动 confirm / reject

不做：
- 记忆管理页
- 记忆列表编辑页
- 历史记忆搜索
- 向量库
- SQLite

完整记忆管理是后续 V8-J 的目标。

## 后续 V8-J：记忆管理面板

V8-J 计划：
1. 查看所有 active memories
2. 删除不需要的记忆
3. 编辑记忆内容

## 文件结构

```
app/ui/
├── memory_suggestion.py    # V8-I: MemorySuggestionView + render_memory_suggestion_text

app/ui/view_model.py         # V8-I: 新增 memory_suggestion + memory_status_text 字段
                             # V8-I: handle_memory_suggestions_detected
                             # V8-I: handle_memory_confirmed
                             # V8-I: handle_memory_rejected
                             # V8-I: handle_memory_error

app/ui/window.py             # V8-I: 新增 memory suggestion widget
                             # V8-I: _on_memory_confirm_clicked
                             # V8-I: _on_memory_reject_clicked

app/main.py                  # V8-I: request_memory_confirm callback
                             # V8-I: request_memory_reject callback
                             # V8-I: 订阅 MEMORY_SUGGESTIONS_DETECTED
                             # V8-I: 订阅 MEMORY_CONFIRMED
                             # V8-I: 订阅 MEMORY_REJECTED
                             # V8-I: 订阅 MEMORY_ERROR

app/tests/
└── test_memory_suggestion_ui.py  # V8-I: ViewModel + Window tests

scripts/
└── probe_memory_suggestion_ui.py  # V8-I: probe script

docs/memory/
└── v8_i_memory_suggestion_ui_v0.md  # V8-I: 本文档
```
