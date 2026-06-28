# desktop-girlfriend

桌面 AI 伙伴 — 一个具有情感陪伴价值的智能桌面助手。

## Vision

> **北极星愿景图**是项目整体目标指导图，用于指导项目目标、产品定位、能力边界和路线图。

![Vision Board](./docs/assets/vision-board.png)

详见：[Vision Reference](./docs/VISION_REFERENCE.md)

## 项目愿景

本项目旨在打造一个 **Jarvis 式** 的桌面 AI 伙伴，具备：

- 多模态交互能力（语音、视觉、手势等）
- 情绪陪伴和情感支持
- 个性化可替换形象
- 智能助手体验

## 技术架构

| 模块 | 描述 |
|------|------|
| UI 层 | 界面展示和用户交互 |
| Core 层 | 核心业务逻辑 |
| Brain 层 | AI 推理和语言处理 |
| Expression 层 | 表情和动作表达 |
| Perception 层 | 感知输入处理 |
| Memory 层 | 记忆存储 |
| Tool 层 | 工具路由和 Agent 能力 |

## 质量支撑体系

项目采用 **Skill / Superpowers** 质量支撑体系，确保开发过程规范可靠。

详见：[SKILLS](./docs/SKILLS.md)

### 核心规范

| 文档 | 说明 |
|------|------|
| [架构规范](./docs/ARCHITECTURE.md) | 分层架构和核心原则 |
| [代码审查指南](./docs/REVIEW_GUIDE.md) | PR 审查原则和安全检查 |
| [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) | Agent 执行边界和约束 |
| [Skill 体系](./docs/SKILLS.md) | 质量 Skill 分类和优先级 |

### 核心原则

- **EventBus 驱动** — 模块间通信通过 EventBus
- **StateMachine 驱动** — 状态变更通过 StateMachine
- **Provider 化** — 外部服务封装为 Provider
- **Prompt Registry** — Prompt 集中管理

## 文档导航

### 愿景与定位
- [愿景图参考](./docs/VISION_REFERENCE.md) — 北极星愿景图和核心目标
- [项目简介](./docs/PROJECT_BRIEF.md) — 项目概述和定位

### 开发规范
- [架构规范](./docs/ARCHITECTURE.md) — 分层架构和核心原则
- [代码审查指南](./docs/REVIEW_GUIDE.md) — PR 审查和安全检查
- [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) — Agent 执行边界
- [Skill 体系](./docs/SKILLS.md) — 质量支撑体系

### 项目管理
- [路线图](./docs/ROADMAP.md) — 版本规划和里程碑

## 版本路线图

| 版本 | 阶段 |
|------|------|
| V0 | 文档和工程初始化 |
| V1 | 桌面壳 |
| V2 | 文本 + 语音 |
| V3 | 语音输入 |
| V4 | 手势事件 |
| V5 | 角色表现增强 |
| V6 | 数字人 / 可替换形象 |
| V7 | Agent 能力 |
