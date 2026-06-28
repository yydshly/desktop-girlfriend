# desktop-girlfriend

桌面 AI 伙伴原型项目 — 探索桌面人格表现、语音交互、手势交互、多模态感知、情绪陪伴和 MiniMax AI 能力集成。

> **它不是**：单纯聊天机器人、单纯桌宠、或第一阶段就要实现完整 3D AI 女友。
>
> **更准确的长期方向**：桌面人格壳 + Jarvis 式助手 + 情绪陪伴 + 多模态交互实验平台。

## Vision

> **北极星愿景图**是项目整体目标指导图，用于指导项目目标、产品定位、能力边界和路线图。

![Vision Board](./docs/assets/vision-board.png)

详见：[Vision Reference](./docs/VISION_REFERENCE.md)

## V1 工程初始化

当前为 **V1 工程初始化** 阶段，建立模块边界、事件契约和基础日志体系。

### 项目结构

```
app/
├── contracts/      # 事件、状态、payload 定义
├── core/           # EventBus、StateMachine、Config、Logging
├── ui/             # PySide6 窗口和 ViewModel
├── brain/          # LLM、Prompt、Provider（后续阶段）
├── expression/     # TTS、Avatar（后续阶段）
├── perception/     # ASR、手势（后续阶段）
├── memory/         # 记忆（后续阶段）
├── tools/          # Tool Router（后续阶段）
└── tests/         # 单元测试
```

### 环境要求

- **Python 3.11+**（项目 `pyproject.toml` 固定 `requires-python = ">=3.11"`）

### 安装

Windows 推荐使用 py launcher 创建虚拟环境：

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### 运行

```bash
python -m app.main
```

### 测试

```bash
ruff check .
mypy app
pytest -q
```

## 技术架构

详见：[架构规范](./docs/ARCHITECTURE.md)

| 模块 | 描述 |
|------|------|
| UI 层 | 桌面窗口、角色展示、用户界面 |
| Core 层 | EventBus、StateMachine、Config、应用生命周期 |
| Brain 层 | LLM、Prompt、MiniMax Provider、Agent 决策 |
| Expression 层 | TTS、语音播放、Avatar 表现、动作状态 |
| Perception 层 | ASR、麦克风、摄像头、手势识别 |
| Memory 层 | 短期上下文、长期记忆、会话历史 |
| Tool 层 | Tool Router、工具调用、权限控制、审计日志 |

## 核心原则

- **EventBus 驱动** — 跨层业务事件通过 EventBus
- **StateMachine 驱动** — 状态变更通过 StateMachine
- **Provider 化** — 外部服务封装为 Provider
- **Prompt Registry** — Prompt 集中管理

## 质量支撑体系

项目采用 **Skill / Superpowers** 质量支撑体系，确保开发过程规范可靠。

### 开发流程

- **Solo Developer Flow** — 单人开发流程，MiniMax 执行，ChatGPT 审查
- **Module Development Gate** — 新模块开发前必须通过的准入审查
- **Checkpoint Review** — 阶段完成后的轻量审查

详见：

- [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) — Solo Developer Flow 和 Module Development Gate
- [代码审查指南](./docs/REVIEW_GUIDE.md) — Checkpoint Review 和 Gate Checklist
- [Skill 体系](./docs/SKILLS.md) — 质量支撑体系

## 文档导航

### 愿景与定位
- [愿景图参考](./docs/VISION_REFERENCE.md) — 北极星愿景图
- [项目简介](./docs/PROJECT_BRIEF.md) — 项目概述和定位

### 开发规范
- [架构规范](./docs/ARCHITECTURE.md) — 分层架构和核心原则
- [代码审查指南](./docs/REVIEW_GUIDE.md) — Checkpoint Review 原则
- [MiniMax 执行规范](./docs/MINIMAX_EXECUTION.md) — Agent 执行边界
- [Skill 体系](./docs/SKILLS.md) — 质量支撑体系

### 项目管理
- [路线图](./docs/ROADMAP.md) — V0-V8 版本规划和里程碑

## 版本路线图

| 版本 | 阶段 |
|------|------|
| V0 | 文档治理与项目规则 |
| V1 | 工程初始化与 PySide6 最小桌面壳 |
| V2 | 状态机、事件总线与桌面角色状态 |
| V3 | MiniMax 文本对话与 TTS |
| V4 | 语音输入 ASR |
| V5 | MediaPipe 手势事件 |
| V6 | Avatar / 数字人表现增强 |
| V7 | Agent 工具能力 |
| V8 | 记忆与人格系统 |
