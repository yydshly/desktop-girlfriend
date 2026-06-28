# Architecture

项目业务架构和工程质量规范。

---

## 业务架构分层

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer                          │
│  (PySide6 / Qt, 窗口、控件、渲染)                      │
├─────────────────────────────────────────────────────┤
│                    Core Layer                        │
│  (应用状态、会话管理、生命周期)                         │
├─────────────────────────────────────────────────────┤
│                    Brain Layer                       │
│  (LLM 调用、推理、决策、Prompt 管理)                    │
├─────────────────────────────────────────────────────┤
│                 Expression Layer                     │
│  (表情、动作、动画、语音输出)                            │
├─────────────────────────────────────────────────────┤
│                 Perception Layer                     │
│  (语音输入、手势识别、视觉感知)                         │
├─────────────────────────────────────────────────────┤
│                   Memory Layer                       │
│  (长期记忆、短期记忆、会话历史)                          │
├─────────────────────────────────────────────────────┤
│                    Tool Layer                        │
│  (工具路由、Agent 工具、权限控制)                       │
└─────────────────────────────────────────────────────┘
```

### 层级职责

| 层级 | 职责 |
|------|------|
| **UI Layer** | 用户界面展示和交互，窗口管理，渲染 |
| **Core Layer** | 应用核心状态管理，会话生命周期，应用入口 |
| **Brain Layer** | AI 推理，LLM 调用，Prompt 管理，决策逻辑 |
| **Expression Layer** | 角色表情，动作动画，语音合成输出 |
| **Perception Layer** | 感知输入处理，语音识别，手势识别 |
| **Memory Layer** | 记忆存储，长期记忆，短期记忆 |
| **Tool Layer** | 工具路由，Agent 工具注册，权限控制 |

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

## 核心原则

### EventBus 驱动模块通信

所有跨模块通信必须通过 EventBus，禁止直接模块间调用。

```
Module A --(Event)--> EventBus --(Event)--> Module B
```

### StateMachine 驱动角色状态

所有角色状态变更必须通过 StateMachine。

```
UI Event --> StateMachine --> State Change --> UI Update
```

### Provider 化外部服务

所有外部服务（API、SDK）必须封装为 Provider 接口。

```
Service --> Provider Interface --> Business Logic
```

### Prompt Registry 管理提示词

所有 Prompt 必须集中在 Prompt Registry 管理，禁止散落在业务代码中。

### Tool Router 受权限控制

所有 Agent 工具调用必须通过 Tool Router，并受权限控制。

---

## 架构检查清单

- [ ] 是否遵守分层架构？
- [ ] 是否通过 EventBus 通信？
- [ ] 状态变更是否通过 StateMachine？
- [ ] 外部服务是否 Provider 化？
- [ ] Prompt 是否在 Registry 中？

---

## 关联文档

- [Skill 体系](./SKILLS.md)
- [Review Guide](./REVIEW_GUIDE.md)
- [MiniMax 执行规范](./MINIMAX_EXECUTION.md)
