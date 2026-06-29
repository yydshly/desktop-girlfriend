# Desktop Girlfriend Release Candidate v0

Version: `0.1.0-rc.3`

Stage: `release-candidate`

Main capabilities:
- V8 Memory Runtime v0
- V9 Proactive Companionship v0
- V10 Avatar Action v0
- V11 Product Experience v0
- V12 Release Candidate Smoke Pack v0

## RC changelog

### v0.1.0-rc.3

- Fixed: README and run script now use pyproject-based installation: `pip install -e ".[dev]"`.
- Fixed: Windows setup now explicitly requires Python >=3.11.
- Fixed: audio recorder no longer imports `sounddevice` at module import time.
- Added: environment readiness probe.
- Improved: event bus thread-safety.
- Improved: controller shutdown handling for worker threads.
- Improved: memory repository write durability with temp-file replace.
- Improved: MiniMax Chat/TTS HTTP error details with key redaction.

### v0.1.0-rc.2

- Fixed: the first click on the “状态” button after startup could have no visible effect.

### v0.1.0-rc.1

- Fixed: the “状态” button did not open the product status panel on Windows/PySide6.

### v0.1.0-rc.0

- First release candidate.

## Tag plan

After merging into `main`, create the release candidate tag:

```powershell
git tag v0.1.0-rc.3
git push origin v0.1.0-rc.3
```

## 当前版本能力

### V8 Memory Runtime v0

- 用户确认式记忆
- 本地 JSON 保存
- 不保存 evidence
- 不保存完整原始对话
- 不自动确认

### V9 Proactive Companionship v0

- 空闲主动陪伴
- 可选 TTS
- 勿扰时间
- 用户拒绝后暂停

### V10 Avatar Action v0

- idle / listening / thinking / speaking / proactive / error 状态
- emoji 状态显示
- 状态样式
- 主动陪伴 avatar 状态修复

### V11 Product Experience v0

- 状态面板
- 启动说明
- 启动诊断

---

## 快速启动（Windows）

```powershell
.\scripts\run_desktop.ps1
```

首次运行脚本会自动从 `.env.example` 创建 `.env`，请先编辑 `.env` 填写真实 provider 配置。

---

## 开发验证

在仓库根目录执行：

```powershell
# Lint
.venv\Scripts\python.exe -m ruff check .

# Type check
.venv\Scripts\python.exe -m mypy app

# Full test suite
.venv\Scripts\python.exe -m pytest -q

# RC self-check
.venv\Scripts\python.exe scripts\probe_release_candidate.py

# Individual probes
.venv\Scripts\python.exe scripts\probe_product_status.py
.venv\Scripts\python.exe scripts\probe_launch_readiness.py
.venv\Scripts\python.exe scripts\probe_startup_diagnostics.py
```

---

## 隐私与安全

**不要提交以下内容：**

- `.env` — 包含真实 API key
- `.tmp` — 临时文件
- 任何真实 API key 或 token

**默认关闭的功能：**

- 记忆（memory_context_enabled）默认关闭
- 主动陪伴（proactive_enabled）默认关闭
- 主动陪伴 TTS（proactive_tts_enabled）默认关闭

**记忆行为：**

- 记忆必须用户确认才保存
- 不保存 evidence
- 不保存完整原始对话

---

## 如何开启可选功能

编辑 `.env`：

```env
# 记忆
MEMORY_CONTEXT_ENABLED=true

# 主动陪伴
PROACTIVE_ENABLED=true

# 主动陪伴 TTS（需先开启主动陪伴）
PROACTIVE_TTS_ENABLED=true
```

---

## 已知限制

- 不支持云端同步
- 不支持自动更新
- 不提供安装包
