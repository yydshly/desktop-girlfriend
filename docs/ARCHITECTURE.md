# Architecture

项目业务架构和工程质量规范。

---

## 业务架构分层

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer                          │
│  (PySide6 / Qt, 桌面窗口、角色展示、用户界面)           │
├─────────────────────────────────────────────────────┤
│                    Core Layer                       │
│  (EventBus、StateMachine、Config、应用生命周期)        │
├─────────────────────────────────────────────────────┤
│                    Brain Layer                      │
│  (LLM、Prompt、MiniMax Provider、Agent 决策)         │
├─────────────────────────────────────────────────────┤
│                  Expression Layer                   │
│  (TTS、语音播放、Avatar 表现、动作状态)               │
├─────────────────────────────────────────────────────┤
│                  Perception Layer                   │
│  (ASR、麦克风、摄像头、手势识别)                       │
├─────────────────────────────────────────────────────┤
│                    Memory Layer                     │
│  (短期上下文、长期记忆、会话历史)                       │
├─────────────────────────────────────────────────────┤
│                     Tool Layer                      │
│  (Tool Router、工具调用、权限控制、审计日志)            │
└─────────────────────────────────────────────────────┘
```

### 层级职责

| 层级 | 职责 |
|------|------|
| **UI Layer** | 桌面窗口、角色展示、用户界面 |
| **Core Layer** | EventBus、StateMachine、Config、应用生命周期 |
| **Brain Layer** | LLM、Prompt、MiniMax Provider、Agent 决策 |
| **Expression Layer** | TTS、语音播放、Avatar 表现、动作状态 |
| **Perception Layer** | ASR、麦克风、摄像头、手势识别 |
| **Memory Layer** | 短期上下文、长期记忆、会话历史 |
| **Tool Layer** | Tool Router、工具调用、权限控制、审计日志 |

---

## EventBus 使用边界

### 应该使用 EventBus 的场景

- UI 交互触发业务事件
- 语音识别完成事件
- 手势识别完成事件
- TTS 播放开始 / 完成事件
- Avatar 状态切换通知
- Agent 工具执行结果通知
- 跨层异步事件通知

### 不需要使用 EventBus 的场景

- 同一模块内部函数调用
- 同一层内部纯工具函数调用
- Provider 内部实现细节
- 无副作用的纯计算逻辑
- 配置读取和数据结构转换

### 禁止的调用方式

| 禁止 | 说明 |
|------|------|
| UI 直接调用 MiniMax API | UI 层禁止直接调用 Brain 层以外的 API |
| UI 直接调用 Tool Router | 禁止 UI 层直接执行本地命令 |
| UI 直接修改角色状态 | 必须通过 StateMachine |
| 任意模块绕过 StateMachine 修改状态 | 状态变更必须走 StateMachine |
| Prompt 散落在业务代码中 | Prompt 必须集中管理 |

### EventBus vs 直接函数调用

```
应该用 EventBus:
  UI Layer --> EventBus --> Core Layer (业务事件)
  Perception --> EventBus --> Brain Layer (感知输入)
  Brain Layer --> EventBus --> Expression Layer (输出指令)

可以用直接调用:
  Core Layer 内部: StateMachine.set_state()
  同一层内部工具函数: def validate_config()
  Provider 内部实现: def _make_request()
```

---

## StateMachine 驱动角色状态

所有角色状态变更必须通过 StateMachine。

```
UI Event --> StateMachine --> State Change --> Expression Update
```

### StateMachine 管理的状态

- 角色情绪状态
- 角色动作状态
- 对话状态
- 交互模式（语音/文本/手势）

---

## Provider 化外部服务

所有外部服务（API、SDK）必须封装为 Provider 接口。

```
External Service --> Provider Interface --> Business Logic
```

### Provider 规范

- 每个外部服务对应一个 Provider
- Provider 定义标准接口
- 业务代码只依赖 Provider 接口，不依赖具体实现

---

## Prompt Registry 管理提示词

所有 Prompt 必须集中在 Prompt Registry 管理，禁止散落在业务代码中。

---

## Tool Router 受权限控制

所有 Agent 工具调用必须通过 Tool Router，并受权限控制。

---

## 工程质量层

### 工具链

| 工具 | 用途 |
|------|------|
| `pre-commit` | Git hooks，提交前检查 |
| `ruff` | Python Lint 和格式化 |
| `pytest` | 单元测试和集成测试 |
| `mypy` | 类型检查 |
| `GitHub Actions` | CI/CD 自动化 |

### 守护 Skill

| Skill | 职责 |
|-------|------|
| `architecture-guard` | 守护分层架构边界 |
| `prompt-registry` | 集中管理 Prompt |
| `safety-privacy-guard` | 安全与隐私合规 |

---

## 架构检查清单

- [ ] 是否遵守分层架构？
- [ ] 业务事件是否通过 EventBus？
- [ ] 状态变更是否通过 StateMachine？
- [ ] 外部服务是否 Provider 化？
- [ ] Prompt 是否在 Registry 中？
- [ ] 是否有禁止的调用方式？

---

## 新模块开发原则

每个新模块开发前，必须先确认：

- 模块归属层级
- 输入事件
- 输出事件
- 依赖边界
- 禁止调用方式

详见：[Review Guide - Module Development Gate Checklist](./REVIEW_GUIDE.md#module-development-gate-checklist)

---

## 关联文档

- [Skill 体系](./SKILLS.md)
- [Review Guide](./REVIEW_GUIDE.md)
- [MiniMax 执行规范](./MINIMAX_EXECUTION.md)
