# PNG Puppet V1 Layer Contract

这个目录用于放置下一步真正可控的人物分层 PNG。

当前 `puppet.html` 仍然使用 `assets/reference/character-reference.png` 作为参考底图，再用前端叠加假眼睛、假嘴型做协议验证。要进入真实素材驱动，需要把角色拆成透明 PNG 图层。

当前目录里的 PNG 如果由 `tools/generate_layer_placeholders.py` 生成，只是技术占位素材，用来验证真实分层加载、口型切换和瞳孔移动链路。最终项目应替换为同一角色的真实分层素材。

## 最小可用图层

```text
base-body.png          透明背景，全身或半身主体，不含可替换眼睛和嘴巴
eye-left-white.png     左眼眼白或完整眼睛底层
eye-right-white.png    右眼眼白或完整眼睛底层
pupil-left.png         左瞳孔
pupil-right.png        右瞳孔
mouth-closed.png       闭嘴
mouth-small.png        小开口
mouth-medium.png       中开口
mouth-large.png        大开口
eyelid-left.png        左眼闭眼/眨眼遮罩
eyelid-right.png       右眼闭眼/眨眼遮罩
```

## 建议增强图层

```text
hair-front.png
hair-back.png
head.png
torso.png
arm-left-idle.png
arm-right-idle.png
arm-left-wave.png
arm-right-wave.png
blush.png
tears.png
shadow.png
```

## 坐标约定

- 所有 PNG 使用相同画布尺寸。
- 所有 PNG 必须是透明背景。
- 图层原点都从画布左上角开始，不要裁切到不同尺寸。
- 第一版建议画布为 `1024x1536` 或 `768x1152`。
- 眼睛、嘴巴、手臂可以先不追求完美，只要能被 `avatar.state` 事件切换。

## 后续替换路径

```text
PNG Puppet V1
  -> Live2D Cubism model3.json
  -> VRM / glTF 3D model
```

这三种渲染器都应该吃同一份 `assets/avatar/avatar-state-schema.json`，不要把 AI 逻辑写死在某个渲染实现里。

## 生成技术占位层

```powershell
python .\tools\generate_layer_placeholders.py
python .\tools\check_layers.py
```
