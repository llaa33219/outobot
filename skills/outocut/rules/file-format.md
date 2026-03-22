# .outocut File Format Specification

Author: BLOUplanet  
License: Apache 2.0  

This document defines the full `.outocut` project format as implemented by OutOcut v1.0 (`src/models.rs`, `src/parser.rs`, `src/animation.rs`).

## File Structure Overview

```json
{
  "version": "1.0",
  "metadata": { ... },
  "settings": { ... },
  "assets": [ ... ],
  "compositions": { ... },
  "mainCompositionId": "comp_main",
  "exportPresets": [ ... ]
}
```

Top-level keys are all required by the Rust `Project` struct.

## 1. `version`

- Type: `string`
- Value: `"1.0"` (currently only supported version)
- Required: Yes

```json
"version": "1.0"
```

Notes:
- The parser deserializes any string, but current engine/docs are v1.0-oriented.
- Use `"1.0"` for compatibility.

## 2. `metadata`

```json
{
  "name": "My Project",
  "created": "2026-03-18T00:00:00Z",
  "author": "Your Name",
  "description": "Optional description",
  "tags": ["tag1", "tag2"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Project display name. |
| `created` | ISO-8601 datetime string | Yes | Parsed as `DateTime<Utc>`. |
| `author` | `string \| null` | No | Author name. |
| `description` | `string \| null` | No | Project description. |
| `tags` | `string[]` | Yes | Tags list (can be empty). |

## 3. `settings`

```json
{
  "width": 1920,
  "height": 1080,
  "fps": 30.0,
  "duration": 60.0,
  "backgroundColor": "#000000",
  "pixelAspect": 1.0,
  "sampleRate": 48000,
  "audioChannels": 2
}
```

Field details:
- `width` / `height`: Resolution in pixels.
- `fps`: Frames per second (affects keyframe time interpretation).
- `duration`: Project duration in seconds.
- `backgroundColor`: Composition background color in hex string form.
- `pixelAspect`: Pixel aspect ratio (usually `1.0`).
- `sampleRate`: Audio sample rate (Hz).
- `audioChannels`: Number of audio channels (`1` = mono, `2` = stereo).

Validation behavior:
- `width > 0`
- `height > 0`
- `fps > 0`
- `duration > 0`

## 4. `assets`

Array of asset references:

```json
[
  {
    "id": "asset-1",
    "type": "video|audio|image|font",
    "path": "./media/video.mp4",
    "trimStart": 0.0,
    "trimEnd": null
  }
]
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Unique asset ID (project-wide best practice). |
| `type` | `AssetType` | Yes | `video`, `audio`, `image`, `font`. |
| `path` | `string` | Yes | File path (use relative path recommended). |
| `trimStart` | `number \| null` | No | Optional start trim in seconds. |
| `trimEnd` | `number \| null` | No | Optional end trim in seconds. |

## 5. `compositions`

HashMap of composition objects:

```json
{
  "comp_main": {
    "id": "comp_main",
    "duration": 60.0,
    "width": 1920,
    "height": 1080,
    "layers": [ ... ]
  },
  "comp_precomp": { ... }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | Yes | Composition ID value. |
| `duration` | `number` | Yes | Duration in seconds. |
| `width` | `u32` | Yes | Composition width. |
| `height` | `u32` | Yes | Composition height. |
| `layers` | `Layer[]` | Yes | Ordered layer stack (first = back, last = front). |

Important runtime check:
- `compositions[mainCompositionId].duration` must equal `settings.duration`.

## 6. `mainCompositionId`

- Type: `string`
- Value: ID/key of composition to render/export
- Required: Yes

```json
"mainCompositionId": "main"
```

Must match an actual key in `compositions` exactly (case-sensitive).

## 7. `exportPresets`

```json
[
  {
    "name": "youtube",
    "codec": "h264",
    "crf": 18,
    "preset": "slow"
  }
]
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Preset label. |
| `codec` | `string` | Yes | Target codec name. |
| `crf` | `u8 \| null` | No | Optional constant-rate-factor value. |
| `preset` | `string \| null` | No | Optional encoder preset. |

## Layer JSON Structure

Complete base layer structure with all possible fields:

```json
{
  "id": "layer_text_title",
  "type": "text",
  "name": "Main Title",
  "enabled": true,
  "startTime": 0.0,
  "duration": 6.0,
  "inPoint": 0.0,
  "outPoint": 6.0,
  "parentId": null,
  "trackMatte": "alpha",
  "blendMode": "screen",
  "opacity": {
    "value": 100,
    "keyframes": [
      { "time": 0.0, "value": 0, "easing": "easeOut" },
      { "time": 0.6, "value": 100 }
    ]
  },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "text": "HELLO",
    "fontId": "font_ui",
    "fontSize": 96,
    "color": "#FFFFFF",
    "tracking": 12,
    "leading": 110,
    "alignment": "center",
    "baselineShift": 0
  },
  "shapeContents": null,
  "effects": [
    {
      "id": "fx_glow_title",
      "type": "glow",
      "enabled": true,
      "params": { "radius": 16, "color": "#77CCFF", "opacity": 45 },
      "keyframes": null
    }
  ],
  "masks": [
    {
      "name": "title_mask",
      "mode": "add",
      "path": [
        { "x": 400, "y": 220, "handleIn": null, "handleOut": null },
        { "x": 1520, "y": 220, "handleIn": null, "handleOut": null },
        { "x": 1520, "y": 860, "handleIn": null, "handleOut": null },
        { "x": 400, "y": 860, "handleIn": null, "handleOut": null }
      ],
      "feather": 0,
      "opacity": 100
    }
  ]
}
```

Layer field reference:

> **Coordinate System**: All position values use top-left origin `(0,0)`. See [coordinate-system.md](coordinate-system.md) for full details.

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `string` | Yes | Unique within the composition. |
| `type` | `LayerType` | Yes | Layer kind (video/audio/text/etc.). |
| `name` | `string \| null` | No | Display name. |
| `enabled` | `boolean` | Yes | Disabled layers are skipped. |
| `startTime` | `number` | Yes | Timeline start in seconds. |
| `duration` | `number` | Yes | Active span length in seconds. |
| `inPoint` | `number \| null` | No | Additional trim-in offset. |
| `outPoint` | `number \| null` | No | Additional trim-out offset. |
| `parentId` | `string \| null` | No | Parent layer ID. |
| `trackMatte` | `TrackMatte \| null` | No | Matte behavior. |
| `blendMode` | `BlendMode \| null` | No | Blend operation. |
| `opacity` | `AnimatedProperty<f64>` | Yes | Layer opacity value/keys. |
| `transform` | `Transform` | Yes | Anchor/position/scale/rotation/skew/skewAxis. All position values use top-left origin. |
| `content` | type-dependent object or `null` | Depends | Payload for non-shape layers. |
| `shapeContents` | `ShapeContent[] \| null` | Shape layers | Shape stack. |
| `effects` | `Effect[] \| null` | No | Layer effect stack. |
| `masks` | `Mask[] \| null` | No | Layer masks. Mask coordinates are in composition space (absolute positions). |

### Type-specific `content` objects

| Layer `type` | `content` shape |
|---|---|
| `video` | `{ "assetId": "asset_video_id" }` |
| `audio` | `{ "assetId": "asset_audio_id" }` |
| `image` | `{ "assetId": "asset_image_id" }` |
| `text` | `{ "text", "fontId", "fontSize", "color", "tracking", "leading", "alignment", "baselineShift" }` |
| `shape` | usually `null` (use `shapeContents`) |
| `solid` | `{ "color": "#RRGGBB" }` |
| `null` | usually `null` |
| `adjustment` | usually `null` |
| `composition` | `{ "compositionId": "comp_key" }` |

### `AnimatedProperty` and `Keyframe`

```json
{
  "value": [960, 540],
  "keyframes": [
    { "time": 0.0, "value": [960, 600], "easing": "easeOutCubic" },
    { "time": 0.8, "value": [960, 540] }
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `value` | any JSON value | Yes | Static/fallback value. |
| `keyframes` | `Keyframe[] \| null` | No | Optional animation curve. |

Keyframe structure:

| Field | Type | Required | Description |
|---|---|---|---|
| `time` | `f64` | Yes | Seconds. |
| `value` | JSON value | Yes | Value at this key. |
| `easing` | `Easing \| null` | No | Segment easing from this key to next. |

## Comment Support

- OutOcut files support `// single-line comments`.
- OutOcut files support `/* multi-line comments */`.
- Comments are stripped before JSON parsing.

Parser behavior details:
- Comment stripping only applies outside string literals.
- Escaped quotes inside strings are handled correctly.
- `http://...` inside strings is preserved.

## Schema Reference (Enums and JSON String Values)

### `AssetType`

| Enum variant | JSON value |
|---|---|
| `Video` | `video` |
| `Audio` | `audio` |
| `Image` | `image` |
| `Font` | `font` |

### `LayerType`

| Enum variant | JSON value |
|---|---|
| `Video` | `video` |
| `Audio` | `audio` |
| `Image` | `image` |
| `Text` | `text` |
| `Shape` | `shape` |
| `Solid` | `solid` |
| `Null` | `null` |
| `Adjustment` | `adjustment` |
| `Composition` | `composition` |

### `TrackMatte`

| Enum variant | JSON value |
|---|---|
| `Alpha` | `alpha` |
| `AlphaInverted` | `alphaInverted` |
| `Luma` | `luma` |
| `LumaInverted` | `lumaInverted` |

### `BlendMode`

| Enum variant | JSON value |
|---|---|
| `Normal` | `normal` |
| `Multiply` | `multiply` |
| `Screen` | `screen` |
| `Overlay` | `overlay` |
| `Darken` | `darken` |
| `Lighten` | `lighten` |
| `ColorDodge` | `colorDodge` |
| `ColorBurn` | `colorBurn` |
| `HardLight` | `hardLight` |
| `SoftLight` | `softLight` |
| `Difference` | `difference` |
| `Exclusion` | `exclusion` |
| `Hue` | `hue` |
| `Saturation` | `saturation` |
| `Color` | `color` |
| `Luminosity` | `luminosity` |
| `Add` | `add` |
| `Subtract` | `subtract` |
| `Divide` | `divide` |

### `TextAlignment`

| Enum variant | JSON value |
|---|---|
| `Left` | `left` |
| `Center` | `center` |
| `Right` | `right` |
| `Justify` | `justify` |

### `ShapeType`

| Enum variant | JSON value |
|---|---|
| `Rect` | `rect` |
| `Ellipse` | `ellipse` |
| `Star` | `star` |
| `Polygon` | `polygon` |
| `Path` | `path` |
| `Fill` | `fill` |
| `Stroke` | `stroke` |
| `Repeater` | `repeater` |
| `Group` | `group` |

### `EffectType`

| Enum variant | JSON value |
|---|---|
| `DropShadow` | `dropShadow` |
| `InnerShadow` | `innerShadow` |
| `Glow` | `glow` |
| `OuterGlow` | `outerGlow` |
| `GaussianBlur` | `gaussianBlur` |
| `DirectionalBlur` | `directionalBlur` |
| `RadialBlur` | `radialBlur` |
| `Crop` | `crop` |
| `Rotate` | `rotate` |
| `Flip` | `flip` |
| `Mirror` | `mirror` |
| `ColorCorrection` | `colorCorrection` |
| `BrightnessContrast` | `brightnessContrast` |
| `HueSaturation` | `hueSaturation` |
| `Levels` | `levels` |
| `Curves` | `curves` |
| `ChromaKey` | `chromaKey` |
| `Noise` | `noise` |
| `Vignette` | `vignette` |
| `GlowEffect` | `glowEffect` |
| `Stroke` | `stroke` |
| `FillGradient` | `fillGradient` |
| `TrimPath` | `trimPath` |
| `Wiggle` | `wiggle` |
| `TextAnimator` | `textAnimator` |

### `MaskMode`

| Enum variant | JSON value |
|---|---|
| `Add` | `add` |
| `Subtract` | `subtract` |
| `Intersect` | `intersect` |
| `Lighten` | `lighten` |
| `Darken` | `darken` |
| `Difference` | `difference` |
| `None` | `none` |

### `Easing`

String easings:

| Enum variant | JSON value |
|---|---|
| `Linear` | `linear` |
| `EaseIn` | `easeIn` |
| `EaseOut` | `easeOut` |
| `EaseInOut` | `easeInOut` |
| `EaseInCubic` | `easeInCubic` |
| `EaseOutCubic` | `easeOutCubic` |
| `EaseInOutCubic` | `easeInOutCubic` |
| `EaseInBack` | `easeInBack` |
| `EaseOutBack` | `easeOutBack` |
| `EaseInOutBack` | `easeInOutBack` |
| `EaseInElastic` | `easeInElastic` |
| `EaseOutElastic` | `easeOutElastic` |
| `EaseInOutElastic` | `easeInOutElastic` |
| `EaseInBounce` | `easeInBounce` |
| `EaseOutBounce` | `easeOutBounce` |
| `EaseInOutBounce` | `easeInOutBounce` |

Custom cubic-bezier form:

```json
{ "cubicBezier": [0.42, 0.0, 0.58, 1.0] }
```

## Complete Example File

This example demonstrates comments, all top-level sections, all layer types, animation, masks, effects, precomposition, track matte, and export presets.

See the source file at `/home/luke/outocut/ai-docs/usage/file-format.md` for the complete example (lines 467-1062).

## Cautions

> **Coordinate System**: OutOcut uses top-left origin `(0,0)`. X increases rightward, Y increases downward. See [coordinate-system.md](coordinate-system.md) for full details.

- All IDs should be unique within the project (`assets[].id`, composition keys, composition `id`, and `layers[].id` per composition).
- `mainCompositionId` must match a composition key exactly.
- Asset `path` values are resolved relative to the project file location (recommended workflow).
- All time/duration values are in seconds, not frames.
- Keep `settings.duration` and main composition `duration` equal, or validation fails.
- Enum strings are case-sensitive; use exact values from the schema tables above.
- **Position values** (`position`, `anchor`, `shape.position`, `mask.path.x/y`) use top-left origin. A `position` of `[0, 0]` places the element at the top-left corner of the composition or layer.
