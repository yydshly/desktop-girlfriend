# Skills / Superpowers

> Skill / Superpowers 是项目的质量支撑体系，不是业务功能。

## 定位

Skills 是项目开发过程中的质量增强层，负责：

- 守护架构边界
- 保证代码质量
- 维护文档一致性
- 管理 Prompt 资产
- 保障安全与隐私

它们不实现业务功能，而是确保业务功能的开发过程规范可靠。

---

## Skill 分类

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

## 优先级

### P0 — 当前必须

- `code-quality-superpower` — 代码质量基线
- `architecture-guard` — 架构边界守护
- `docs-consistency-check` — 文档一致性
- `minimax-execution-guard` — MiniMax 执行边界

### P1 — 接 MiniMax 前

- `prompt-registry` — Prompt 集中管理
- `provider-contract-check` — Provider 接口契约
- `usage-guard` — API 使用量控制

### P2 — 接语音/手势/数字人 前

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
