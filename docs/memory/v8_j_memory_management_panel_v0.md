# V8-J Memory Management Panel v0

## 目标

V8-J 的目标是让用户可以在 UI 中查看和删除已经保存的 active memories。

## 目标链路

```
用户点击"记忆"
  -> 发布 memory.list_requested
  -> MemorySuggestionController 读取 repository active records
  -> 发布 memory.listed
  -> DesktopViewModel 保存 active memory views
  -> DesktopWindow 显示轻量记忆面板
  -> 用户点击删除某条
  -> 发布 memory.delete_requested
  -> repository soft delete
  -> 发布 memory.deleted
  -> UI 刷新列表
```

**本阶段只做：查看 active memories、删除 active memory、刷新记忆列表。**

## 为什么只做查看和删除

V8-J 专注于最基础的记忆管理功能：

1. **查看**：用户可以确认哪些记忆被保存了
2. **删除**：用户可以删除不需要的记忆

不做编辑功能，因为：
1. 编辑可能引入数据不一致
2. 简化 V0 实现
3. 用户可以删除后重新确认来"编辑"

## 为什么删除是 soft delete

`delete_record()` 调用 `repository.delete()`，这是 soft delete：

1. **可追溯**：deleted 记录仍然存在于数据库中
2. **可恢复**：如果需要，可以实现恢复功能
3. **不泄露**：list_active_records() 不会返回已删除记录

## 为什么 panel 不展示 record_id/evidence/source

record payload 只展示用户关心的内容：

1. **record_id**：内部标识，用户不需要知道
2. **evidence**：原始对话内容，隐私敏感
3. **source**：内部来源信息，用户不需要知道

只展示：
- kind（记忆类型）
- importance（重要性）
- text（记忆文本）
- created_at/updated_at（时间戳）

## 为什么 V0 只支持删除第一条

V0 的"删除第一条"是简化实现：

1. **降低复杂度**：不需要实现每条记录的选择/删除 UI
2. **满足基础需求**：用户可以删除不需要的记忆
3. **为后续扩展留空间**：V8-K 可以实现多条删除

## 后续 V8-K：管理面板增强

V8-K 计划：
1. 查看所有 memories（包括 deleted）
2. 多条选择删除
3. 可选编辑记忆内容
4. 按 kind 或 importance 筛选

## 文件结构

```
app/contracts/
├── events.py              # V8-J: 新增 MEMORY_LIST_REQUESTED, MEMORY_LISTED,
│                           #       MEMORY_DELETE_REQUESTED, MEMORY_DELETED
├── payloads.py            # V8-J: 新增 MemoryRecordPayload, MemoryListedPayload,
│                           #       MemoryListRequestedPayload, MemoryDeleteRequestedPayload,
│                           #       MemoryDeletedPayload

app/brain/memory/
└── controller.py          # V8-J: 新增 _on_memory_list_requested,
                            #       _on_memory_delete_requested

app/ui/
├── memory_record_view.py   # V8-J: MemoryRecordView + render_memory_record_text

app/ui/view_model.py        # V8-J: 新增 memory_records, memory_panel_visible
                            # V8-J: handle_memory_listed, handle_memory_deleted
                            # V8-J: toggle_memory_panel

app/ui/window.py            # V8-J: 新增"记忆"按钮和 memory panel widget
                            # V8-J: _on_memory_panel_clicked
                            # V8-J: _on_memory_delete_first_clicked

app/main.py                  # V8-J: request_memory_list, request_memory_delete
                            # V8-J: 订阅 MEMORY_LISTED, MEMORY_DELETED

app/tests/
└── test_memory_management_ui.py  # V8-J: ViewModel tests

scripts/
└── probe_memory_management_ui.py  # V8-J: probe script

docs/memory/
└── v8_j_memory_management_panel_v0.md  # V8-J: 本文档
```
