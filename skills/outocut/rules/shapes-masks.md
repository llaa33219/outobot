# Shapes and Masks

Comprehensive reference for OutOcut shape and mask data in `.outocut` files.

- **Author**: BLOUplanet
- **License**: Apache 2.0

## Overview

Shapes and masks are layer-level vector constructs:

- Shapes live in `layer.shapeContents` (array of `ShapeContent` objects).
- Masks live in `layer.masks` (array of `Mask` objects).
- A shape layer can contain multiple shapes, plus normal layer transforms, opacity, blend mode, and effects.
- Shape and mask values are JSON data and can be combined with keyframed layer properties for animation.

---

## Part 1: Shape System

### ShapeType enum values

`ShapeType` uses lowercase JSON values.

| Value | Name | Purpose |
|---|---|---|
| `rect` | Rectangle | Axis-aligned rectangle, optionally rounded corners via `roundness` |
| `ellipse` | Ellipse / circle | Oval shape defined by `size` |
| `star` | Star shape | Star primitive (renderer/engine-dependent interpretation) |
| `polygon` | Regular polygon | N-sided regular shape (renderer/engine-dependent interpretation) |
| `path` | Custom path (vector) | Arbitrary vector path marker for custom pipelines |
| `fill` | Fill area | Fill operation/color in shape stack semantics |
| `stroke` | Stroke/outline | Outline operation with `width` and `color` |
| `repeater` | Repeat shape multiple times | Repetition operator using `copies` and `offset` |
| `group` | Group multiple shapes | Logical grouping node for shape stack organization |

### ShapeContent structure

> **Coordinate Reference**: Shape positions use top-left origin `(0,0)`. For full details, see [Coordinate System](coordinate-system.md).

Each item in `shapeContents` is a `ShapeContent` object:

```json
{
  "type": "rect",
  "name": "optional_name",
  "size": [400, 240],
  "position": [200, 120],
  "roundness": 24,
  "color": "#33AAFF",
  "width": 6,
  "copies": 8,
  "offset": [20, 12]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | `ShapeType` | Yes | Shape primitive/operator type |
| `name` | `string` | No | Human-readable label |
| `size` | `[number, number]` | No | Width/height tuple (from top-left of shape) |
| `position` | `[number, number]` | No | Offset from shape layer origin `(0,0)` — top-left origin |
| `roundness` | `number` | No | Rectangle corner radius |
| `color` | `string` | No | Hex color (`#RRGGBB` or renderer-supported variant) |
| `width` | `number` | No | Stroke width |
| `copies` | `integer` | No | Repeater copy count |
| `offset` | `[number, number]` | No | Repeater x/y step offset |

### Position Field Details

`position` defines the shape's offset within the shape layer's local coordinate space:

```
┌─────────────────────────────────────────────┐
│  Shape Layer Space                          │
│                                             │
│  (0,0) ───────────────────────── (size[0], 0)│
│    │                                        │  │
│    │  ┌──────────────────────┐              │  │
│    │  │     Shape            │              │  │
│    │  │  position: [50,30]   │              │  │
│    │  │                      │              │  │
│    │  └──────────────────────┘              │  │
│    │                                        │  │
│  (0,size[1])                   (size[0],size[1])│
└─────────────────────────────────────────────┘

position[0] = X offset from layer left edge
position[1] = Y offset from layer top edge
```

### Shape layer usage

Important usage rules:

- Shape layers use `shapeContents` (array), not `content`.
- `content` is usually `null` for `"type": "shape"` layers.
- Multiple shape entries can exist in one layer.
- A shape layer can still use `effects`, transform keyframes, blending, and opacity.

Practical shape layer skeleton:

```json
{
  "id": "shape_layer_ui",
  "type": "shape",
  "name": "UI Shapes",
  "enabled": true,
  "startTime": 0,
  "duration": 8.0,
  "inPoint": 0,
  "outPoint": 8.0,
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [0, 0], "keyframes": null },
    "position": { "value": [0, 0], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": null,
  "shapeContents": [
    {
      "type": "rect",
      "name": "CardBase",
      "size": [640, 360],
      "position": [120, 100],
      "roundness": 28,
      "color": "#1E293B",
      "width": null,
      "copies": null,
      "offset": null
    },
    {
      "type": "stroke",
      "name": "CardOutline",
      "size": [640, 360],
      "position": [120, 100],
      "roundness": 28,
      "color": "#38BDF8",
      "width": 4,
      "copies": null,
      "offset": null
    }
  ],
  "effects": [
    {
      "id": "glow_card",
      "type": "glow",
      "enabled": true,
      "params": { "radius": 20, "color": "#38BDF8", "opacity": 35 },
      "keyframes": null
    }
  ],
  "masks": []
}
```

### JSON examples for every shape type

Use these as drop-in `shapeContents` entries.

#### 1) `rect` (Rectangle)

```json
{
  "type": "rect",
  "name": "HeroRect",
  "size": [800, 300],
  "position": [120, 80],
  "roundness": 36,
  "color": "#0EA5E9",
  "width": null,
  "copies": null,
  "offset": null
}
```

#### 2) `ellipse` (Ellipse / circle)

```json
{
  "type": "ellipse",
  "name": "CircleBadge",
  "size": [180, 180],
  "position": [860, 120],
  "roundness": null,
  "color": "#F43F5E",
  "width": null,
  "copies": null,
  "offset": null
}
```

#### 3) `star` (Star shape)

```json
{
  "type": "star",
  "name": "Spark",
  "size": [120, 120],
  "position": [300, 260],
  "roundness": 0,
  "color": "#F59E0B",
  "width": null,
  "copies": null,
  "offset": null
}
```

#### 4) `polygon` (Regular polygon)

```json
{
  "type": "polygon",
  "name": "HexTile",
  "size": [160, 160],
  "position": [520, 260],
  "roundness": 8,
  "color": "#22C55E",
  "width": null,
  "copies": null,
  "offset": null
}
```

#### 5) `path` (Custom path vector marker)

```json
{
  "type": "path",
  "name": "LogoPath",
  "size": [420, 240],
  "position": [700, 420],
  "roundness": null,
  "color": "#A855F7",
  "width": 3,
  "copies": null,
  "offset": null
}
```

#### 6) `fill` (Fill operation)

```json
{
  "type": "fill",
  "name": "PrimaryFill",
  "size": null,
  "position": null,
  "roundness": null,
  "color": "#2563EB",
  "width": null,
  "copies": null,
  "offset": null
}
```

#### 7) `stroke` (Stroke operation)

```json
{
  "type": "stroke",
  "name": "OutlineStroke",
  "size": null,
  "position": null,
  "roundness": null,
  "color": "#E2E8F0",
  "width": 8,
  "copies": null,
  "offset": null
}
```

#### 8) `repeater` (Repeat operation)

```json
{
  "type": "repeater",
  "name": "GridRepeater",
  "size": null,
  "position": null,
  "roundness": null,
  "color": null,
  "width": null,
  "copies": 12,
  "offset": [48, 0]
}
```

#### 9) `group` (Grouping operation)

```json
{
  "type": "group",
  "name": "IconCluster",
  "size": null,
  "position": [0, 0],
  "roundness": null,
  "color": null,
  "width": null,
  "copies": null,
  "offset": null
}
```

### Practical tips for shapes

> **Coordinate system**: Shape positions use **layer space** (relative to shape layer origin). Origin is top-left `(0,0)`. Shape expands rightward (+) and downward (+).

- Keep `size` and `position` explicit for predictable layout.
- Use uppercase hex (`#RRGGBB`) for readability and consistency.
- Prefer one layer for related vectors; split layers when timing/effects differ.
- Put style operators (`fill`, `stroke`) close to related geometry in your shape array.
- Use `repeater` with small offsets first, then increase gradually to avoid accidental off-canvas copies.
- Remember: `position` is relative to the layer's top-left, not absolute on the canvas.

---

## Part 2: Mask System

### MaskMode enum values

`MaskMode` also uses lowercase JSON values.

| Value | Name | Meaning |
|---|---|---|
| `add` | Additive mask (union) | Adds visible area |
| `subtract` | Subtract from mask | Removes area from result |
| `intersect` | Keep intersection only | Keeps overlap of existing and new region |
| `lighten` | Lighten blend | Lighten-style mask compositing |
| `darken` | Darken blend | Darken-style mask compositing |
| `difference` | Difference blend | Difference-style compositing |
| `none` | No mask mode | Defines mask path without applying blend mode effect |

### Mask structure

Each mask object in `layer.masks`:

```json
{
  "name": "FaceCutout",
  "mode": "add",
  "path": [
    { "x": 320, "y": 240, "handleIn": null, "handleOut": [30, 0] },
    { "x": 640, "y": 240, "handleIn": [-30, 0], "handleOut": null },
    { "x": 640, "y": 480, "handleIn": null, "handleOut": [0, 30] },
    { "x": 320, "y": 480, "handleIn": [0, -30], "handleOut": null }
  ],
  "feather": 12,
  "opacity": 100
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | Mask identifier |
| `mode` | `MaskMode` | Yes | Compositing behavior |
| `path` | `MaskPoint[]` | Yes | Ordered points describing closed mask contour |
| `feather` | `number` | Yes | Soft-edge amount |
| `opacity` | `number` | Yes | Mask strength (typically 0-100) |

### MaskPoint structure

> **Coordinate Reference**: Mask coordinates use **composition space** (absolute positions on canvas), NOT layer space. Top-left origin `(0,0)`. See [Coordinate System](coordinate-system.md) for full details.

Each point in `mask.path`:

| Field | Type | Required | Description |
|---|---|---|---|
| `x` | `number` | Yes | X position from composition left edge |
| `y` | `number` | Yes | Y position from composition top edge |
| `handleIn` | `[number, number] \| null` | No | Incoming bezier tangent offset |
| `handleOut` | `[number, number] \| null` | No | Outgoing bezier tangent offset |

Mask point example:

```json
{
  "x": 900,
  "y": 300,
  "handleIn": [-40, 20],
  "handleOut": [40, -20]
}
```

### Mask Coordinate Space

Masks use **composition space**, meaning coordinates are absolute positions on the canvas, not relative to the layer position. This allows masks to be defined independently of layer transforms.

```
┌─────────────────────────────────────────────────┐
│  Composition Space (1920×1080)                   │
│                                                 │
│  (0,0)                                          │
│    │                                            │
│    │  ┌─────────────────────────────────────┐  │
│    │  │  Layer                              │  │
│    │  │                                     │  │
│    │  │         Mask path:                  │  │
│    │  │         (x:400, y:200)              │  │
│    │  │              ●───────────────────   │  │
│    │  │             /│                      │  │
│    │  │            / │                      │  │
│    │  │           ●  │                      │  │
│    │  │              ●──────────────────    │  │
│    │  │                                     │  │
│    │  └─────────────────────────────────────┘  │
│    │                                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

> **Important**: Mask coordinates are absolute in composition space, NOT relative to layer position.

### Usage notes

- Masks are stored in `layer.masks`.
- Use `handleIn` / `handleOut` for curved edges.
- `feather` creates soft transitions at the edge.
- Multiple masks are applied in array order (top to bottom in JSON).

### JSON examples for each mask mode

Use these directly inside a layer `masks` array.

#### 1) `add`

```json
{
  "name": "Add_MainRegion",
  "mode": "add",
  "path": [
    { "x": 100, "y": 100, "handleIn": null, "handleOut": null },
    { "x": 900, "y": 100, "handleIn": null, "handleOut": null },
    { "x": 900, "y": 500, "handleIn": null, "handleOut": null },
    { "x": 100, "y": 500, "handleIn": null, "handleOut": null }
  ],
  "feather": 0,
  "opacity": 100
}
```

#### 2) `subtract`

```json
{
  "name": "Subtract_Hole",
  "mode": "subtract",
  "path": [
    { "x": 340, "y": 220, "handleIn": null, "handleOut": [50, 0] },
    { "x": 660, "y": 220, "handleIn": [-50, 0], "handleOut": null },
    { "x": 660, "y": 380, "handleIn": null, "handleOut": [0, 50] },
    { "x": 340, "y": 380, "handleIn": [0, -50], "handleOut": null }
  ],
  "feather": 6,
  "opacity": 100
}
```

#### 3) `intersect`

```json
{
  "name": "Intersect_Band",
  "mode": "intersect",
  "path": [
    { "x": 200, "y": 260, "handleIn": null, "handleOut": null },
    { "x": 820, "y": 260, "handleIn": null, "handleOut": null },
    { "x": 820, "y": 420, "handleIn": null, "handleOut": null },
    { "x": 200, "y": 420, "handleIn": null, "handleOut": null }
  ],
  "feather": 2,
  "opacity": 100
}
```

#### 4) `lighten`

```json
{
  "name": "Lighten_GlowRegion",
  "mode": "lighten",
  "path": [
    { "x": 300, "y": 120, "handleIn": null, "handleOut": [40, 20] },
    { "x": 780, "y": 180, "handleIn": [-30, 10], "handleOut": [20, 40] },
    { "x": 760, "y": 460, "handleIn": [-20, -30], "handleOut": [-40, 0] },
    { "x": 260, "y": 420, "handleIn": [30, -20], "handleOut": null }
  ],
  "feather": 18,
  "opacity": 75
}
```

#### 5) `darken`

```json
{
  "name": "Darken_ShadeRegion",
  "mode": "darken",
  "path": [
    { "x": 120, "y": 80, "handleIn": null, "handleOut": null },
    { "x": 940, "y": 80, "handleIn": null, "handleOut": null },
    { "x": 940, "y": 540, "handleIn": null, "handleOut": null },
    { "x": 120, "y": 540, "handleIn": null, "handleOut": null }
  ],
  "feather": 10,
  "opacity": 55
}
```

#### 6) `difference`

```json
{
  "name": "Difference_Cut",
  "mode": "difference",
  "path": [
    { "x": 240, "y": 160, "handleIn": null, "handleOut": [30, 10] },
    { "x": 860, "y": 220, "handleIn": [-20, 0], "handleOut": [0, 30] },
    { "x": 700, "y": 520, "handleIn": [10, -20], "handleOut": [-30, 0] },
    { "x": 200, "y": 440, "handleIn": [20, -10], "handleOut": null }
  ],
  "feather": 4,
  "opacity": 100
}
```

#### 7) `none`

```json
{
  "name": "None_Placeholder",
  "mode": "none",
  "path": [
    { "x": 140, "y": 140, "handleIn": null, "handleOut": null },
    { "x": 880, "y": 140, "handleIn": null, "handleOut": null },
    { "x": 880, "y": 500, "handleIn": null, "handleOut": null },
    { "x": 140, "y": 500, "handleIn": null, "handleOut": null }
  ],
  "feather": 0,
  "opacity": 100
}
```

### Mask mode combination example (stacked order)

This example applies multiple modes in sequence on one layer:

```json
{
  "masks": [
    {
      "name": "BaseAdd",
      "mode": "add",
      "path": [
        { "x": 80, "y": 80, "handleIn": null, "handleOut": null },
        { "x": 980, "y": 80, "handleIn": null, "handleOut": null },
        { "x": 980, "y": 560, "handleIn": null, "handleOut": null },
        { "x": 80, "y": 560, "handleIn": null, "handleOut": null }
      ],
      "feather": 0,
      "opacity": 100
    },
    {
      "name": "HoleSubtract",
      "mode": "subtract",
      "path": [
        { "x": 400, "y": 240, "handleIn": null, "handleOut": [40, 0] },
        { "x": 660, "y": 240, "handleIn": [-40, 0], "handleOut": null },
        { "x": 660, "y": 380, "handleIn": null, "handleOut": [0, 40] },
        { "x": 400, "y": 380, "handleIn": [0, -40], "handleOut": null }
      ],
      "feather": 8,
      "opacity": 100
    },
    {
      "name": "BandIntersect",
      "mode": "intersect",
      "path": [
        { "x": 140, "y": 260, "handleIn": null, "handleOut": null },
        { "x": 920, "y": 260, "handleIn": null, "handleOut": null },
        { "x": 920, "y": 430, "handleIn": null, "handleOut": null },
        { "x": 140, "y": 430, "handleIn": null, "handleOut": null }
      ],
      "feather": 3,
      "opacity": 100
    }
  ]
}
```

### Cautions and performance notes

- Complex masks (many points, many bezier handles, many stacked masks) are computationally expensive.
- Feather can produce edge softness that looks like aliasing at low resolutions.
- Mask paths should be topologically closed for reliable results.
- Mask order matters; later masks operate on the result of earlier masks.
- Prefer fewer points with smooth bezier handles over dense straight-point meshes for better performance.

### Troubleshooting checklist

- Mask not visible: confirm `opacity > 0` and valid `mode`.
- Jagged edge: increase render resolution or reduce feather extremes.
- Unexpected cutout: inspect mask order and swap problematic entries.
- Curves look broken: verify `handleIn` and `handleOut` are 2-number arrays.

---

## Full practical layer example (shapes + masks + effects)

```json
{
  "id": "layer_shape_mask_demo",
  "type": "shape",
  "name": "ShapesAndMasksDemo",
  "enabled": true,
  "startTime": 0,
  "duration": 12,
  "inPoint": 0,
  "outPoint": 12,
  "parentId": null,
  "trackMatte": null,
  "blendMode": "normal",
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [0, 0], "keyframes": null },
    "position": { "value": [0, 0], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": null,
  "shapeContents": [
    {
      "type": "rect",
      "name": "Panel",
      "size": [720, 420],
      "position": [100, 90],
      "roundness": 24,
      "color": "#0F172A",
      "width": null,
      "copies": null,
      "offset": null
    },
    {
      "type": "ellipse",
      "name": "Badge",
      "size": [180, 180],
      "position": [620, 60],
      "roundness": null,
      "color": "#22D3EE",
      "width": null,
      "copies": null,
      "offset": null
    },
    {
      "type": "stroke",
      "name": "PanelStroke",
      "size": [720, 420],
      "position": [100, 90],
      "roundness": 24,
      "color": "#67E8F9",
      "width": 5,
      "copies": null,
      "offset": null
    }
  ],
  "effects": [
    {
      "id": "fx_glow_01",
      "type": "glow",
      "enabled": true,
      "params": {
        "radius": 16,
        "color": "#22D3EE",
        "opacity": 40
      },
      "keyframes": null
    }
  ],
  "masks": [
    {
      "name": "MainAdd",
      "mode": "add",
      "path": [
        { "x": 120, "y": 110, "handleIn": null, "handleOut": null },
        { "x": 780, "y": 110, "handleIn": null, "handleOut": null },
        { "x": 780, "y": 470, "handleIn": null, "handleOut": null },
        { "x": 120, "y": 470, "handleIn": null, "handleOut": null }
      ],
      "feather": 6,
      "opacity": 100
    },
    {
      "name": "InnerSubtract",
      "mode": "subtract",
      "path": [
        { "x": 300, "y": 220, "handleIn": null, "handleOut": [40, 0] },
        { "x": 580, "y": 220, "handleIn": [-40, 0], "handleOut": null },
        { "x": 580, "y": 360, "handleIn": null, "handleOut": [0, 40] },
        { "x": 300, "y": 360, "handleIn": [0, -40], "handleOut": null }
      ],
      "feather": 10,
      "opacity": 95
    }
  ]
}
```