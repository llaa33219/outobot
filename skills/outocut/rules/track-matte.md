# Track Matte System

Comprehensive guide for OutOcut track matte behavior in `.outocut` files.

- **Author**: BLOUplanet
- **License**: Apache 2.0

## Overview

Track matte lets one layer control the visibility of another layer.

In OutOcut, when a layer has `trackMatte` set, that layer uses the layer immediately above it as a matte source:

- The bottom layer is the **matted layer** (the one you want to reveal/hide).
- The layer directly above it is the **matte layer** (the control layer).
- The matte layer's alpha or luma drives visibility.
- The matte layer itself is not meant to render as a normal visible layer in the final result.

If there is no layer directly above, or the wrong layer is above, matte behavior will not match intent.

---

## Mental Model

Think of track matte as a stencil operation:

1. Render matte layer to a temporary mask buffer.
2. Convert that buffer to alpha-based coverage using selected mode (`alpha`, `alphaInverted`, `luma`, `lumaInverted`).
3. Apply coverage to the layer below.
4. Composite the matted result into the timeline.

In shorthand:

```text
final_pixel = bottom_layer_pixel * matte_coverage
```

Where `matte_coverage` is computed from either matte alpha or matte brightness.

---

## Layer Ordering Diagram

Order is the single most important rule.

```text
Timeline stack (top to bottom):

[2] Matte Layer        <- acts as stencil source
[1] Layer with matte   <- has "trackMatte": "alpha" (or other mode)
[0] Other layers       <- normal background/content
```

Relationship diagram:

```text
Matte Layer (N)
   |
   | provides alpha/luma coverage
   v
Matted Layer (N+1, directly below, has trackMatte)
   |
   v
Composited result
```

If any unrelated layer is inserted between these two, the matte target changes (or breaks).

---

## `TrackMatte` Enum Values

OutOcut supports four modes:

| JSON Value | Reads From Matte | Effect |
|---|---|---|
| `alpha` | Matte alpha channel | Show matted layer where matte is opaque; hide where transparent |
| `alphaInverted` | Inverse matte alpha | Hide where matte is opaque; show where transparent |
| `luma` | Matte brightness (lightness) | Bright areas reveal more; dark areas hide |
| `lumaInverted` | Inverse matte brightness | Dark areas reveal more; bright areas hide |

### 1) `alpha`

Best when matte has clean transparency or anti-aliased edges (PNG, vector text, shape alpha).

```text
matte alpha 1.0 -> fully visible
matte alpha 0.0 -> fully hidden
```

### 2) `alphaInverted`

Best for cutout effects where the matte shape creates a hole in the matted layer.

```text
matte alpha 1.0 -> fully hidden
matte alpha 0.0 -> fully visible
```

### 3) `luma`

Best when matte is grayscale artwork or gradients. White reveals, black hides, gray partially reveals.

```text
matte luma 1.0 (white) -> fully visible
matte luma 0.0 (black) -> fully hidden
```

### 4) `lumaInverted`

Reverse of `luma`; useful for negative-style reveals.

```text
matte luma 1.0 (white) -> fully hidden
matte luma 0.0 (black) -> fully visible
```

---

## How It Works in Practice

Core behavior rules:

- The layer with `trackMatte` set uses the layer immediately above as matte input.
- The matte layer contributes control data (alpha/luma), not normal visible pixels.
- Only matte coverage information affects the matted layer output.
- Matte layer opacity affects matte strength; low opacity produces weaker matte influence.

Simple pseudo-flow:

```text
if layer.trackMatte is null:
  render layer normally
else:
  matte = layer_above
  coverage = compute_coverage(matte, mode)
  output = layer * coverage
```

---

## Setup (Step-by-Step)

1. Create the matte layer (shape, text, image, or video can be used).
2. Place matte directly above the layer you want to mask.
3. Set `trackMatte` on the bottom (matted) layer.
4. Render and verify that matte layer itself is not appearing as a normal visible layer.

Practical checklist before rendering:

- Matte and matted layers overlap spatially.
- Matte active time intersects matted layer active time.
- Matte has usable alpha (for alpha modes) or high-contrast brightness (for luma modes).
- No extra layers inserted between matte and matted layers.

---

## Canonical JSON Example

```json
{
  "layers": [
    {
      "id": "matte-shape",
      "type": "shape",
      "name": "Track Matte",
      "enabled": true,
      "shapeContents": [
        {
          "type": "rect",
          "name": "Reveal Window",
          "size": [640, 360],
          "position": [320, 180],
          "roundness": 32,
          "color": "#FFFFFF"
        }
      ]
      // No trackMatte field - this is the matte
    },
    {
      "id": "video-layer",
      "type": "video",
      "name": "My Video",
      "enabled": true,
      "trackMatte": "alpha",
      // Video only shows through matte's shape
      "content": { "assetId": "video-1" }
    }
  ]
}
```

---

## Additional JSON Examples by Mode

### Alpha Inverted Cutout

```json
{
  "layers": [
    {
      "id": "text-matte",
      "type": "text",
      "name": "Cutout Text",
      "enabled": true,
      "content": {
        "text": "OUTOCUT",
        "fontSize": 220,
        "color": "#FFFFFF"
      }
    },
    {
      "id": "solid-fill",
      "type": "solid",
      "name": "Background Fill",
      "enabled": true,
      "trackMatte": "alphaInverted",
      "content": { "color": "#0A84FF" }
    }
  ]
}
```

### Luma Gradient Reveal

```json
{
  "layers": [
    {
      "id": "gradient-matte",
      "type": "image",
      "name": "BW Gradient",
      "enabled": true,
      "content": { "assetId": "img-gradient-bw" }
    },
    {
      "id": "footage",
      "type": "video",
      "name": "Interview",
      "enabled": true,
      "trackMatte": "luma",
      "content": { "assetId": "vid-interview" }
    }
  ]
}
```

### Luma Inverted Dark-Reveal

```json
{
  "layers": [
    {
      "id": "noisy-matte",
      "type": "image",
      "name": "Noise Matte",
      "enabled": true,
      "content": { "assetId": "img-noise" }
    },
    {
      "id": "logo-video",
      "type": "video",
      "name": "Logo Fill",
      "enabled": true,
      "trackMatte": "lumaInverted",
      "content": { "assetId": "vid-motion-bg" }
    }
  ]
}
```

---

## Use Cases

- Text reveals (including typewriter-like window reveals).
- Shape-based wipes and geometric transitions.
- Simulated light rays through windows/blinds.
- Video constrained inside logo silhouettes.
- Custom shaped reveals that are hard to achieve with simple rectangular masks.

---

## Cautions and Rules

- **Layer ordering is critical**: matte must be directly above the matted layer.
- Matte layer is not intended to render visible output as a normal layer.
- If you do not want the matte affecting output, disable or remove the matte relationship (`enabled: false` or `trackMatte: null` as appropriate).
- `luma`/`lumaInverted` work best with high-contrast black-and-white sources.
- `alpha`/`alphaInverted` work best with clean transparency and smooth alpha gradients.
- Track matte is computationally expensive in complex stacks.

---

## Performance Guidance

Track matte adds significant render overhead because it requires extra compositing passes.

Recommendations:

- Avoid many simultaneous matte pairs in the same frame.
- Prefer simpler matte geometry where possible.
- Pre-render heavy matte animation into a single asset for reuse.
- Limit high-resolution luma mattes with noisy detail when real-time preview speed matters.
- Profile final scenes early to avoid late render-time surprises.

Rule of thumb:

```text
More matte pairs + higher resolution + animated matte content = slower renders
```

---

## Common Mistakes

1. Reversed layer order (matted layer above matte layer).
2. Matte not directly adjacent to the matted layer.
3. Incorrect matte opacity causing unexpected weak/strong results.
4. Low-contrast matte source used for `luma` mode.
5. Expecting `trackMatte` itself to be keyframed; matte behavior should be animated via layer properties/content instead.

---

## Troubleshooting Checklist

If output looks wrong, check in this order:

1. **Adjacency**: Is matte immediately above the matted layer?
2. **Mode**: Is `alpha` vs `luma` mode matched to source content type?
3. **Contrast/Alpha**: Does matte image actually contain strong alpha or luma variation?
4. **Timing**: Are both layers active at the same time?
5. **Opacity**: Is matte opacity near intended value?
6. **Enabled state**: Are both layers enabled?

---

## Practical Design Patterns

### Pattern A: Logo Fill Reveal

```text
Top:    White logo image/text (matte)
Bottom: Video texture layer (trackMatte: alpha)
Result: Video appears only inside logo
```

### Pattern B: Soft Luma Fog Reveal

```text
Top:    Animated grayscale fog/noise matte
Bottom: Solid or footage layer (trackMatte: luma)
Result: Organic appearance/disappearance based on brightness
```

### Pattern C: Inverted Spotlight

```text
Top:    Circular white matte shape
Bottom: Dark overlay layer (trackMatte: alphaInverted)
Result: Circular "hole" revealing scene underneath
```

---

## Summary

Use track matte when you need one layer to drive the visibility of another using alpha or brightness. Keep matte ordering strict, choose mode based on source data quality (alpha vs luma), and budget extra render time for matte-heavy scenes.