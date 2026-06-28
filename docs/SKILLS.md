# Skills / Superpowers

> Skill / Superpowers 是项目的开发辅助层，不是业务功能，也不是 CI / 测试 / 人工审查的替代品。

## 定位

Skills 是项目开发过程中的质量增强层，用于：

- 约束 MiniMax 执行边界
- 辅助代码审查
- 保证文档一致性
- 管理 Prompt 资产
- 保护 API Key 和隐私素材
- 降低单人开发审查成本
- 把架构纪律转化为可重复执行的流程
- 复用优秀外部 Skill（如 Superpowers）中的成熟工作流

它们不实现业务功能。当前阶段以 **Superpowers** 作为主要开发方法论辅助，用于需求澄清、计划拆解、TDD、调试、代码审查和分支收尾。项目自定义 Skill 暂不作为主线；只有在真实使用中发现稳定、高频、项目特有的流程后，再考虑沉淀。

---

## 当前状态

> 本节说明本项目 Skill 体系的当前成熟度。

### Skill 来源分类

| 来源 | 说明 | 示例 |
|------|------|------|
| **Superpowers** | 当前主开发工作流插件，优先使用 | `brainstorming`、`writing-plans`、`test-driven-development`、`requesting-code-review` |
| **内置 Skill** | 当前工具内置，作为补充辅助使用 | code review、verify、debug |
| **优秀外部 Skill** | 来源明确、内容可审查的 Skill，可按需引入 | 公开纯文档 Skill |
| **项目自定义 Skill** | 暂缓，等项目流程稳定后再沉淀 | `architecture-guard`、`code-quality-superpower` |

### 当前成熟度

| 类别 | 状态 | 说明 |
|------|------|------|
| Superpowers | ✅ 已作为主辅助方案 | 通过 Codex App 插件安装；新会话/重启后生效，用于项目把控和开发流程 |
| 内置 Skill | ✅ 可用 | 可用于补充代码审查、验证、调试和总结风险 |
| 其他优秀外部 Skill | ⚠️ 按需引入 | 先阅读或使用可信入口，不让其自动读取密钥、联网、提交代码 |
| 公开 Skill 借鉴 | ⚠️ 按需研究 | 详见 [SKILL_INVENTORY.md](./SKILL_INVENTORY.md) |
| 项目自定义 Skill | ⏸️ 暂缓 | 不再优先自研，避免和 Superpowers 工作流重复；后续只沉淀项目特有规则 |

### 当前使用原则

当前使用 Superpowers / Skill 辅助开发，但遵循以下边界：

- **Superpowers 优先**：需求不清时先用 brainstorming；进入实现前用 writing-plans；写功能时优先按 TDD；阶段结束前做 code review / verification。
- **项目规则优先级更高**：Roadmap、Architecture、Review Guide、MiniMax Execution 的阶段边界仍然必须遵守。
- **再沉淀为制度**：只有高频、稳定、项目特有的流程才抽成项目自定义 Skill。
- **不替代基础质量工具**：`ruff`、`mypy`、`pytest`、CI 仍是质量底座。
- **不放大权限**：第三方 Skill 不得自动读取 `.env`、访问外部网络、提交代码或修改全局配置。
- **不跨阶段实现**：Skill 可以提醒 V3/V4/V5 的边界，但不能替项目越过 Roadmap。

### V3 Skill 策略

- 以 Superpowers 作为主工作流辅助。
- V3 MiniMax Provider 进入实现前，先完成 brainstorming / writing-plans / Module Development Gate。
- 实现阶段优先遵循 test-driven-development。
- 阶段收尾使用 requesting-code-review / verification-before-completion。
- 项目自定义 Skill 暂不继续扩展；相关检查以 Superpowers + Review Guide checklist 为准。

详见：[SKILL_INVENTORY.md](./SKILL_INVENTORY.md)

---

## Superpowers 对应项目场景

| Superpowers 能力 | 本项目使用场景 |
|------------------|----------------|
| `brainstorming` | V3/V4 等新能力进入前，澄清目标、边界和非目标 |
| `writing-plans` | 将 V3 MiniMax Provider、Prompt Registry、TTS 等拆成小任务 |
| `test-driven-development` | Provider、Prompt Registry、State/Event 契约变更 |
| `systematic-debugging` | 启动失败、环境问题、事件链路异常 |
| `requesting-code-review` | Gate 通过前、阶段完成前、接入外部 API 前 |
| `verification-before-completion` | 宣称完成前复核测试、运行和文档一致性 |

---

## 后续可能沉淀的项目 Skill

### 1. 架构守护类 Skill

| Skill | 描述 |
|-------|------|
| `architecture-guard` | 守护分层架构边界，确保各层职责清晰 |

### 2. 代码质量类 Skill

| Skill | 描述 |
|-------|------|
| `code-quality-superpower` | 代码风格检查、lint、格式化 |
| `provider-contract-check` | 外部服务 Provider 接口契约检查 |

### 3. 文档一致性类 Skill

| Skill | 描述 |
|-------|------|
| `docs-consistency-check` | 文档与代码一致性检查 |

### 4. Prompt 管理类 Skill

| Skill | 描述 |
|-------|------|
| `prompt-registry` | 集中管理所有 Prompt 资产 |

### 5. 安全与隐私类 Skill

| Skill | 描述 |
|-------|------|
| `minimax-execution-guard` | MiniMax Agent 执行边界守护 |
| `usage-guard` | API 使用量守护 |
| `safety-privacy-guard` | 安全与隐私合规检查 |

### 6. 多模态能力类 Skill

| Skill | 描述 |
|-------|------|
| `audio-pipeline-check` | 音频管线检查（TTS/ASR） |
| `gesture-event-check` | 手势事件处理检查 |
| `avatar-driver-check` | 数字人驱动检查 |

### 7. Agent 工具安全类 Skill

| Skill | 描述 |
|-------|------|
| `tool-router-sandbox` | 工具路由沙箱 |
| `command-safety-check` | 命令安全检查 |
| `audit-log-check` | 审计日志检查 |

---

## 项目自定义 Skill 优先级

### 暂缓自研

当前不再优先开发项目自定义 Skill。先使用 Superpowers 跑过 V3 的真实开发流程，再根据重复出现的问题决定是否沉淀：

- `architecture-guard` — 架构边界守护
- `docs-consistency-check` — 文档一致性
- `provider-contract-check` — Provider 接口契约
- `prompt-registry` — Prompt 集中管理

### 接 MiniMax 前需要重点关注

- `prompt-registry` — Prompt 集中管理
- `provider-contract-check` — Provider 接口契约
- `usage-guard` — API 使用量控制

### P2 — 接语音 / 手势 / 数字人 前

- `audio-pipeline-check` — 音频管线规范
- `gesture-event-check` — 手势事件规范
- `avatar-driver-check` — 数字人驱动规范

### P3 — 接 Agent 工具 前

- `tool-router-sandbox` — 工具路由沙箱
- `command-safety-check` — 命令安全检查
- `audit-log-check` — 审计日志规范

---

## 关联文档

- [架构规范](./ARCHITECTURE.md)
- [代码审查指南](./REVIEW_GUIDE.md)
- [MiniMax 执行规范](./MINIMAX_EXECUTION.md)
