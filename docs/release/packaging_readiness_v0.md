# Packaging Readiness v0

**Phase:** 3-F
**Version:** 0.2.0-alpha.2
**Goal:** Confirm the project has the minimum conditions for future packaging.

This document is **not** a final release or installation package.
It records the current packaging readiness state and known risks.

---

## 当前推荐启动方式

```powershell
# 1. 创建虚拟环境（首次）
python -m venv .venv

# 2. 安装依赖
.venv\Scripts\python.exe -m pip install -e .

# 3. 复制配置示例
copy .env.example .env

# 4. 按需填写 .env 中的 API key（可选，fake 模式无需 key）

# 5. 运行
.\scripts\run_desktop.ps1
```

默认 **fake provider** 模式可用，不需要真实 API key。

真实模型、TTS、ASR 功能需要自行配置对应 API key。

---

## 项目结构（打包相关）

```
.
├── .env.example          # 用户配置模板（安全，不含真实 key）
├── VERSION               # 版本号文件
├── pyproject.toml       # Python 项目配置
├── README.md            # 项目说明
├── scripts/
│   └── run_desktop.ps1  # Windows 启动脚本
├── app/
│   ├── main.py          # 应用入口
│   └── packaging/
│       └── readiness.py  # 打包就绪检查
└── docs/
    └── release/
        ├── packaging_readiness_v0.md
        └── windows_gui_smoke_checklist.md
```

---

## 后续可选打包方案

| 方案 | 状态 | 说明 |
|------|------|------|
| PyInstaller | 可行 | 需处理 PySide6 资源路径 |
| Nuitka | 未验证 | 可能更快 |
| NSIS / Inno Setup | 未做 | 需后续阶段 |
| conda / pip install | 未做 | 需完善 pyproject.toml |

---

## 暂不做的项

- 安装器（NSIS / Inno Setup）
- 自动更新机制
- 代码签名
- Windows 系统通知（Toast）
- 开机自启
- 多平台分发（macOS / Linux）
- 正式 release tag

---

## 打包前已知风险

| 风险 | 说明 | 缓解方式 |
|------|------|----------|
| PySide6 资源路径 | 打包后 QML/图标可能找不到 | 使用 `--add-data` 或 `PySide6-addons` |
| 托盘图标 | 打包后可能不显示 | 确认图标路径为绝对路径或嵌入资源 |
| .env 管理 | 用户 key 需要手动配置 | 提供 .env.example 说明 |
| API key 安全 | 不要提交 .env 到仓库 | .gitignore 已排除 |
| Windows 杀软误报 | PyInstaller 常见问题 | 签名或加入白名单 |
| .tmp 目录 | 运行时生成，需要写权限 | 使用用户可写目录 |

---

## 验证方式

```powershell
# 打包就绪探测
python scripts/probe_packaging_readiness.py

# GUI smoke 测试
# 参考 docs/release/windows_gui_smoke_checklist.md 手动验证
```

---

## 下一步（不承诺）

- Phase 3-G: Release Stabilization（未开始）
- 正式安装包制作（需要单独项目立项）
