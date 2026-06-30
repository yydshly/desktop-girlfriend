# Avatar Puppet V1 计划

当前 `puppet.html` 的目标不是“展示一张图”，而是建立人物素材的可控协议。

## 当前阶段：伪分层 Puppet

由于我们还没有真正的分层人物素材，V1 采用：

```text
base-body: 整张人物图
pupil: 前端叠加的瞳孔层
mouth: 前端叠加的嘴型层
blink: 前端叠加的眨眼层
emotion-aura: 情绪氛围层
fx-layer: Canvas 粒子层
```

这不是最终美术方案，但它能验证最重要的运行时控制能力。

## 当前能控制什么

- 瞳孔跟随鼠标
- 头部轻微跟随
- 嘴型切换：closed / small / medium / large
- speaking 状态自动口型
- 情绪粒子：calm / happy / excited / sad
- 动作姿态：idle / think / speak / sing / sad
- 事件日志和状态读数

## 为什么先做伪分层

真正分层素材需要更高成本：

```text
head.png
hair-front.png
hair-back.png
eye-left.png
eye-right.png
pupil-left.png
pupil-right.png
mouth-closed.png
mouth-open-small.png
mouth-open-medium.png
mouth-open-large.png
body.png
arm-left.png
arm-right.png
```

在没有这些素材前，先做伪分层可以回答：

- 控制协议是否合理
- 状态事件是否足够
- 哪些部件最值得优先拆
- 未来接 Live2D/Spine 时需要哪些 motion/state

## 下一步

推荐顺序：

1. 校准当前伪分层的眼睛和嘴巴位置。
2. 使用 `assets/avatar/puppet-v1.json` 作为当前角色素材配置。
3. 生成或绘制透明背景角色。
4. 先拆 `eyes / pupils / mouth`，不用急着拆全身。
5. 把 `puppet.js` 的 DOM 图层替换成真实 PNG 图层。
6. 如果控制效果成立，再升级 Live2D / Spine。

## 和 AI 状态机的接口

未来后端只需要发事件：

```js
window.dispatchPuppetAction({
  type: "puppet.action",
  emotion: "happy",
  action: "speak",
  mouth: "medium",
  gaze: "cursor",
  speaking: true,
  source: "ai-state",
});
```

前端负责把它变成具体视觉表现。
