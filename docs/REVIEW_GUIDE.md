# Review Guide

代码审查指南，确保项目质量一致性。

---

## 审查模式：Checkpoint Review

本项目采用轻量 Checkpoint Review，不是每个小改动都走正式 PR。

### 何时需要 Checkpoint Review

1. 合并 `main` 前
2. 进入新里程碑前
3. 接入高风险能力前（外部 API、摄像头、麦克风、真实人物素材、Tool Router）
4. 修改架构边界前

### 小改动不需要单独审查

- 文档修正、拼写错误修复
- 小型重构（保持行为不变）
- 内部模块调整（不涉及跨层边界）
- 测试用例补充

---

## Module Development Gate Checklist

每次进入新模块或新能力开发前，必须执行 Module Development Gate。

**未通过 Gate，不允许进入功能实现。**

详见：[MINIMAX_EXECUTION.md - Module Development Gate](./MINIMAX_EXECUTION.md#module-development-gate)

### 当前阶段确认

- [ ] 当前分支
- [ ] 当前里程碑
- [ ] 即将开发的模块
- [ ] Roadmap 对应版本
- [ ] 是否允许当前阶段开发

### 文档一致性检查

- [ ] README.md 是否包含当前阶段说明
- [ ] PROJECT_BRIEF.md 是否与目标一致
- [ ] ROADMAP.md 是否允许该模块
- [ ] ARCHITECTURE.md 是否定义模块边界
- [ ] SKILLS.md 是否定义所需质量支撑
- [ ] REVIEW_GUIDE.md 是否覆盖审查规则
- [ ] MINIMAX_EXECUTION.md 是否覆盖执行边界

### 架构边界检查

- [ ] 模块归属层级
- [ ] 输入事件
- [ ] 输出事件
- [ ] 是否需要 EventBus
- [ ] 是否需要 StateMachine
- [ ] 是否需要 Provider
- [ ] 是否需要 Prompt Registry
- [ ] 是否需要权限控制
- [ ] 禁止直接调用的模块

### 当前代码健康检查

必须运行：

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy app
python -m pytest -q
```

如涉及 UI，额外运行：

```bash
python -m app.main
```

### 风险检查

- [ ] 是否涉及外部 API
- [ ] 是否涉及 API Key
- [ ] 是否涉及摄像头
- [ ] 是否涉及麦克风
- [ ] 是否涉及真实人物素材
- [ ] 是否涉及本地命令执行
- [ ] 是否涉及长期记忆或用户隐私

### Gate 结论

- [ ] 是否允许进入开发
- [ ] 需要先补的文档
- [ ] 需要先修的代码
- [ ] 本模块开发边界

---

## 审查原则

1. **Architecture First** — 先检查架构边界，再看代码细节
2. **分层清晰** — 每一层只做本层职责内的事
3. **安全优先** — 隐私、密钥、权限必须严格审查
4. **文档同步** — 代码变更必须同步更新文档

### Superpowers 辅助审查

当前项目优先使用 Superpowers 做流程辅助：

- 新能力进入前，先用 `brainstorming` 澄清范围。
- 实现前，用 `writing-plans` 拆分小任务。
- 涉及功能代码时，优先按 `test-driven-development` 执行。
- 阶段完成前，用 `requesting-code-review` 和 `verification-before-completion` 做收尾。

Superpowers 的结论不能替代本文件的 Gate Checklist；二者不一致时，以项目文档和用户明确指令为准。

---

## 架构边界检查

### 必须遵守的分层规则

| 规则 | 说明 |
|------|------|
| UI 不直接调用 MiniMax | UI 层通过 Core/Brain 层间接调用 |
| `main.py` 不承载业务逻辑 | 只做应用入口和初始化 |
| 状态变化必须走 StateMachine | 禁止直接修改状态 |
| 感知输入事件通过 EventBus | 语音/手势等事件发布到总线 |
| 角色状态变化必须走 StateMachine | 禁止直接修改状态 |
| 外部 API 必须 Provider 化 | 禁止硬编码外部调用 |
| Prompt 必须集中管理 | 禁止散落在业务代码中 |

### 检查清单

- [ ] 新文件是否放在了正确的模块下？
- [ ] 是否引入了跨层直接调用？
- [ ] 是否有绕过 EventBus 的业务事件？
- [ ] 状态变更是否通过 StateMachine？
- [ ] 外部服务是否已 Provider 化？
- [ ] 是否新增 Prompt 但没有进入 Prompt Registry？
- [ ] 是否新增 Provider 但没有接口契约？

---

## 安全检查

### 敏感信息

- [ ] 不提交 `.env` 文件
- [ ] 不硬编码 API Key / Token
- [ ] 不在代码中存储敏感信息

### 隐私素材

涉及以下类型的素材必须显式说明：
- 摄像头采集
- 麦克风采集
- 真实人物照片/视频/语音

### 工具使用

- [ ] Agent 工具调用是否有授权边界？
- [ ] 命令执行是否有安全检查？

---

## Checkpoint Review 清单

审查重点：

- [ ] 是否遵守当前阶段目标？
- [ ] 是否违反架构分层？
- [ ] 是否绕过 EventBus / StateMachine 的边界？
- [ ] 是否引入未授权外部 API？
- [ ] 是否提交密钥或隐私素材？
- [ ] 是否新增 Prompt 但没有进入 Prompt Registry？
- [ ] 是否新增 Provider 但没有接口契约？
- [ ] 是否需要同步更新文档？
- [ ] 是否有测试命令和测试结果？

---

## Checkpoint Review Summary 模板

```markdown
## Checkpoint Review Summary

### 当前分支
<!-- 分支名 -->

### 修改文件
<!-- 列出所有修改文件 -->

### 核心修改
<!-- 概括本次改动 -->

### 文档一致性检查
<!-- 各文档是否已对齐 -->

### 是否写功能代码
<!-- 是 / 否 -->

### 是否涉及敏感信息
<!-- 是 / 否 -->

### 风险点
<!-- 说明可能的风险 -->

### 下一步建议
<!-- 下一步计划 -->
```

---

## 关联文档

- [架构规范](./ARCHITECTURE.md)
- [Skill 体系](./SKILLS.md)
- [MiniMax 执行规范](./MINIMAX_EXECUTION.md)
