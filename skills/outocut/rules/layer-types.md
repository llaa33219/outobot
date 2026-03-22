# OutOcut Layer Types

Author: BLOUplanet  
License: Apache 2.0

This guide documents all OutOcut layer types in practical detail.

## Common Layer Model (applies to all layer types)

Every layer in `composition.layers` follows the same base structure. Type-specific data is stored in `content` and/or `shapeContents`.

```json
{
  "id": "layer_unique_id",
  "type": "text",
  "name": "Layer Name",
  "enabled": true,
  "startTime": 0.0,
  "duration": 5.0,
  "inPoint": 0.0,
  "outPoint": 5.0,
  "parentId": null,
  "trackMatte": null,
  "blendMode": null,
  "opacity": {
    "value": 100,
    "keyframes": null
  },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {},
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### Common fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique layer identifier in the composition. |
| `type` | enum | Yes | One of: `video`, `audio`, `image`, `text`, `shape`, `solid`, `null`, `adjustment`, `composition`. |
| `name` | string or null | No | Human-readable label. |
| `enabled` | boolean | Yes | If false, layer is skipped. |
| `startTime` | number | Yes | Layer start time in composition timeline seconds. |
| `duration` | number | Yes | Layer span length in seconds. |
| `inPoint` | number or null | No | Trim-in relative to layer start. |
| `outPoint` | number or null | No | Trim-out relative to layer start. |
| `parentId` | string or null | No | Parent layer id for transform hierarchy/grouping. |
| `trackMatte` | enum or null | No | `alpha`, `alphaInverted`, `luma`, `lumaInverted`. |
| `blendMode` | enum or null | No | Blend mode for compositing. |
| `opacity` | object | Yes | `AnimatedProperty<f64>` (0-100 typical). |
| `transform` | object | Yes | Anchor, position, scale, rotation, skew, skewAxis; each animated. |
| `content` | object or null | Depends on type | Type-specific payload. |
| `shapeContents` | array or null | Shape layers | Shape primitives/operators. |
| `effects` | array or null | No | Layer effect stack. |
| `masks` | array or null | No | Layer masks. |

### Active-time behavior

A layer is active when all conditions are true:
- `time >= startTime`
- `time < startTime + duration`
- `time >= startTime + (inPoint or 0)`
- `time < startTime + (outPoint or duration)`

### Parent/child relationships

Use `parentId` to build hierarchies:
- Child layers inherit logical relationship to parent (grouping/rigging intent).
- Use a `null` layer as a clean controller/anchor for many children.

### Layer ordering and z-index

In a composition, layers are processed in array order:
- Earlier entries render first (back).
- Later entries render on top (front).

So for `layers: [A, B, C]`:
- `A` is bottom-most
- `C` is top-most

## Layer Types

### 1) `video` layer

Use `video` layers for footage clips (camera shots, B-roll, screen captures, pre-rendered animations).

```json
{
  "id": "layer_video_intro",
  "type": "video",
  "name": "Intro Footage",
  "enabled": true,
  "startTime": 0.0,
  "duration": 8.0,
  "inPoint": 0.5,
  "outPoint": 7.5,
  "parentId": null,
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "assetId": "vid_intro"
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 2) `audio` layer

Use `audio` layers for music, voice-over, SFX, and ambience.

```json
{
  "id": "layer_audio_bgm",
  "type": "audio",
  "name": "Background Music",
  "enabled": true,
  "startTime": 0.0,
  "duration": 30.0,
  "inPoint": 0.0,
  "outPoint": 30.0,
  "parentId": null,
  "trackMatte": null,
  "blendMode": null,
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [0, 0], "keyframes": null },
    "position": { "value": [0, 0], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "assetId": "aud_music_main"
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 3) `image` layer

Use `image` for logos, photos, still overlays, and UI captures.

```json
{
  "id": "layer_image_logo",
  "type": "image",
  "name": "Brand Logo",
  "enabled": true,
  "startTime": 1.0,
  "duration": 9.0,
  "inPoint": 0.0,
  "outPoint": 9.0,
  "parentId": "ctrl_brand_group",
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [100, 100], "keyframes": null },
    "position": { "value": [1800, 980], "keyframes": null },
    "scale": { "value": [60, 60], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "assetId": "img_logo"
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 4) `text` layer

Use `text` layers for titles, lower-thirds, captions, CTAs, labels, and kinetic typography.

Required text fields:
- `text` (string)
- `fontSize` (number)
- `color` (string, typically hex)

Optional text fields:
- `fontId` (string or null, references a font asset)
- `tracking` (number or null)
- `leading` (number or null)
- `alignment` (`left` | `center` | `right` | `justify`)
- `baselineShift` (number or null)

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
  "parentId": "ctrl_title_group",
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "text": "OUTOCUT LAYER SYSTEM",
    "fontId": "font_heading_semibold",
    "fontSize": 84,
    "color": "#f7f7f7",
    "tracking": 18,
    "leading": 96,
    "alignment": "center",
    "baselineShift": 0
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 5) `shape` layer

Use `shape` layers for vector graphics, backgrounds, bars, badges, icons, motion design elements, and procedural geometry rigs.

Shape layers use `shapeContents` array with shape primitives:
- `rect` - Rectangle
- `ellipse` - Ellipse/Circle
- `star` - Star shape
- `polygon` - Polygon
- `path` - Bezier path
- `fill` - Solid color fill
- `stroke` - Stroke/outline
- `repeater` - Duplicate shape
- `group` - Group shapes

```json
{
  "id": "layer_shape_panel",
  "type": "shape",
  "name": "Panel",
  "enabled": true,
  "startTime": 0.5,
  "duration": 9.5,
  "inPoint": 0.0,
  "outPoint": 9.5,
  "parentId": "ctrl_title_group",
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": null,
  "shapeContents": [
    {
      "type": "rect",
      "name": "Card",
      "size": [1320, 560],
      "position": [300, 260],
      "roundness": 28,
      "color": "#121A2BEE"
    },
    {
      "type": "stroke",
      "name": "CardStroke",
      "color": "#88B7FF",
      "width": 3
    }
  ],
  "effects": null,
  "masks": null
}
```

### 6) `solid` layer

Use `solid` for color background layers and flat color elements.

```json
{
  "id": "layer_bg",
  "type": "solid",
  "name": "Background",
  "enabled": true,
  "startTime": 0.0,
  "duration": 60.0,
  "inPoint": null,
  "outPoint": null,
  "parentId": null,
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "color": "#0A0F1A"
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 7) `null` layer

Use `null` layers as parent controllers/anchors for grouping and organizing related layers.

```json
{
  "id": "ctrl_title_block",
  "type": "null",
  "name": "Title Block Controller",
  "enabled": true,
  "startTime": 0.0,
  "duration": 14.0,
  "inPoint": 0.0,
  "outPoint": 14.0,
  "parentId": null,
  "trackMatte": null,
  "blendMode": null,
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": null,
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

### 8) `adjustment` layer

Use `adjustment` layers to apply effects to all layers below without rendering visible content itself.

```json
{
  "id": "layer_adjustment_grade",
  "type": "adjustment",
  "name": "Global Grade",
  "enabled": true,
  "startTime": 0.0,
  "duration": 60.0,
  "inPoint": null,
  "outPoint": null,
  "parentId": null,
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": null,
  "shapeContents": null,
  "effects": [
    {
      "id": "fx_grade",
      "type": "colorCorrection",
      "enabled": true,
      "params": { "temperature": -2, "contrast": 1.08, "saturation": 102 }
    },
    {
      "id": "fx_vignette",
      "type": "vignette",
      "enabled": true,
      "params": { "amount": 0.18, "roundness": 0.65 }
    }
  ],
  "masks": null
}
```

### 9) `composition` layer

Use `composition` layers to embed/reference other compositions (pre-comps) within the current composition.

```json
{
  "id": "layer_precomp",
  "type": "composition",
  "name": "Nested Composition",
  "enabled": true,
  "startTime": 18.0,
  "duration": 20.0,
  "inPoint": 0.0,
  "outPoint": 20.0,
  "parentId": null,
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": {
    "compositionId": "comp_precomp"
  },
  "shapeContents": null,
  "effects": null,
  "masks": null
}
```

## Common Pitfalls

- `assetId` must reference an existing asset in top-level `assets`.
- Ensure `duration` and `outPoint` match intended clip length logic.
- Check image dimensions and intended anchor/position math.
- Missing `fontSize` or `color` makes text content invalid.
- Keep audio layer timing explicit with `startTime`, `inPoint`, and `outPoint`.

## See Also

- [file-format.md](file-format.md) - Complete .outocut format specification
- [transforms.md](transforms.md) - Transform property reference
- [effects.md](effects.md) - Effect reference
- [blend-modes.md](blend-modes.md) - Blend mode reference
