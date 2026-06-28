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

它们不实现业务功能。当前阶段允许直接使用可信的内置 Skill、Superpowers 等优秀 Skill 辅助开发，但项目自定义 Skill 只有在仓库中真实创建、验证并纳入流程后，才视为正式质量机制。

---

## 当前状态

> 本节说明本项目 Skill 体系的当前成熟度。

### Skill 来源分类

| 来源 | 说明 | 示例 |
|------|------|------|
| **内置 Skill** | 当前工具内置，直接作为开发辅助使用 | code review、verify、debug |
| **优秀外部 Skill** | 来源明确、内容可审查的 Skill，可直接用于个人辅助 | Superpowers、公开纯文档 Skill |
| **项目自定义 Skill** | 根据本项目架构和阶段规则沉淀的 Skill | `desktop-girlfriend-guard`、`architecture-guard` |

### 当前成熟度

| 类别 | 状态 | 说明 |
|------|------|------|
| 内置 Skill | ✅ 可用 | 可立即用于代码审查、验证、调试和总结风险 |
| Superpowers / 优秀外部 Skill | ✅ 可作为个人辅助使用 | 先阅读或使用可信入口，不让其自动读取密钥、联网、提交代码 |
| 公开 Skill 借鉴 | ⚠️ 按需研究 | 详见 [SKILL_INVENTORY.md](./SKILL_INVENTORY.md) |
| 项目自定义 P0 Skill | ✅ 基线已创建 | `.codex/skills/desktop-girlfriend-guard/SKILL.md` 覆盖架构、质量、文档一致性和 V3 Gate；更细分 Skill 后续再拆 |
| 项目自定义 P1 Skill | ❌ 尚未实现 | V3 MiniMax 接入后实现 |
| 项目自定义 P2/P3 Skill | ❌ 尚未实现 | V4+ 阶段逐步实现 |

### 当前使用原则

当前可以直接使用 Skill 辅助开发，但遵循以下边界：

- **先用作顾问**：用 Skill 做需求澄清、架构检查、代码审查、测试建议和风险提示。
- **再沉淀为制度**：只有高频、稳定、可复用的流程才抽成项目自定义 Skill。
- **不替代基础质量工具**：`ruff`、`mypy`、`pytest`、CI 仍是质量底座。
- **不放大权限**：第三方 Skill 不得自动读取 `.env`、访问外部网络、提交代码或修改全局配置。
- **不跨阶段实现**：Skill 可以提醒 V3/V4/V5 的边界，但不能替项目越过 Roadmap。

### V3 Skill 策略

- 继续使用内置 Skill 和 Superpowers 辅助代码审查、验证和风险分析。
- 借鉴可信公开 Skill 中的纯文档工作流。
- 当前先使用项目级聚合 Skill：`desktop-girlfriend-guard`。
- 后续从聚合 Guard 中拆分高频专项 Skill：`architecture-guard`、`code-quality-superpower`、`docs-consistency-check`。
- 在项目自定义 Skill 建好之前，相关检查以 Review Guide checklist 为准。
- 当前仓库已提供 `desktop-girlfriend-guard` 作为项目级聚合 Skill；若当前工具尚未自动发现，可按路径手动引用其 `SKILL.md`。

详见：[SKILL_INVENTORY.md](./SKILL_INVENTORY.md)

---

## Skill 分类

### 1. 架构守护类 Skill

| Skill | 描述 |
|-------|------|
| `desktop-girlfriend-guard` | 项目级聚合 Guard，覆盖当前阶段、架构边界、质量命令、V3 Gate 和提交卫生 |
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

## 优先级

### P0 — 当前优先沉淀

- `code-quality-superpower` — 代码质量基线
- `architecture-guard` — 架构边界守护
- `docs-consistency-check` — 文档一致性
- `minimax-execution-guard` — MiniMax 执行边界

### P1 — 接 MiniMax 前

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
