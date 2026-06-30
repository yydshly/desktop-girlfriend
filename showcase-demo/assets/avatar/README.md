# Avatar Puppet Assets

这个目录用于沉淀“可控人物素材”的协议。

当前 `puppet.html` 还没有真正分层 PNG，所以使用伪分层：

```text
base image: assets/reference/character-reference.png
overlay: CSS/DOM 生成的 pupil、mouth、blink、emotion-aura
```

## V1 配置目标

在 `puppet.html` 的“部件校准”面板里调整眼睛和嘴巴位置后，可以把“当前部件配置”里的 JSON 保存成正式素材配置：

```text
assets/avatar/puppet-v1.json
```

`puppet.js` 启动时会优先读取这个文件。如果直接双击 HTML 导致浏览器拦截 `fetch`，页面会自动回退到内置默认值；使用本地服务访问时会读取 JSON。

## 未来目录结构

```text
assets/avatar/
  puppet-v1.json
  base-body.png
  head.png
  eye-left.png
  eye-right.png
  pupil-left.png
  pupil-right.png
  mouth-closed.png
  mouth-open-small.png
  mouth-open-medium.png
  mouth-open-large.png
```

第一步不需要拆全身。最优先拆：

```text
eyes / pupils / mouth
```

这三类素材决定了“看鼠标”和“说话”是否真实。
