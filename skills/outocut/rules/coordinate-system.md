# Coordinate System

Comprehensive reference for OutOcut's coordinate system, spatial conventions, and bounds.

- **Author**: BLOUplanet
- **License**: Apache 2.0
- **Requires**: OutOcut v1.0+

---

## Overview

> ⚠️ **AI AGENT COORDINATE WARNING**
>
> **CRITICAL**: Many AI agents incorrectly assume `(0, 0)` is at the **center** of the canvas or at the **bottom-left**.
>
> **OUTOCUT CONVENTION**: `(0, 0)` is ALWAYS at the **TOP-LEFT** corner.
> - Center of a 1920×1080 canvas is `[960, 540]`, NOT `[0, 0]`
> - Bottom-left is `[0, height]`, NOT `[0, 0]`
> - When positioning elements, `(0, 0)` means top-left, not center

OutOcut uses a **standard 2D graphics coordinate system** where:

| Property | Value | Description |
|----------|-------|-------------|
| **Origin** | `(0, 0)` | **TOP-LEFT** corner of the canvas |
| **X-axis** | Positive → Right | Horizontal position increases rightward |
| **Y-axis** | Positive ↓ Down | Vertical position increases downward |
| **Angle** | Positive ↻ Clockwise | Rotation values increase clockwise |
| **Bounds X** | `0` to `width - 1` | Valid horizontal pixel indices |
| **Bounds Y** | `0` to `height - 1` | Valid vertical pixel indices |

This matches common industry conventions (CSS, Canvas, SVG, After Effects, etc.) and ensures intuitive layout behavior.

---

## Coordinate Spaces

OutOcut defines three nested coordinate spaces. Understanding the distinction is critical for correct positioning.

### 1. Composition Space

The outermost space representing the entire render canvas.

- **Bounds**: `(0, 0)` to `(width - 1, height - 1)`
- **Example**: A 1920×1080 composition spans from `(0, 0)` to `(1919, 1079)`
- **Used by**: `position` (layer transform)

```
(0,0) ───────────────────────────────────────────── (1919, 0)
   │                                                    │
   │                                                    │
   │                 Composition Space                   │
   │                   1920 × 1080                     │
   │                                                    │
   │                                                    │
(0,1079) ─────────────────────────────────────── (1919, 1079)
```

### 2. Layer Space

The coordinate system local to each layer, used for transforms and content placement within the layer.

> ⚠️ **AI AGENT WARNING: Layer Space Origin is TOP-LEFT, not Center**
>
> **CRITICAL**: Many AI agents incorrectly assume `(0, 0)` in layer space is at the **layer's center**.
>
> **OUTOCUT CONVENTION**: Layer space `(0, 0)` is at the **TOP-LEFT** of the layer content.
> - `anchor: [0, 0]` = top-left corner of layer
> - `anchor: [width/2, height/2]` = **center** of layer
> - The `anchor` value DEFINE where (0,0) is, NOT that (0,0) is the center

- **Origin**: Defined by the layer's `anchor` value
- **Bounds**: Depends on layer content size
- **Used by**: `anchor`, `scale`, `rotation`, `skew`

```
Layer Space (origin at anchor point)

(-anchor_x, -anchor_y)    Layer Content    (width - anchor_x, -anchor_y)
         ┌─────────────────────────────────────┐
         │                                     │
         │              Layer                  │
         │            Content                  │
         │                                     │
         └─────────────────────────────────────┘
(-anchor_x, height - anchor_y)          (width - anchor_x, height - anchor_y)
```

### 3. Shape Space

The coordinate system local to individual shapes within a shape layer.

- **Origin**: Top-left of the shape layer's content area
- **Used by**: `shapeContents[].position`

```
┌─────────────────────────────────────────────┐
│  Shape Space                                │
│                                             │
│   (0,0) ───────────────────────── (size[0], 0)  │
│     │                                        │  │
│     │  ┌──────────────────────┐              │  │
│     │  │     Shape            │              │  │
│     │  │  position: [50,30]   │              │  │
│     │  └──────────────────────┘              │  │
│     │                                        │  │
│   (0,size[1])                   (size[0], size[1])│
└─────────────────────────────────────────────┘
```

---

## Center Calculation

Many operations require the center point of a composition or layer.

### Composition Center

```text
center_x = width / 2
center_y = height / 2

1920×1080 → [960, 540]
1280×720  → [640, 360]
3840×2160 → [1920, 1080]
```

### Layer Center

```text
center_x = layer_width / 2
center_y = layer_height / 2

For a 400×200 layer → [200, 100]
```

### Anchor Center

```text
For a 400×200 layer, center anchor = [200, 100]
```

### Quick Reference Table

| Resolution | Center Position |
|------------|----------------|
| 1920×1080  | [960, 540]     |
| 1280×720   | [640, 360]     |
| 3840×2160  | [1920, 1080]   |
| 1080×1080  | [540, 540]     |
| 1920×540   | [960, 270]     |

---

## Position Behavior

### Layer Position (`position`)

`position` places the layer's anchor point in composition space.

- **Coordinate Space**: Composition
- **Default**: `[0, 0]` (top-left of composition)
- **Behavior**: The layer's anchor point lands at the specified `(x, y)` in the composition

```json
// Layer with anchor at center, positioned at composition center
"transform": {
  "anchor": { "value": [200, 100] },
  "position": { "value": [960, 540] }
}
```

### Shape Position (`position`)

`shapeContents[].position` offsets the shape within the shape layer's local space.

- **Coordinate Space**: Shape/Layer space (relative to shape layer origin)
- **Default**: `[0, 0]` (top-left of layer content)
- **Behavior**: Shape's top-left corner is offset by `(x, y)` from layer origin

---

## Transform Coordinate System

Transforms operate in layer space, with `anchor` defining the origin.

> ⚠️ **AI AGENT WARNING: Do NOT Confuse Layer Space (0,0) with Layer Center**
>
> **WRONG assumption**: "`(0, 0)` in layer coordinates means the layer's center"
>
> **CORRECT understanding**:
> - Layer space `(0, 0)` is at the **TOP-LEFT** of the layer content
> - `anchor` is a **user-defined point** that becomes the origin of layer space
> - `anchor: [0, 0]` → origin is top-left
> - `anchor: [200, 100]` → origin is at position (200, 100) within the layer
>
> **When centering a layer**: You set `anchor: [width/2, height/2]` AND set `position` to composition center

### Anchor (`anchor`)

The anchor point is the transform origin in layer-local coordinates.

| Anchor Value | Transform Origin |
|--------------|-----------------|
| `[0, 0]` | Top-left corner of layer |
| `[width/2, height/2]` | Center of layer |
| `[width, height]` | Bottom-right corner of layer |

### Scale (`scale`)

Scales the layer relative to its anchor point.

- **Unit**: Percentage (`100` = 100%, no change)
- **Negative values**: Flip along that axis

### Rotation (`rotation`)

Rotates the layer around the anchor point.

- **Unit**: Degrees
- **Direction**: Clockwise is positive

---

## Mask Coordinate System

Masks use composition space coordinates by default (relative to the layer's position).

### MaskPoint Structure

```json
{
  "x": 400,
  "y": 300,
  "handleIn": [-30, 0],
  "handleOut": [30, 0]
}
```

### Coordinate Space

Mask coordinates are in **composition space**, meaning they are absolute positions on the canvas, NOT relative to the layer.

---

## Common Patterns

### 1. Center a Layer

```json
"transform": {
  "anchor": { "value": [200, 100] },
  "position": { "value": [960, 540] }
}
```

### 2. Position Layer at Top-Left

```json
"transform": {
  "anchor": { "value": [0, 0] },
  "position": { "value": [0, 0] }
}
```

### 3. Position Layer at Top-Right

```json
"transform": {
  "anchor": { "value": [0, 0] },
  "position": { "value": [1920, 0] }
}
```

### 4. Position Layer at Bottom-Right

```json
"transform": {
  "anchor": { "value": [0, 0] },
  "position": { "value": [1920, 1080] }
}
```

---

## Comparison with Other Tools

| Tool | Origin | Y-axis Direction |
|------|--------|-----------------|
| **OutOcut** | Top-left | ↓ Down |
| After Effects | Top-left | ↓ Down |
| CSS | Top-left | ↓ Down |
| Canvas 2D | Top-left | ↓ Down |
| SVG | Top-left | ↓ Down |
| Unity 2D | Bottom-left | ↑ Up |
| OpenGL | Bottom-left | ↑ Up (or center) |

---

## Quick Reference

```
┌──────────────────────────────────────────────────────────┐
│  OutOcut Coordinate System                             │
│                                                          │
│  (0,0) ──────────────────────────────────── (width,0)   │
│    │                                              │      │
│    │   X: increases → right                      │      │
│    │   Y: increases ↓ down                      │      │
│    │                                              │      │
│    │   Angle: increases ↻ clockwise             │      │
│    │                                              │      │
│    │   center_x = width / 2                      │      │
│    │   center_y = height / 2                     │      │
│    │                                              │      │
│ (0,height) ───────────────────────────── (width,height) │
└──────────────────────────────────────────────────────────┘
```

---

## See Also

- [transforms.md](transforms.md) - Detailed transform property reference
- [shapes-masks.md](shapes-masks.md) - Shape and mask data structures
- [file-format.md](file-format.md) - Complete .outocut format specification
