# Skill Inventory — V3 Research

> 本文档调研 GitHub / 社区中存在的可复用公开 Skill，为 V3 及后续阶段的开发辅助流程提供参考。
>
> **背景**：项目 `docs/SKILLS.md` 已列出 Skill 需求清单，但这些是项目治理概念，不代表已安装或已实现。本文档对公开 Skill 进行调研分类，供后续决策参考。

---

## 调研目标

为 desktop-girlfriend 项目识别可复用 Skill，重点方向：

- Code review / architecture review
- Provider / API integration quality
- Prompt management
- Secret scanning / privacy guard
- Docs consistency
- Python 项目质量
- GitHub PR review
- Superpowers 等优秀工作流 Skill

---

## 安全审查原则

在调研和引入任何第三方 Skill 前，必须遵守以下原则：

| 原则 | 说明 |
|------|------|
| 不安装来源不明的 Skill | 只调研有明确来源的公开仓库 |
| 不执行未知脚本 | 第三方 Skill 只能先阅读内容，不直接运行 |
| 不引入会读取密钥的 Skill | 避免引入会自动读取 `.env` 或密钥的 Skill |
| 不引入会自动提交代码的 Skill | 避免引入会自动 `git commit/push` 的 Skill |
| 不引入会访问外部网络的 Skill，除非人工确认 | 网络访问需显式授权 |
| 第三方 Skill 只能先阅读，不允许直接运行 | 所有 Skill 内容必须人工审查后再考虑引入 |

---

## 候选 Skill 列表

### 1. Agent Skills 标准

| 项目 | 值 |
|------|-----|
| 名称 | Agent Skills |
| 链接 | https://github.com/agentskills/agentskills |
| 所属生态 | Anthropic（开放标准，已被 Claude Code、Cursor、VS Code 等采纳） |
| 入口文件 | `SKILL.md` |
| 包含脚本 | 视具体 Skill 而定 |
| 是否会执行命令 | 视具体 Skill 而定 |
| 是否会读写文件 | 视具体 Skill 而定 |
| 是否会访问网络 | 视具体 Skill 而定 |
| 是否涉及密钥/隐私 | 视具体 Skill 而定 |
| 适合本项目 | ✅ 是（Skill 格式标准） |
| 推荐结论 | **采用** |

**原因**：Agent Skills 是开放标准，定义了 `SKILL.md` 目录结构，被 Claude Code、Cursor、VS Code Copilot 等主流工具采纳。本项目 `docs/SKILLS.md` 中的需求可以直接以 Agent Skills 格式实现为项目自定义 Skill。

---

### 2. anthropics/skills — Claude Code 官方 Skill 库

| 项目 | 值 |
|------|-----|
| 名称 | anthropics/skills |
| 链接 | https://github.com/anthropics/skills |
| 所属生态 | Claude Code（Anthropic 官方） |
| 入口文件 | `SKILL.md` |
| 包含脚本 | 视具体 Skill 而定 |
| 是否会执行命令 | 视具体 Skill 而定 |
| 是否会读写文件 | 视具体 Skill 而定 |
| 是否会访问网络 | 视具体 Skill 而定 |
| 是否涉及密钥/隐私 | 视具体 Skill 而定 |
| 适合本项目 | 部分适用 |
| 推荐结论 | **借鉴** |

**仓库统计**：156k stars，18.4k forks，42 commits

#### 可直接采用的 Skill

| Skill 名称 | 用途 | 执行命令 | 读写文件 | 访问网络 | 涉及密钥 | 推荐 |
|-----------|------|---------|---------|---------|---------|------|
| `claude-api` | Claude API 参考（模型、价格、参数、流式、工具使用、MCP、缓存、token 计数、模型迁移） | ❌ | ❌ | ❌ | ❌ | **采用** — 纯文档，无执行，无网络，无密钥 |
| `skill-creator` | Skill 创建指南（如何创建、测试、优化 Skill） | ❌ | 部分（创建文件） | ❌ | ❌ | **采用** — 指导本项目 Skill 体系建设 |

#### 可借鉴的 Skill

| Skill 名称 | 用途 | 执行命令 | 读写文件 | 访问网络 | 涉及密钥 | 推荐 |
|-----------|------|---------|---------|---------|---------|------|
| `mcp-builder` | MCP Server 构建指南（Python FastMCP / TypeScript） | ❌（指导性质） | 部分（创建文件） | ❌ | ❌ | **借鉴** — V7 Agent/Tool Router 阶段可能需要 |
| `webapp-testing` | Playwright Web 测试（执行命令连接本地服务器） | ✅ | ✅ | ✅（本地） | ❌ | **不采用** — 本项目 UI 测试不需要引入 Playwright |
| `docx` | Word 文档处理 | ❌ | ✅ | ❌ | ❌ | **不采用** — V3 阶段不需要 |
| `pdf` | PDF 处理 | ❌ | ✅ | ❌ | ❌ | **不采用** — V3 阶段不需要 |
| `pptx` | PowerPoint 处理 | ❌ | ✅ | ❌ | ❌ | **不采用** — 当前不需要 |
| `xlsx` | Excel 处理 | ❌ | ✅ | ❌ | ❌ | **不采用** — 当前不需要 |

---

### 3. Claude Code 内置 Bundled Skills

Claude Code 自带以下 Bundled Skills（通过 `/skill-name` 调用）：

| Skill | 用途 | 是否适合本项目 |
|-------|------|--------------|
| `/code-review` | 代码审查 | ✅ 可直接使用 |
| `/verify` | 构建并运行 App 验证变更 | ✅ 可直接使用 |
| `/run` | 启动并驱动 App 查看变化 | ✅ 可直接使用 |
| `/debug` | 调试辅助 | ✅ 可直接使用 |
| `/batch` | 批量处理 | ⚠️ V3 阶段可能不需要 |
| `/claude-api` | Claude API 参考 | ✅ 等同于 `claude-api` Skill |

> 注意：Bundled Skills 不需要安装，直接可用。

---

### 4. Superpowers / 优秀外部 Skill

| 项目 | 值 |
|------|-----|
| 名称 | Superpowers / 优秀外部 Skill |
| 所属生态 | 视具体来源而定 |
| 适合本项目 | ✅ 是，适合作为个人开发辅助 |
| 推荐结论 | **可直接辅助使用，进入项目制度前需审查** |

**采用方式**：用于需求澄清、架构审查、代码审查、调试、测试策略和风险提示。若某个流程在项目中高频复用，再沉淀为项目自定义 Skill。

**边界**：不得让第三方 Skill 自动读取 `.env`、访问外部网络、提交代码、修改全局配置或越过 Roadmap 实现未来能力。

---

### 5. 本项目自定义 Skill 需求（从 docs/SKILLS.md 映射）

| Skill 名称 | 需求来源 | 建议实现方式 | 推荐 |
|-----------|----------|-------------|------|
| `architecture-guard` | SKILLS.md P0 | **项目自定义候选** — 守护分层架构边界 | **暂缓** — 先用 Superpowers + Review Guide |
| `code-quality-superpower` | SKILLS.md P0 | **项目自定义候选** — ruff/mypy/pytest 规范 | **暂缓** — 先用 Superpowers + CI/本地命令 |
| `docs-consistency-check` | SKILLS.md P0 | **项目自定义候选** — 文档与代码一致性检查 | **暂缓** — 先用 Superpowers + Review Guide |
| `minimax-execution-guard` | SKILLS.md P0 | **项目自定义候选** — MiniMax 执行边界守护 | **暂缓** — 先用 Superpowers + Gate |
| `provider-contract-check` | SKILLS.md P1 | **项目自定义** — Provider 接口契约检查 | **采用** — V3 Provider 实现后补充 |
| `prompt-registry` | SKILLS.md P1 | **项目自定义** — Prompt 集中管理 | **采用** — V3 Prompt Registry 实现后补充 |
| `usage-guard` | SKILLS.md P1 | **项目自定义** — API 使用量控制 | **采用** — V3 MiniMax 接入后补充 |
| `audio-pipeline-check` | SKILLS.md P2 | **项目自定义** — TTS/ASR 管线检查 | **借鉴** — V4+ 才需要 |
| `gesture-event-check` | SKILLS.md P2 | **项目自定义** — 手势事件规范 | **借鉴** — V5+ 才需要 |
| `avatar-driver-check` | SKILLS.md P2 | **项目自定义** — 数字人驱动规范 | **借鉴** — V6+ 才需要 |
| `tool-router-sandbox` | SKILLS.md P3 | **项目自定义** — 工具路由沙箱 | **借鉴** — V7 才需要 |
| `command-safety-check` | SKILLS.md P3 | **项目自定义** — 命令安全检查 | **借鉴** — V7 才需要 |
| `audit-log-check` | SKILLS.md P3 | **项目自定义** — 审计日志规范 | **借鉴** — V7 才需要 |

---

## 推荐采用项

| Skill | 来源 | 用途 | 说明 |
|-------|------|------|------|
| Agent Skills 格式 | agentskills.io | Skill 标准 | 开放标准，跨工具兼容，本项目 Skill 以此格式实现 |
| `claude-api` | anthropics/skills | API 参考 | 纯文档，无需执行，适合直接采用 |
| `skill-creator` | anthropics/skills | Skill 创建指导 | 指导本项目自定义 Skill 体系建设 |
| `/code-review` | Claude Code 内置 | 代码审查 | Bundled Skill，直接可用 |
| `/verify` | Claude Code 内置 | 验证变更 | Bundled Skill，直接可用 |
| `/run` | Claude Code 内置 | 运行 App | Bundled Skill，直接可用 |
| Superpowers | obra/superpowers | 需求澄清、计划、TDD、调试、审查、收尾 | 当前主辅助方案 |
| 项目自定义 P0 Skill | 本项目 | 架构守护/质量基线 | 暂缓；等 Superpowers 跑过真实流程后再决定是否沉淀 |

---

## 推荐借鉴项

| Skill | 来源 | 借鉴内容 |
|-------|------|---------|
| `mcp-builder` | anthropics/skills | MCP Server 构建模式，V7 可能需要 |
| `skill-creator` 的评估流程 | anthropics/skills | Skill 创建 → 测试 → 评估 → 迭代的工作流 |

---

## 不采用项

| Skill | 来源 | 不采用原因 |
|-------|------|-----------|
| `webapp-testing` | anthropics/skills | 需要 Playwright 和本地服务器，本项目 PySide6 不需要 |
| `docx` / `pdf` / `pptx` / `xlsx` | anthropics/skills | 当前阶段不需要文档处理能力 |
| 任何来源不明的第三方 Skill | — | 安全风险，未知执行行为 |

---

## 安全风险

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 第三方 Skill 执行未知命令 | 高 | 只阅读内容，不直接安装/运行；人工审查后再决定 |
| Skill 读取密钥或 .env | 高 | 禁止引入会自动读取密钥的 Skill |
| Skill 自动提交代码 | 高 | 禁止引入会自动 git commit/push 的 Skill |
| Skill 访问外部网络 | 中 | 需要人工确认网络访问需求 |
| Skill 读写任意文件 | 中 | 审查 Skill 读写范围，确保在项目目录内 |

---

## 对本项目的建议

### V3 阶段 Skill 策略

1. **直接使用 Claude Code Bundled Skills**（无需安装）：
   - `/code-review` — 代码审查
   - `/verify` — 验证变更
   - `/run` — 运行 App
   - `/claude-api` — API 参考

2. **采用 anthropics/skills 中的纯文档 Skill**：
   - `claude-api` — 以项目文件形式放在 `docs/skills/` 或直接参考
   - `skill-creator` — 指导本项目自定义 Skill 实现

3. **暂缓项目自定义 Skill**：
   - 不再优先自研 P0 Skill。
   - 先用 Superpowers 跑完 V3 的真实开发流程。
   - 如果某些检查反复出现，再沉淀为项目自定义 Skill。

4. **不创建 `.skills` 目录**（遵循项目约束）

### Skill 实现优先级

| 优先级 | Skill | 说明 |
|--------|-------|------|
| P0 | Superpowers | 当前主辅助方案，用于 V3 Gate 和开发流程把控 |
| P0 | `code-quality-superpower` | 暂缓；如 V3 实践证明需要，再沉淀 |
| P0 | `architecture-guard` | 暂缓；如 V3 实践证明需要，再沉淀 |
| P1 | `provider-contract-check` | Provider 接口契约，V3 MiniMax Provider 实现后 |
| P1 | `prompt-registry` | Prompt 集中管理，V3 Prompt Registry 实现后 |
| P1 | `minimax-execution-guard` | MiniMax 执行边界，V3 接入 API 后激活 |

---

## 关联文档

- [Skill 体系](./SKILLS.md) — 项目 Skill 需求清单
- [架构规范](./ARCHITECTURE.md) — 分层架构和核心原则
- [代码审查指南](./REVIEW_GUIDE.md) — Checkpoint Review 原则
- [Agent Skills 官网](https://agentskills.io) — 开放标准
- [anthropics/skills](https://github.com/anthropics/skills) — Claude Code 官方 Skill 库
