# Effects Reference

Comprehensive reference for OutOcut's layer effects system.

- Author: BLOUplanet
- License: Apache 2.0

## Effects System Overview

Effects are defined per layer in `layer.effects` and evaluated in stack order.

```json
{
  "effects": [
    {
      "id": "fx_01",
      "type": "dropShadow",
      "enabled": true,
      "params": {
        "distance": 12,
        "angle": 135,
        "blur": 20,
        "color": "#000000",
        "opacity": 60
      },
      "keyframes": {
        "distance": [
          { "time": 0, "value": 4 },
          { "time": 1.0, "value": 16, "easing": "easeOutCubic" }
        ]
      }
    }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique effect instance ID in the layer. |
| `type` | string | Yes | Camel-case effect identifier (from `EffectType`). |
| `enabled` | boolean | Yes | Enables/disables effect without removing it. |
| `params` | object | Yes | Effect-specific parameter object. |
| `keyframes` | object or `null` | No | Per-parameter keyframe tracks (by param name). |

## Important Rules

1. Effect order matters: effects are applied top-to-bottom in `effects[]`; changing order changes output.
2. Stack cost is cumulative: each additional effect can add full-frame processing work.
3. Keyframes are per param: put tracks under `keyframes.<paramName>`.
4. Multiple blur effects can produce non-linear results and may not visually "stack" as expected.

## Performance Scale

| Level | Typical Cost |
|---|---|
| Low | Minimal per-pixel math, usually real-time friendly at 1080p. |
| Medium | Noticeable extra processing, especially with many layers. |
| High | Expensive sampling/compositing; can significantly slow frame rendering. |

## Effect Index

| # | Effect | `type` | Keyframes | Perf | Primary Use |
|---|---|---|---|---|---|
| 1 | Drop Shadow | `dropShadow` | Yes | Medium | Depth and separation |
| 2 | Inner Shadow | `innerShadow` | Yes | Medium | Engraved/inset styling |
| 3 | Glow | `glow` | Yes | Medium | Soft emitted light |
| 4 | Outer Glow | `outerGlow` | Yes | Medium | Halo around outside edges |
| 5 | Gaussian Blur | `gaussianBlur` | Yes | High | Defocus, atmospheric softness |
| 6 | Directional Blur | `directionalBlur` | Yes | High | Motion streak in one direction |
| 7 | Radial Blur | `radialBlur` | Yes | High | Spin/zoom radiating blur |
| 8 | Crop | `crop` | Yes | Low | Edge trimming and reveal windows |
| 9 | Rotate | `rotate` | Yes | Low | Extra post-transform rotation |
| 10 | Flip | `flip` | Yes | Low | Horizontal/vertical inversion |
| 11 | Mirror | `mirror` | Yes | Medium | Reflection/tile duplication |
| 12 | Color Correction | `colorCorrection` | Yes | Medium | Overall color balancing |
| 13 | Brightness/Contrast | `brightnessContrast` | Yes | Low | Quick tonal tuning |
| 14 | Hue/Saturation | `hueSaturation` | Yes | Medium | Palette shifting and intensity |
| 15 | Levels | `levels` | Yes | Medium | Input/output remapping |
| 16 | Curves | `curves` | Partial | Medium | Filmic tonal shaping |
| 17 | Chroma Key | `chromaKey` | Yes | High | Green/blue screen keying |
| 18 | Noise | `noise` | Yes | Medium | Grain and texture |
| 19 | Vignette | `vignette` | Yes | Low | Edge darkening/focus |
| 20 | Glow Effect | `glowEffect` | Yes | Medium | Alternate glow pipeline |
| 21 | Stroke | `stroke` | Yes | Medium | Outlines around alpha/paths |
| 22 | Fill Gradient | `fillGradient` | Partial | Medium | Gradient recolor/fill |
| 23 | Trim Path | `trimPath` | Yes | Medium | Shape draw-on effects |
| 24 | Wiggle | `wiggle` | Yes | Low | Procedural jitter animation |
| 25 | Text Animator | `textAnimator` | Partial | Medium | Text-specific animated styling |

## Shadow Effects

### Drop Shadow (`dropShadow`)

Purpose: Adds an offset shadow behind the layer to improve depth and readability.

| Param | Type | Range | Description |
|---|---|---|---|
| `distance` | number | `>= 0` px | Shadow offset distance. |
| `angle` | number | `0-360` deg | Direction of shadow offset. |
| `blur` | number | `>= 0` px | Softness radius. |
| `color` | string | Hex color | Shadow tint. |
| `opacity` | number | `0-100` | Shadow visibility. |

```json
{
  "id": "shadow_1",
  "type": "dropShadow",
  "enabled": true,
  "params": {
    "distance": 12,
    "angle": 120,
    "blur": 18,
    "color": "#000000",
    "opacity": 55
  },
  "keyframes": null
}
```

### Inner Shadow (`innerShadow`)

Purpose: Creates inward shading at layer edges for inset or embossed looks.

| Param | Type | Range | Description |
|---|---|---|---|
| `distance` | number | `>= 0` px | Inward offset distance. |
| `angle` | number | `0-360` deg | Direction of inner shading. |
| `blur` | number | `>= 0` px | Edge softness. |
| `color` | string | Hex color | Shadow color. |
| `opacity` | number | `0-100` | Shadow intensity. |
| `choke` | number | `0-100` | Hardens edge before blur. |

```json
{
  "id": "inner_1",
  "type": "innerShadow",
  "enabled": true,
  "params": {
    "distance": 6,
    "angle": 315,
    "blur": 10,
    "color": "#000000",
    "opacity": 35,
    "choke": 15
  },
  "keyframes": null
}
```

### Glow (`glow`)

Purpose: Adds soft light around bright or alpha edges.

| Param | Type | Range | Description |
|---|---|---|---|
| `radius` | number | `>= 0` px | Glow spread size. |
| `color` | string | Hex color | Glow tint. |
| `opacity` | number | `0-100` | Glow intensity. |
| `threshold` | number | `0-100` | Luma cutoff for selective glow. |

```json
{
  "id": "glow_1",
  "type": "glow",
  "enabled": true,
  "params": {
    "radius": 24,
    "color": "#00ccff",
    "opacity": 80,
    "threshold": 35
  },
  "keyframes": null
}
```

### Outer Glow (`outerGlow`)

Purpose: Applies glow strictly outside opaque regions.

| Param | Type | Range | Description |
|---|---|---|---|
| `radius` | number | `>= 0` px | Outer halo size. |
| `color` | string | Hex color | Halo color. |
| `opacity` | number | `0-100` | Halo intensity. |
| `spread` | number | `0-100` | Fills glow core before falloff. |

```json
{
  "id": "outer_glow_1",
  "type": "outerGlow",
  "enabled": true,
  "params": {
    "radius": 30,
    "color": "#ffaa00",
    "opacity": 70,
    "spread": 20
  },
  "keyframes": null
}
```

## Blur Effects

### Gaussian Blur (`gaussianBlur`)

Purpose: Smooth isotropic blur used for defocus and background softening.

| Param | Type | Range | Description |
|---|---|---|---|
| `radius` | number | `>= 0` px | Blur radius. |
| `iterations` | integer | `1+` | Additional blur passes. |
| `edgeMode` | string | `clamp`, `wrap`, `mirror` | Edge handling behavior. |

```json
{
  "id": "gblur_1",
  "type": "gaussianBlur",
  "enabled": true,
  "params": {
    "radius": 14,
    "iterations": 1,
    "edgeMode": "clamp"
  },
  "keyframes": null
}
```

### Directional Blur (`directionalBlur`)

Purpose: Blurs pixels along a line to simulate directional motion.

| Param | Type | Range | Description |
|---|---|---|---|
| `distance` | number | `>= 0` px | Blur travel length. |
| `angle` | number | `0-360` deg | Blur direction. |
| `samples` | integer | `3+` | Number of sampling taps. |

```json
{
  "id": "dblur_1",
  "type": "directionalBlur",
  "enabled": true,
  "params": {
    "distance": 22,
    "angle": 90,
    "samples": 16
  },
  "keyframes": null
}
```

### Radial Blur (`radialBlur`)

Purpose: Blurs radially from a center point (spin or zoom style).

| Param | Type | Range | Description |
|---|---|---|---|
| `amount` | number | `0-100` | Blur strength. |
| `center` | array | `[x, y]` | Radial origin in pixels. |
| `mode` | string | `spin`, `zoom` | Radial blur mode. |
| `samples` | integer | `4+` | Sampling quality. |

```json
{
  "id": "rblur_1",
  "type": "radialBlur",
  "enabled": true,
  "params": {
    "amount": 28,
    "center": [960, 540],
    "mode": "zoom",
    "samples": 20
  },
  "keyframes": null
}
```

## Transform Effects

### Crop (`crop`)

Purpose: Trims layer edges after base transforms.

| Param | Type | Range | Description |
|---|---|---|---|
| `left` | number | `>= 0` px | Crop from left edge. |
| `top` | number | `>= 0` px | Crop from top edge. |
| `right` | number | `>= 0` px | Crop from right edge. |
| `bottom` | number | `>= 0` px | Crop from bottom edge. |
| `feather` | number | `>= 0` px | Soft crop edge falloff. |

```json
{
  "id": "crop_1",
  "type": "crop",
  "enabled": true,
  "params": {
    "left": 120,
    "top": 0,
    "right": 120,
    "bottom": 0,
    "feather": 0
  },
  "keyframes": null
}
```

### Rotate (`rotate`)

Purpose: Adds extra rotation as an effect-stage operation.

| Param | Type | Range | Description |
|---|---|---|---|
| `angle` | number | any degree | Additional rotation angle. |
| `center` | array | `[x, y]` | Rotation pivot override. |
| `resample` | string | `nearest`, `bilinear` | Sampling filter. |

### Flip (`flip`)

Purpose: Mirrors content horizontally, vertically, or both.

| Param | Type | Range | Description |
|---|---|---|---|
| `horizontal` | boolean | `true/false` | Flip on X axis. |
| `vertical` | boolean | `true/false` | Flip on Y axis. |

```json
{
  "id": "flip_1",
  "type": "flip",
  "enabled": true,
  "params": {
    "horizontal": true,
    "vertical": false
  },
  "keyframes": null
}
```

### Mirror (`mirror`)

Purpose: Reflects and repeats content across a configurable axis.

| Param | Type | Range | Description |
|---|---|---|---|
| `axis` | string | `horizontal`, `vertical`, `angle` | Mirror axis mode. |
| `angle` | number | `0-360` deg | Axis angle when `axis=angle`. |
| `offset` | number | px | Reflection offset from center. |
| `repeat` | integer | `1+` | Number of repeated reflections. |

## Color Correction Effects

### Color Correction (`colorCorrection`)

Purpose: Overall color balancing.

| Param | Type | Range | Description |
|---|---|---|---|
| `brightness` | number | `-100` to `100` | Brightness adjustment. |
| `contrast` | number | `-100` to `100` | Contrast adjustment. |
| `saturation` | number | `0+` | Saturation multiplier. |
| `temperature` | number | `-100` to `100` | Color temperature shift. |
| `exposure` | number | `-5` to `5` | Exposure adjustment in stops. |
| `gamma` | number | `0.1` to `10` | Gamma correction. |

### Brightness/Contrast (`brightnessContrast`)

Purpose: Quick tonal tuning.

| Param | Type | Range | Description |
|---|---|---|---|
| `brightness` | number | `-100` to `100` | Brightness. |
| `contrast` | number | `-100` to `100` | Contrast. |

### Hue/Saturation (`hueSaturation`)

Purpose: Palette shifting and intensity.

| Param | Type | Range | Description |
|---|---|---|---|
| `hue` | number | `-180` to `180` | Hue shift in degrees. |
| `saturation` | number | `0+` | Saturation multiplier. |
| `lightness` | number | `-100` to `100` | Lightness adjustment. |

### Levels (`levels`)

Purpose: Input/output remapping.

| Param | Type | Range | Description |
|---|---|---|---|
| `inputBlack` | number | `0-255` | Input black point. |
| `inputWhite` | number | `0-255` | Input white point. |
| `outputBlack` | number | `0-255` | Output black point. |
| `outputWhite` | number | `0-255` | Output white point. |
| `gamma` | number | `0.1` to `10` | Midtone gamma. |

### Vignette (`vignette`)

Purpose: Edge darkening/focus.

| Param | Type | Range | Description |
|---|---|---|---|
| `amount` | number | `0-1` | Vignette intensity. |
| `roundness` | number | `0-1` | Shape roundness. |
| `feather` | number | `0-1` | Edge softness. |

```json
{
  "id": "vig_1",
  "type": "vignette",
  "enabled": true,
  "params": {
    "amount": 0.25,
    "roundness": 0.8,
    "feather": 0.5
  },
  "keyframes": null
}
```

## Styling Effects

### Noise (`noise`)

Purpose: Grain and texture.

| Param | Type | Range | Description |
|---|---|---|---|
| `amount` | number | `0-100` | Noise intensity. |
| `size` | number | `1+` | Grain size. |

### Chroma Key (`chromaKey`)

Purpose: Green/blue screen keying.

| Param | Type | Range | Description |
|---|---|---|---|
| `keyColor` | string | Hex color | Color to remove. |
| `tolerance` | number | `0-100` | Keying tolerance. |
| `edgeSoftness` | number | `0-100` | Edge feathering. |

## See Also

- [file-format.md](file-format.md) - Complete .outocut format specification
- [transforms.md](transforms.md) - Transform property reference
- [coordinate-system.md](coordinate-system.md) - Position and coordinate reference
