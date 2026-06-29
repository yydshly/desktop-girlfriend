# v0.3.0-alpha.1 Release Notes

## 定位

这是 Desktop Girlfriend / 小云桌面伴侣的 Phase 3 alpha 版本。

本版本目标是让应用从"开发环境可运行"进入"小范围真实试用"的状态。

## 主要能力

### 桌面伴侣基础体验
- 顶部角色卡（☁️ 小云）
- 聊天区
- 输入框
- 发送按钮
- 小窗模式
- 置顶模式
- 托盘隐藏与恢复
- 点击 X 隐藏到托盘

### 启动引导
- 首次启动引导卡
- 设置入口说明
- 记忆隐私说明
- 主动陪伴说明（含"别打扰"控制）

### 记忆体验
- 记忆建议（用户确认后保存）
- 手动添加记忆
- 查看已保存记忆
- 删除记忆
- 不自动保存完整聊天
- 不保存 evidence

### 主动陪伴
- 空闲后主动出现
- 冷却时间说明
- 勿扰时间说明
- "别打扰"轻量反馈（小云会安静一会儿）
- 托盘隐藏时不强制弹窗

### 设置体验
- 设置面板可滚动
- 结构化设置说明
- API Key 只显示"已配置"/"未配置"
- 复制安全配置示例按钮
- 明确当前版本不会直接修改 .env
- 明确部分配置需要重启生效

### 打包准备
- .env.example（含所有配置区块）
- Windows 启动说明（PowerShell 脚本）
- Packaging readiness probe
- Windows GUI smoke checklist

## 安全与隐私

- 不提交真实 .env 到仓库
- 不显示真实 API Key
- 不保存完整原始聊天
- 不保存 memory evidence
- 记忆仅保存用户确认或手动添加的内容
- Memory 数据本地 JSON 文件保存

## 已知限制

- 当前不是正式安装包
- 当前没有安装器（NSIS/Inno Setup）
- 当前没有自动更新
- 当前没有代码签名
- 当前没有账号系统
- 当前没有云同步
- 当前没有正式产品形态定稿
- 当前仍建议通过 `scripts/run_desktop.ps1` 或开发环境启动

## Phase 3 完成情况

| Phase | 名称 | 状态 |
|-------|------|------|
| Phase 3-A | Close / Tray Behavior | ✅ |
| Phase 3-B | First Run Onboarding | ✅ |
| Phase 3-C | Memory UX v1 | ✅ |
| Phase 3-D | Proactive Companion Real UX v1 | ✅ |
| Phase 3-E | Settings Runtime Controls v1 | ✅ |
| Phase 3-F | Packaging Readiness v0 | ✅ |

## 验证

- ruff
- mypy
- target tests
- probes
- full pytest
- Windows GUI smoke checklist

## 升级说明

从 `0.2.0-alpha.2` 升级：

1. `git pull` 获取最新代码
2. 确认 `.env` 配置（如使用 fake 模式无需额外配置）
3. 运行 `.\scripts\run_desktop.ps1`
