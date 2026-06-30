# Live2D Asset Specification

## Required Delivery

- Layered PSD suitable for Live2D Cubism.
- Exported Live2D model folder with `.model3.json`.
- Texture files referenced by the model.
- At least four expressions: neutral, happy, thinking, sad.
- At least four motions: idle, greet, reply, comfort.
- Physics file for hair and clothing movement when available.

## PSD Layer Requirements

- Back hair separated from face and body.
- Front hair separated into left, center, and right clumps when possible.
- Face base separated from eyes, brows, mouth, blush, and shadow.
- Eye whites, pupils, highlights, and eyelids separated.
- Mouth shapes separated for closed, small, medium, and wide open.
- Brows separated for neutral, happy, sad, and thinking poses.
- Neck, body, arms, sleeves, skirt, and accessories separated.

## Runtime Parameter Targets

- `ParamAngleX`
- `ParamAngleY`
- `ParamAngleZ`
- `ParamBodyAngleX`
- `ParamEyeLOpen`
- `ParamEyeROpen`
- `ParamEyeBallX`
- `ParamEyeBallY`
- `ParamMouthOpenY`
- `ParamMouthForm`
- `ParamBreath`
