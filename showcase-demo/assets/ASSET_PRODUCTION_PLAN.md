# 第一版素材生产方案

目标：先让 showcase 从“CSS 占位动画”升级成“真实视觉素材驱动”，但不把项目过早绑死到某一个生成平台。

## 结论

第一版建议采用混合路线：

```text
房间背景：生成静态图
角色基础形象：生成角色设定图
走路/手势/唱歌/待机：用 image-to-video 或 text-to-video 生成短 loop
眼神追踪：暂时继续用前端分层/假动画
情绪粒子：继续用前端 Canvas 粒子
```

这样最快能得到接近参考图的视觉效果，同时保留后续升级成 Live2D/Spine/3D 的空间。

## 为什么不第一版就全用视频

全视频路线的问题：

- 眼神追踪很难实时响应鼠标。
- 情绪粒子用前端做更可控，也更轻。
- 每个动作都重新生成角色，容易脸不一致。
- 视频素材一旦带背景，后续做透明桌面层会麻烦。

所以第一版最实用的是：

- 需要“动作感”的模块用视频。
- 需要“实时交互”的模块用前端逻辑。
- 需要“氛围”的模块用 Canvas/CSS。

## 素材优先级

### P0：必须先做

| 文件 | 用途 | 推荐方式 |
| --- | --- | --- |
| `background-room-night.png` | 统一房间背景 | 文生图 |
| `character-reference.png` | 角色统一参考 | 文生图 |
| `walking.webm` | 走路卡片 | 图生视频 |
| `wave.webm` | 手势卡片默认动作 | 图生视频 |
| `sing.webm` | 唱歌卡片 | 图生视频 |
| `idle-read.webm` | 待机卡片 | 图生视频 |

### P1：增强表现

| 文件 | 用途 | 推荐方式 |
| --- | --- | --- |
| `heart.webm` | 比心动作 | 图生视频 |
| `point.webm` | 指点动作 | 图生视频 |
| `think.webm` | 思考动作 | 图生视频 |
| `idle-wave.webm` | 待机挥手 | 图生视频 |
| `idle-stretch.webm` | 伸懒腰 | 图生视频 |
| `idle-drink.webm` | 喝饮料 | 图生视频 |

### P2：后续升级

| 文件 | 用途 | 推荐方式 |
| --- | --- | --- |
| `character-layered.psd` | 分层角色源文件 | 画师/AI 后修 |
| `eyes.png` / `pupils.png` | 眼神追踪 | 分层导出 |
| `mouth-*.png` | 口型同步 | 分层导出 |
| `live2d/` | 可控角色 | Live2D Cubism |

## 推荐生成方式

### 方式 A：MiniMax / Hailuo 视频

适合：

- 走路
- 挥手
- 比心
- 唱歌
- 待机动作

建议工作流：

1. 先生成 `character-reference.png`。
2. 用同一张角色图做 image-to-video。
3. 每次只生成一个动作。
4. 导出 6 秒左右视频。
5. 转成 `webm`，放进 `assets/motions/`。

注意：

- 提示词里不要引用任何已有 IP 或明星。
- 不要让模型每次重新设计角色。
- 尽量使用同一张角色参考图保持一致性。
- 如果要做透明桌面层，优先尝试纯色背景或透明背景导出，再后期抠像。

### 方式 B：网络素材/素材库

适合：

- 背景图
- 粒子贴图
- 音符图标
- 房间装饰

注意：

- 必须确认授权。
- 不要直接使用不明来源二次元角色。
- 第一版可以用免费可商用素材，但角色主体最好自己生成或自制。

### 方式 C：前端生成

适合：

- 情绪粒子
- 波形
- 音符
- 眼神追踪
- 光效

这些不建议做成视频，因为前端实时生成更灵活。

## 输出规格

视频：

```text
format: webm
duration: 4-8s
resolution: 1280x720 or 1920x1080
fps: 24 or 30
loop: seamless if possible
audio: none
```

图片：

```text
format: png or webp
background: separate from character when possible
minimum: 1280x720 for room background
character: 1024px height or higher
```

## 验收标准

每个动作素材通过以下检查：

- 角色脸和发型尽量一致。
- 动作清晰，一眼能看出含义。
- 循环播放时不突兀。
- 没有明显多手、多腿、脸部变形。
- 背景不要强占主体。
- 没有水印、平台 logo、字幕。
- 文件名符合页面约定。

## 第一版建议

先不要追求 10 个动作全部高质量。更好的顺序是：

1. 先做 `character-reference.png`。
2. 再做 `background-room-night.png`。
3. 生成 `wave.webm` 和 `sing.webm`。
4. 如果角色一致性可接受，再扩展 `walking.webm` 和 idle 动作。
5. 如果一致性很差，暂停视频生成，改走 Live2D/Spine/分层图路线。
