# Roadmap

## Vision-driven Roadmap

本路线图基于北极星愿景图制定，确保每个版本都为最终愿景服务。

> **愿景图**：[Vision Reference](./VISION_REFERENCE.md)

> **注意**：当前阶段（V0）不要实现 TTS、ASR、手势识别、LivePortrait、Agent 工具调用。

---

## Module Development Gate

**每个版本进入开发前，必须先通过 Module Development Gate。**

Gate 通过后才允许进入功能实现。详见：

- [MINIMAX_EXECUTION.md - Module Development Gate](./MINIMAX_EXECUTION.md#module-development-gate)
- [Review Guide - Module Development Gate Checklist](./REVIEW_GUIDE.md#module-development-gate-checklist)

---

## 版本规划

### V0 — 文档治理与项目规则

**目标**：建立项目基础规范和文档体系

- [x] 愿景图纳入文档
- [x] 项目文档体系
- [x] Skill / Superpowers 质量支撑体系
- [x] Solo Developer Flow 规范
- [ ] 工程脚手架（留待 V1）

**交付物**：文档结构、愿景参考、项目规则

---

### V1 — 工程初始化与 PySide6 最小桌面壳

**目标**：建立桌面应用框架

- [ ] PySide6 窗口应用
- [ ] 基础 UI 布局
- [ ] 应用入口（main.py）
- [ ] 最小可运行壳

**技术模块**：UI 层 + Core 层

---

### V2 — 状态机、事件总线与桌面角色状态

**目标**：建立核心基础设施

- [ ] EventBus 实现
- [ ] StateMachine 实现
- [ ] 角色状态定义
- [ ] 基础事件发布/订阅

**技术模块**：Core 层

---

### V3 — MiniMax 文本对话与 TTS

**目标**：实现基础对话能力

- [ ] MiniMax Provider 实现
- [ ] 文本对话界面
- [ ] TTS 语音输出
- [ ] Prompt Registry 初始化

**技术模块**：Brain 层 + Expression 层

---

### V4 — 语音输入 ASR

**目标**：实现语音交互

- [ ] ASR 集成
- [ ] 语音对话模式
- [ ] 语音唤醒
- [ ] 多轮对话支持

**技术模块**：Perception 层

---

### V5 — MediaPipe 手势事件

**目标**：实现手势交互

- [ ] MediaPipe 手势识别
- [ ] 手势事件响应
- [ ] 手势快捷操作
- [ ] 触摸/鼠标手势

**技术模块**：Perception 层

---

### V6 — Avatar / 数字人表现增强

**目标**：增强角色表现力

- [ ] Avatar 驱动
- [ ] 表情系统
- [ ] 动作动画
- [ ] 情绪反馈

**技术模块**：Expression 层

---

### V7 — Agent 工具能力

**目标**：实现完整 AI Agent

- [ ] Tool Router 实现
- [ ] 自主任务规划
- [ ] 工具使用能力
- [ ] 主动服务

**技术模块**：Tool 层 + Brain 层

---

### V8 — 记忆与人格系统

**目标**：实现长期陪伴能力

- [ ] Memory Layer 实现
- [ ] 长期记忆存储
- [ ] 人格系统
- [ ] 个性化学习

**技术模块**：Memory 层

---

## 技术模块与版本映射

| 模块 | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V8 |
|------|----|----|----|----|----|----|----|----|
| UI 层 | ● | ● | ● | ● | ● | ● | ● | ● |
| Core 层 | ● | ● | ● | ● | ● | ● | ● | ● |
| Brain 层 |   |   | ● | ● | ● | ● | ● | ● |
| Expression 层 |   |   | ● |   |   | ● | ● | ● |
| Perception 层 |   |   |   | ● | ● |   |   | ● |
| Memory 层 |   |   |   |   |   |   |   | ● |
| Tool 层 |   |   |   |   |   |   | ● | ● |

---

## 关联文档

- [愿景图参考](./VISION_REFERENCE.md)
- [项目简介](./PROJECT_BRIEF.md)
- [架构规范](./ARCHITECTURE.md)
