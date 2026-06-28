# Project Brief

## 项目概述

Desktop Girlfriend 是一个桌面 AI 伙伴**原型项目**，目标是探索：

- 桌面人格表现
- 语音交互
- 手势交互
- 多模态感知
- 情绪陪伴
- MiniMax AI 能力集成

### 它不是什么

- **不是**单纯聊天机器人
- **不是**单纯桌宠
- **不是**第一阶段就要实现完整 3D AI 女友

### 更准确的长期方向

桌面人格壳 + Jarvis 式助手 + 情绪陪伴 + 多模态交互实验平台

## 产品定位

- **核心价值**：情绪陪伴 + 智能助手
- **目标用户**：需要桌面陪伴和交互体验的用户
- **产品形态**：桌面端应用程序
- **交互方式**：多模态（语音、手势、文本）

## 核心能力

1. **AI 伙伴** — 具有情感理解和生成能力的智能实体
2. **多模态交互** — 支持语音对话、手势识别、视觉感知
3. **个性化形象** — 可定制的数字人形象
4. **主动服务** — 智能提醒、日程管理、信息查询

## Vision Reference

> 本项目的所有决策和规划都围绕北极星愿景图展开。

**愿景图**：[Vision Reference](./VISION_REFERENCE.md)

愿景图定义了：
- 项目核心目标和北极星指标
- 技术架构模块划分
- 版本路线图阶段映射

![Vision Board](./assets/vision-board.png)

### 愿景图定位说明

愿景图是：
- 产品愿景参考
- 目标体验参考
- 路线图方向参考
- 产品气质参考

愿景图不是：
- 技术规格书
- 第一阶段验收标准
- 必须完全复刻的 UI 图
- 立即要实现的功能清单

## 技术栈

- **UI**: PySide6 / Qt
- **AI**: 大语言模型 API（MiniMax 等）
- **语音**: TTS / STT（后续阶段）
- **视觉**: 图像处理、手势识别（后续阶段）

## 技术架构

详见：[架构规范](./ARCHITECTURE.md)

| 层级 | 职责 |
|------|------|
| UI Layer | 桌面窗口、角色展示、用户界面 |
| Core Layer | EventBus、StateMachine、Config、应用生命周期 |
| Brain Layer | LLM、Prompt、MiniMax Provider、Agent 决策 |
| Expression Layer | TTS、语音播放、Avatar 表现、动作状态 |
| Perception Layer | ASR、麦克风、摄像头、手势识别 |
| Memory Layer | 短期上下文、长期记忆、会话历史 |
| Tool Layer | Tool Router、工具调用、权限控制、审计日志 |

## 开发规范

详见：

- [架构规范](./ARCHITECTURE.md)
- [代码审查指南](./REVIEW_GUIDE.md)
- [MiniMax 执行规范](./MINIMAX_EXECUTION.md)
- [Skill 体系](./SKILLS.md)

## 里程碑

| 版本 | 目标 |
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

详见：[路线图](./ROADMAP.md)
