# Showcase Tools

## Check Assets

```powershell
python .\tools\check_assets.py
```

Checks whether every file listed in `assets/asset-manifest.json` exists.

## Generate Placeholder Motions

```powershell
python .\tools\generate_placeholder_motions.py
```

Regenerates the current simple placeholder WebM loops from `assets/reference/character-reference.png`.

## Normalize External Motion Video

Use this when you download a video from MiniMax/Hailuo/another generation tool.

Preview candidate:

```powershell
python .\tools\normalize_motion.py wave C:\Downloads\wave.mp4
```

Activate it in the showcase:

```powershell
python .\tools\normalize_motion.py wave C:\Downloads\wave.mp4 --replace
```

Valid motion keys are defined in `assets/asset-manifest.json`:

```text
walking, wave, heart, point, think, sing,
idleWave, idleStretch, idleRead, idleDrink
```

The output format is:

```text
VP9 WebM, 1280x720, 24fps, no audio, 4 seconds by default
```
