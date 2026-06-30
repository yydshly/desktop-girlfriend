# Asset Origin

这份文件记录当前第一版素材的来源，避免后续不知道哪些能直接替换。

## 当前素材

| 文件 | 来源 | 用途 | 是否最终资产 |
| --- | --- | --- | --- |
| `assets/reference/character-reference.png` | AI 生成 | 角色统一参考图 | 否 |
| `assets/background/background-room-night.png` | AI 生成 | 展示页统一房间背景 | 可暂用 |
| `assets/motions/*.webm` | 本地 ffmpeg 从角色参考图生成 | 跑通视频加载链路 | 否 |

## 角色参考图提示词摘要

原创温柔二次元桌面 AI 伙伴女孩，棕色长发，粉色发夹，浅粉色宽松毛衣，白色百褶裙，夜晚电脑桌房间，暖色台灯，柔和景深，无文字、无 logo、无已有 IP。

## 背景图提示词摘要

夜晚温馨电脑桌房间，双显示器、木质书桌、暖色台灯、植物、书架、窗帘，中间留出角色站立空间，无人物、无文字、无 logo。

## 占位 WebM 的性质

当前 `assets/motions/*.webm` 只是轻微旋转/呼吸 loop，用来验证：

- 文件命名是否正确
- 页面是否能自动加载真实视频
- 缺素材时是否能回退到 CSS/Canvas
- 后续替换 MiniMax/Hailuo 视频是否无需改代码

这些占位视频不代表最终动作质量。真实动作应使用 `assets/prompts/motion-prompts.md` 中的提示词，通过 image-to-video 生成后覆盖同名文件。

## 替换规则

用真实视频替换时，直接覆盖同名文件：

```text
assets/motions/wave.webm
assets/motions/sing.webm
assets/motions/walking.webm
```

覆盖后运行：

```powershell
python .\tools\check_assets.py
```

页面无需改代码。

如果下载到的是 `mp4` 或 `mov`，先用归一化工具转换：

```powershell
python .\tools\normalize_motion.py wave C:\Downloads\wave.mp4 --replace
```
