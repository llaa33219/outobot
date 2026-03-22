# Blend Modes

Complete reference for OutOcut layer blend modes.

Author: BLOUplanet  
License: Apache 2.0

## Overview

Blend modes control how a layer (the **top** or blend layer) combines with pixels already in the frame (the **bottom** or base layer).

- `blendMode` is an optional layer field.
- If omitted (`null` or missing), behavior defaults to `normal`.
- Layer order matters: swapping two layers usually changes the result.
- Blend math is evaluated per channel (`R`, `G`, `B`) on normalized values in `[0, 1]`.

### Layer Field

```json
{
  "id": "highlight",
  "type": "solid",
  "blendMode": "screen",
  "opacity": { "value": 65, "keyframes": null }
}
```

## Performance Notes

| Cost | Modes |
|------|-------|
| Low | `normal`, `multiply`, `screen`, `darken`, `lighten`, `add`, `subtract` |
| Medium | `overlay`, `hardLight`, `difference`, `exclusion`, `divide` |
| High | `colorDodge`, `colorBurn`, `softLight`, `hue`, `saturation`, `color`, `luminosity` |

## Blend Mode Reference

### 1) Normal

- **JSON value**: `"normal"`
- **Visual effect**: Standard over compositing. Top layer simply appears over bottom layer.
- **Formula**: `R = F` (then alpha compositing with layer opacity)
- **Use cases**: Most layers, UI elements, titles, cutout assets, default behavior.

```json
{ "blendMode": "normal" }
```

### 2) Multiply

- **JSON value**: `"multiply"`
- **Visual effect**: Darkens image by multiplying base and blend. White has little effect; black forces black.
- **Formula**: `R = B * F`
- **Use cases**: Shadows, dirt/grain overlays, texture integration, darkening bright footage.

```json
{ "blendMode": "multiply" }
```

### 3) Screen

- **JSON value**: `"screen"`
- **Visual effect**: Brightens by inverting both layers, multiplying, then inverting back. Black has little effect.
- **Formula**: `R = 1 - (1 - B) * (1 - F)`
- **Use cases**: Light leaks, glow passes, lens flares, fire/sparks, additive-looking brightening.

```json
{ "blendMode": "screen" }
```

### 4) Overlay

- **JSON value**: `"overlay"`
- **Visual effect**: Combines multiply in dark regions and screen in bright regions, increasing contrast.
- **Use cases**: Contrast pop, texture-on-footage, cinematic punch, stylized grade layers.

```json
{ "blendMode": "overlay", "opacity": { "value": 35, "keyframes": null } }
```

### 5) Darken

- **JSON value**: `"darken"`
- **Visual effect**: Keeps the darker value from base or blend per channel.
- **Formula**: `R = min(B, F)`
- **Use cases**: Replace bright background noise, merge shadows, suppress highlights.

```json
{ "blendMode": "darken" }
```

### 6) Lighten

- **JSON value**: `"lighten"`
- **Visual effect**: Keeps the lighter value from base or blend per channel.
- **Formula**: `R = max(B, F)`
- **Use cases**: Glow/luma extraction style merges, preserving bright particles or highlights.

```json
{ "blendMode": "lighten" }
```

### 7) Color Dodge

- **JSON value**: `"colorDodge"`
- **Visual effect**: Strongly brightens and saturates highlights; can blow out whites quickly.
- **Formula**: `R = 1` if `F = 1`; otherwise `R = min(1, B / (1 - F))`
- **Use cases**: Intense light rays, magical glints, specular boost.

```json
{ "blendMode": "colorDodge", "opacity": { "value": 25, "keyframes": null } }
```

### 8) Color Burn

- **JSON value**: `"colorBurn"`
- **Visual effect**: Aggressive darkening with strong contrast/saturation in darker tones.
- **Formula**: `R = 0` if `F = 0`; otherwise `R = 1 - min(1, (1 - B) / F)`
- **Use cases**: Gritty stylization, heavy shadow shaping, distressed film looks.

```json
{ "blendMode": "colorBurn" }
```

### 9) Hard Light

- **JSON value**: `"hardLight"`
- **Visual effect**: Combines dodge and burn depending on blend value.
- **Use cases**: Contrast enhancement, textured overlays.

```json
{ "blendMode": "hardLight" }
```

### 10) Soft Light

- **JSON value**: `"softLight"`
- **Visual effect**: Gentler version of hard light with smoother transitions.
- **Use cases**: Subtle texture, gentle contrast.

```json
{ "blendMode": "softLight" }
```

### 11) Difference

- **JSON value**: `"difference"`
- **Visual effect**: Absolute difference between base and blend.
- **Formula**: `R = |B - F|`
- **Use cases**: Color inversion effects, glitch aesthetics.

```json
{ "blendMode": "difference" }
```

### 12) Exclusion

- **JSON value**: `"exclusion"`
- **Visual effect**: Similar to difference but with lower contrast.
- **Use cases**: Softer exclusion effect, muted color shifts.

```json
{ "blendMode": "exclusion" }
```

### 13) Hue

- **JSON value**: `"hue"`
- **Visual effect**: Applies hue of blend layer while preserving luminosity of base.
- **Use cases**: Color styling without affecting brightness.

```json
{ "blendMode": "hue" }
```

### 14) Saturation

- **JSON value**: `"saturation"`
- **Visual effect**: Applies saturation of blend layer while preserving hue and luminosity of base.
- **Use cases**: Saturation adjustments.

```json
{ "blendMode": "saturation" }
```

### 15) Color

- **JSON value**: `"color"`
- **Visual effect**: Applies hue and saturation of blend layer while preserving luminosity of base.
- **Use cases**: Color transfer, tinting.

```json
{ "blendMode": "color" }
```

### 16) Luminosity

- **JSON value**: `"luminosity"`
- **Visual effect**: Applies luminosity of blend layer while preserving hue and saturation of base.
- **Use cases**: Luminosity-based styling.

```json
{ "blendMode": "luminosity" }
```

### 17) Add

- **JSON value**: `"add"`
- **Visual effect**: Simple addition, can exceed 1.0 (clamping typically applied).
- **Formula**: `R = min(1, B + F)`
- **Use cases**: Glow accumulation, light addition.

```json
{ "blendMode": "add" }
```

### 18) Subtract

- **JSON value**: `"subtract"`
- **Visual effect**: Simple subtraction.
- **Formula**: `R = max(0, B - F)`
- **Use cases**: Darkening effects, shadow creation.

```json
{ "blendMode": "subtract" }
```

### 19) Divide

- **JSON value**: `"divide"`
- **Visual effect**: Division blend, can produce bright results.
- **Use cases**: Brightening, screen-like effects.

```json
{ "blendMode": "divide" }
```

## Common Use Cases

### Text with Glow Effect
```json
{
  "id": "layer_text_title",
  "type": "text",
  "blendMode": "screen",
  "opacity": { "value": 100, "keyframes": null }
}
```

### Dark Texture Overlay
```json
{
  "id": "texture_overlay",
  "type": "image",
  "blendMode": "multiply",
  "opacity": { "value": 30, "keyframes": null }
}
```

### Logo on Video
```json
{
  "id": "logo",
  "type": "image",
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null }
}
```

## See Also

- [layer-types.md](layer-types.md) - Layer type reference
- [effects.md](effects.md) - Effect reference
- [file-format.md](file-format.md) - Complete .outocut format specification
