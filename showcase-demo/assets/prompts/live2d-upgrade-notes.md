# Live2D / Spine 升级素材说明

如果视频生成的角色一致性不够好，下一阶段应改为“可控角色资产”。

## 最小分层

```text
body
head
hair_back
hair_front
eye_left
eye_right
pupil_left
pupil_right
mouth_closed
mouth_open_small
mouth_open_medium
mouth_open_large
arm_left
arm_right
hand_left
hand_right
leg_left
leg_right
skirt
accessory_hairclip
```

## 为什么需要分层

- 眼神追踪需要独立眼睛/瞳孔。
- 唱歌需要独立嘴型。
- 手势需要手臂可控。
- 呼吸、眨眼、头发晃动可以循环驱动。

## 第一版不必马上做

Live2D/Spine 的资产成本高，建议在视频 showcase 验证方向后再投入。

推荐判断条件：

- 如果你只是想要“展示页好看”：继续视频素材。
- 如果你想要“桌面角色长期陪伴”：转 Live2D/Spine。
- 如果你想要“真实空间感与 3D 互动”：再考虑 VRM/Three.js。
