# Transform System

Comprehensive reference for OutOcut layer transforms.

- **Author**: BLOUplanet
- **License**: Apache 2.0
- **Requires**: OutOcut v1.0+

## Coordinate System

OutOcut uses a standard 2D graphics coordinate system:

| Property | Value |
|----------|-------|
| **Origin** | `(0, 0)` — top-left corner |
| **X-axis** | Positive → right |
| **Y-axis** | Positive ↓ down |
| **Angle** | Positive ↻ clockwise |

For full details, see [coordinate-system.md](coordinate-system.md).

## Overview

Every layer has a `transform` object. Each transform field is an `AnimatedProperty`, so every value can be static or keyframed over time.

Transform fields:

1. `anchor` - `Vec<f64>` (`[x, y]`) - point around which transform occurs
2. `position` - `Vec<f64>` (`[x, y]`) - layer position in composition space
3. `scale` - `Vec<f64>` (`[x%, y%]`) - scale factors (`100` means 100%, negative values flip)
4. `rotation` - `f64` - rotation in degrees (`360` = full turn)
5. `skew` - `Vec<f64>` (`[x, y]`) - skew angles
6. `skewAxis` - `f64` - skew axis angle in degrees

## Default Values

When a transform is omitted or created with defaults:

- `anchor`: `[0, 0]`
- `position`: `[0, 0]`
- `scale`: `[100, 100]`
- `rotation`: `0`
- `skew`: `[0, 0]`
- `skewAxis`: `0`

Default JSON:

```json
"transform": {
  "anchor": { "value": [0, 0], "keyframes": null },
  "position": { "value": [0, 0], "keyframes": null },
  "scale": { "value": [100, 100], "keyframes": null },
  "rotation": { "value": 0, "keyframes": null },
  "skew": { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```

## Transform Structure and AnimatedProperty

All transform fields follow the same `AnimatedProperty<T>` shape:

```json
{
  "value": [960, 540],
  "keyframes": [
    { "time": 0.0, "value": [0, 540], "easing": "easeOutCubic" },
    { "time": 1.2, "value": [960, 540] }
  ]
}
```

## How Transforms Are Applied (Order Matters)

OutOcut transform evaluation is order-sensitive. The conceptual transform stack is:

1. `anchor`
2. `position`
3. `scale`
4. `rotation`
5. `skew`

## Anchor (Transform Origin) Behavior

`anchor` is the transform origin in layer-local coordinates. It determines which point in the layer space is used as the pivot for scale, rotation, and skew operations.

**Coordinate space**: Layer space (relative to layer content, NOT composition)

| Anchor Value | Transform Origin |
|--------------|-----------------|
| `[0, 0]` | Top-left corner of layer |
| `[width/2, height/2]` | Center of layer |
| `[width, 0]` | Top-right corner |
| `[0, height]` | Bottom-left corner |
| `[width, height]` | Bottom-right corner |

## Negative Scale and Flipping

`scale` uses percent values:

- `[100, 100]` = original size
- `[50, 50]` = half size
- `[200, 100]` = double width only
- `[-100, 100]` = horizontal flip
- `[100, -100]` = vertical flip
- `[-100, -100]` = horizontal + vertical flip (equivalent to 180-degree mirror around anchor)

## Transform Inheritance with Parent Layers

You can build transform hierarchies with `parentId`.

- parent transform is evaluated first
- child local transform is applied relative to parent space
- final child transform is the composed parent + child result

## Practical Examples

### 1) Center a layer

For a 1920×1080 composition, center position is `[960, 540]`.

```json
"transform": {
  "anchor": { "value": [200, 100], "keyframes": null },
  "position": { "value": [960, 540], "keyframes": null },
  "scale": { "value": [100, 100], "keyframes": null },
  "rotation": { "value": 0, "keyframes": null },
  "skew": { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```

### 2) Scale from center

Set anchor to layer center, then animate scale.

```json
"transform": {
  "anchor": { "value": [200, 100], "keyframes": null },
  "position": { "value": [960, 540], "keyframes": null },
  "scale": {
    "value": [100, 100],
    "keyframes": [
      { "time": 0.0, "value": [0, 0], "easing": "easeOutBack" },
      { "time": 0.6, "value": [100, 100] }
    ]
  },
  "rotation": { "value": 0, "keyframes": null },
  "skew": { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```

### 3) Rotate around custom anchor

Move anchor to left edge to create a hinge effect.

```json
"transform": {
  "anchor": { "value": [0, 100], "keyframes": null },
  "position": { "value": [960, 540], "keyframes": null },
  "scale": { "value": [100, 100], "keyframes": null },
  "rotation": {
    "value": 0,
    "keyframes": [
      { "time": 0.0, "value": -45, "easing": "easeOutCubic" },
      { "time": 1.0, "value": 0 }
    ]
  },
  "skew": { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```

## Cautions and Best Practices

- Transform order is critical: `anchor -> position -> scale -> rotation -> skew`.
- Negative scale is powerful for flips but may produce unexpected behavior with some effects.
- Skew without a meaningful `skewAxis` often gives unintuitive results.
- Very large scale values can introduce visible pixelation, especially raster media.
- Keep anchor values intentional; many "wrong pivot" bugs are anchor issues, not rotation bugs.
- Prefer parent controllers (`null` layers) when animating groups to keep timelines clean.
- **Coordinate system**: OutOcut uses top-left origin `(0,0)`. X increases right, Y increases down. Always consider this when positioning layers.

## Quick Copy Template

```json
"transform": {
  "anchor": { "value": [0, 0], "keyframes": null },
  "position": { "value": [960, 540], "keyframes": null },
  "scale": { "value": [100, 100], "keyframes": null },
  "rotation": { "value": 0, "keyframes": null },
  "skew": { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```
