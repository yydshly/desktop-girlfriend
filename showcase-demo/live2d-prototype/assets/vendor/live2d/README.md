# Live2D Runtime Vendor Assets

These browser runtime files are vendored so the PySide6/QtWebEngine desktop
shell can load the Live2D model without depending on remote CDN script loading.

Sources:

- `pixi.min.js`: `https://cdn.jsdelivr.net/npm/pixi.js@6.5.10/dist/browser/pixi.min.js`
- `live2dcubismcore.min.js`: `https://cubism.live2d.com/sdk-web/cubismcore/live2dcubismcore.min.js`
- `pixi-live2d-display-cubism4.min.js`: `https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js`
