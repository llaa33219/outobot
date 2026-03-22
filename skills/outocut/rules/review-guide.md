# OutOcut Production Review Guide

Comprehensive review and validation guide for `.outocut` projects before rendering or delivery.

- **Author**: BLOUplanet
- **License**: Apache 2.0
- **Purpose**: Prevent layout breaks, incorrect positioning, wrong effect intensities, and unintended output by documenting what to check and how to fix it.

---

## Why This Guide Exists

OutOcut projects are authored in JSON. Unlike visual editors where errors are immediately obvious, JSON authoring hides mistakes until render time — or worse, produces output that looks "close enough" to pass until delivery.

**Common failure patterns without review:**

| Problem | Symptom | Cause |
|---------|---------|-------|
| Layout broken | Layer appears at wrong position or outside canvas | `position` values wrong for coordinate space |
| Layer invisible | Nothing renders at expected time | `enabled: false`, wrong `inPoint`/`outPoint`, hidden by opaque layer above |
| Effect wrong | Glow/shadow/blur intensity unexpected | Wrong `params` range, effect order swapped |
| Shape wrong | Rectangle not where expected | `shapeContents[].position` confused with composition-space coords |
| Mask wrong | Cutout in wrong place or not working | Mask coords in wrong coordinate space |
| Animation broken | Jump, stutter, or hold instead of motion | Duplicate keyframe times, wrong easing, vector length mismatch |
| Track matte fails | Matte has no effect or wrong effect | Layer order wrong, matte not adjacent |
| Blend mode wrong | Colors look wrong | Mode chosen without understanding base/blend relationship |
| Scale flip causes issues | Shadow/effect behaves unexpectedly | Negative `scale` values interacting with effects |

This guide gives you a systematic process to catch and fix all of these before they reach render.

---

## Review Process Overview

Review in three stages, in order. Each stage catches different classes of errors.

### Stage 1: Structure & Schema Review (Fast — Automated + Manual)

Catches: missing fields, wrong types, broken references, enum typos.

- Run `outocut validate project.outocut`
- Check all IDs are unique (no duplicate `id` in same composition)
- Verify `mainCompositionId` matches an actual composition key
- Confirm `settings.duration` equals main composition `duration`
- Confirm every `assetId` resolves to an entry in `assets[]`
- Confirm every `compositionId` resolves to a key in `compositions`
- Confirm every `parentId` points to an existing layer ID
- Verify all enum strings are exact (case-sensitive)

### Stage 2: Logical & Visual Review (Medium — Targeted Preview)

Catches: wrong values, broken positioning, missing animation, incorrect effect parameters.

- Preview key moments with `outocut preview --time <sec>`
- Check each layer's position in composition space (not layer space)
- Verify layer ordering reflects intended z-index
- Confirm every layer is active at its intended time range
- Check effect `params` are within expected ranges
- Verify effect stacking order produces intended visual result
- Confirm blend modes interact correctly with layers beneath
- Verify track matte adjacency and mode match intent

### Stage 3: Pre-Render Checklist (Quick — Systematic Pass)

Catches: resolution mismatches, quality setting errors, missing previews.

- Render a review pass (`--preset veryfast --crf 30`) and watch it
- Verify on target resolution (1080p/4K/social)
- Check on at least one other display for color consistency
- Verify text readability and color contrast
- Confirm animation timing at actual fps
- Validate audio sync if project has audio

---

## System-by-System Review Checklist

### 1. Transform Review

Transform errors are the most common cause of broken layouts.

#### Position (`position`)

**Rule**: `position` places the layer's **anchor point** in **composition space** (top-left origin `(0,0)`).

**Review checklist:**
- [ ] `position[0]` and `position[1]` are within canvas bounds
- [ ] `position: [0, 0]` places layer at **top-left**, not center
- [ ] For center placement, use `[width/2, height/2]` (e.g., `[960, 540]` for 1920×1080)
- [ ] Check: does this position make sense for the element's role? (title centered? logo in corner?)

**Common mistakes:**
- Setting `position: [0, 0]` expecting center — results in top-left placement
- Mixing up layer-space `position` (inside `shapeContents`) with composition-space `position` (layer transform)

#### Anchor (`anchor`)

**Rule**: `anchor` is in **layer-local coordinates**, defining the pivot point for scale/rotation/skew.

**Review checklist:**
- [ ] Anchor value matches intended pivot
- [ ] `[0, 0]` = top-left of layer content, `[width/2, height/2]` = center
- [ ] For shapes/text: anchor is relative to shape content size, not composition size
- [ ] After changing anchor, verify position still makes sense — anchor moves the pivot, not the layer

**Common mistakes:**
- Setting `anchor: [960, 540]` for a 400×200 layer expecting center — should be `[200, 100]`
- Animating scale/rotation without verifying anchor produces the intended pivot behavior

#### Scale (`scale`)

**Rule**: Values are percentages. `[100, 100]` = original size. Negative values flip.

**Review checklist:**
- [ ] No unintended horizontal or vertical flip (`[-100, 100]` or `[100, -100]`)
- [ ] Scale values are reasonable — very large values cause pixelation
- [ ] After negative scale: re-test blur, shadow, and directional effects
- [ ] When using negative scale, verify result is intentional

**Common mistakes:**
- Negative `scale` values unintentionally flip the layer, causing text/masks to appear reversed
- `[-100, -100]` produces 180° mirror around anchor — this may not be the intended flip

#### Rotation (`rotation`)

**Rule**: Degrees, clockwise positive. Pivot is at `anchor` point.

**Review checklist:**
- [ ] Rotation value is in expected range
- [ ] For 360° spin animations, verify rotation goes from `0` to `360`, not `0` to `-360` (unless intentional)
- [ ] Verify pivot (`anchor`) is where the rotation should revolve around

#### Skew (`skew`) and `skewAxis`

**Rule**: Applied last in transform stack. Shears geometry along `skewAxis`.

**Review checklist:**
- [ ] `skewAxis` has a meaningful value when skew is used
- [ ] Skew result matches creative intent — skew without clear axis is usually wrong

#### Transform Order (`anchor → position → scale → rotation → skew`)

**Review checklist:**
- [ ] Understand that changing `anchor` affects where `position` lands
- [ ] Scaling before rotating ≠ rotating before scaling
- [ ] Skew always applies last regardless of where it appears in JSON

#### Parent Relationships (`parentId`)

**Review checklist:**
- [ ] Parent layer is active at all times child is active
- [ ] Child transforms are relative to parent space (child `position: [0, 0]` = parent's anchor position)
- [ ] No circular parent chains (A → B → C → A)
- [ ] Changing parent position/scale/rotation affects children as intended

**Debugging tip:** Preview at the moment you expect to see a parent-child animation working. If child doesn't move with parent, check that parent `startTime`/`duration` overlaps child.

---

### 2. Effect Review

Effects have specific ordering, parameter, and stacking requirements that are easy to get wrong.

#### Effect Stack Order

**Rule**: Effects are applied top-to-bottom in `effects[]` array. Order changes output.

**Review checklist:**
- [ ] Effect order matches the recommended stacking pattern:
  1. Utility/geometry: `crop`, `flip`, `mirror`, `rotate`
  2. Cleanup: `chromaKey`
  3. Color/tonal: `colorCorrection`, `levels`, `curves`, `hueSaturation`
  4. Styling: `stroke`, `fillGradient`, `trimPath`
  5. Blur/light: `gaussianBlur`, `directionalBlur`, `radialBlur`, `glow`
  6. Mood: `vignette`, `noise`
- [ ] Do not reorder blur and glow — this drastically changes edge quality
- [ ] Place `chromaKey` early; blurring before keying worsens matte quality
- [ ] Avoid stacking multiple heavy blurs on the same layer

#### Effect Parameter Ranges

**Review checklist per effect:**

| Effect | Critical Params to Verify |
|--------|--------------------------|
| `dropShadow` | `distance > 0`, `angle` 0-360, `blur >= 0`, `opacity 0-100` |
| `innerShadow` | `distance >= 0`, `angle` 0-360, `choke` 0-100 |
| `glow` / `outerGlow` | `radius >= 0`, `opacity 0-100`, `threshold 0-100` |
| `gaussianBlur` | `radius >= 0`, `iterations >= 1` |
| `directionalBlur` | `distance >= 0`, `angle` 0-360, `samples >= 3` |
| `radialBlur` | `amount 0-100`, `center [x, y]`, `mode` is `spin` or `zoom` |
| `colorCorrection` | `saturation` 0-200, `gamma > 0` |
| `brightnessContrast` | `brightness` -100 to 100, `contrast` -100 to 100 |
| `hueSaturation` | `hue` -180 to 180, `saturation` 0-200, `lightness` -100 to 100 |
| `chromaKey` | `similarity` and `smoothness` 0-100, `spillSuppression` 0-100 |
| `vignette` | `amount` -100 to 100, `roundness` -100 to 100 |
| `stroke` | `width >= 0`, `position` is `inside`/`center`/`outside` |
| `trimPath` | `start`/`end` 0-100, `offset` any degree |
| `wiggle` | `frequency >= 0`, `amplitude >= 0` |

#### Effect Keyframes

**Review checklist:**
- [ ] Keyframes are under `keyframes.<paramName>`, not directly on `params`
- [ ] Animated params use scalar values (not complex objects/arrays) for safest interpolation
- [ ] At 30fps, `1/30 = 0.0333...` — avoid over-reliance on exact equality
- [ ] Verify keyframe values are in the valid range for that parameter

**Common mistakes:**
- Setting `params.radius: 18` and expecting keyframes to work if they're not under `keyframes.radius`
- Putting complex object params under keyframes — scalar params are safest
- Animating `amount` on `radialBlur` expecting `center` to move — these are independent params

#### Effect Performance

**Review checklist:**
- [ ] High-cost effects (`gaussianBlur`, `chromaKey`, `directionalBlur`, `radialBlur`) are not stacked unnecessarily
- [ ] At 4K resolution, heavy effect stacks are verified with a preview before full render
- [ ] Consider pre-rendering expensive static effect stacks

---

### 3. Shape and Mask Review

Shape and mask review has one critical distinction that causes most errors.

#### Shape Position vs Composition Position

**Rule**: `shapeContents[].position` uses **layer space** (relative to shape layer origin, top-left `(0,0)`). Layer transform `position` uses **composition space** (absolute canvas position).

**Review checklist:**
- [ ] Shape positions are relative to shape layer origin, not composition
- [ ] `size` and `position` together produce the expected shape placement within the layer
- [ ] For a shape at composition `[300, 200]` with layer origin at `[0, 0]`: shape position `[300, 200]` is correct
- [ ] For nested shapes: each shape's `position` is relative to its parent shape group's origin, not the composition

#### Shape Stack Order

**Review checklist:**
- [ ] Shape items in `shapeContents[]` are in the intended draw order
- [ ] `fill` and `stroke` operators are placed near their related geometry
- [ ] `repeater` results are within canvas bounds — start with low `copies`, increase gradually

#### Mask Coordinate Space

**Rule**: Masks use **composition space** (absolute positions on canvas), NOT layer space. This is different from shapes.

**Review checklist:**
- [ ] Mask path coordinates are absolute on the canvas, not relative to layer
- [ ] Mask covers the intended region — verify with `outocut preview --time <sec>`
- [ ] Mask paths are topologically closed (first point connects to last point)
- [ ] `feather` values produce intended edge softness
- [ ] Mask mode (`add`, `subtract`, `intersect`, etc.) produces intended result

**Common mistakes:**
- Using shape-layer-space coordinates for mask paths — masks are in composition space
- Forgetting that mask feather at high values can make edges look aliased at low resolution
- Stacking many masks and expecting predictable results — test early

#### Mask Ordering

**Review checklist:**
- [ ] Masks apply in array order (top to bottom in JSON)
- [ ] Later masks operate on the result of earlier masks
- [ ] No extra masks added between matte-related layers

---

### 4. Layer Type Review

#### Layer Active Time

**Rule**: Layer is visible when: `time >= startTime` AND `time < startTime + duration` AND `time >= startTime + (inPoint or 0)` AND `time < startTime + (outPoint or duration)`.

**Review checklist:**
- [ ] `startTime` and `duration` produce intended active window
- [ ] `inPoint`/`outPoint` trim within the block correctly
- [ ] No gap between when one layer ends and another begins (if continuity expected)
- [ ] Disabled layers (`enabled: false`) are intentional

#### Layer Ordering (Z-Index)

**Rule**: Layers are processed in array order — earlier = back (renders first), later = front (renders on top).

**Review checklist:**
- [ ] Layer order reflects intended visual stacking
- [ ] Base backgrounds are near the start of `layers[]`
- [ ] Foreground elements (titles, overlays) are near the end
- [ ] After reordering, verify no unintended occlusion

#### Text Layers

**Review checklist:**
- [ ] `fontSize` is appropriate for canvas resolution
- [ ] `color` contrast is readable against background
- [ ] `alignment` enum is exact: `left`, `center`, `right`, `justify`
- [ ] `tracking` and `leading` values don't cause text to overflow or collapse
- [ ] `fontId` references an existing font asset if used

#### Media Layers (video, audio, image)

**Review checklist:**
- [ ] `assetId` matches a declared asset in `assets[]`
- [ ] Asset type matches layer type (`video` asset for `video` layer, etc.)
- [ ] `inPoint`/`outPoint` don't trim content beyond available media

#### Composition Layers (Precomps)

**Review checklist:**
- [ ] `compositionId` references an existing composition key
- [ ] No circular references (A → B → A)
- [ ] Nested composition `duration` and `startTime` are intentional
- [ ] Verify precomp renders correctly standalone before using in main timeline

---

### 5. Animation Review

#### Keyframe Timing

**Review checklist:**
- [ ] Keyframe times are in ascending order
- [ ] Keyframe times are aligned to frame rate when exact timing matters
  - At 30fps: use `0.0`, `0.0333`, `0.0667`, etc. (multiples of `1/30`)
  - At 24fps: use `0.0`, `0.0417`, `0.0833`, etc. (multiples of `1/24`)
- [ ] No duplicate keyframe times unless a hard discontinuity is intended
- [ ] For hard cuts, use adjacent times: `{ time: 1.999, value: 0 }, { time: 2.0, value: 100 }`

#### Keyframe Values

**Review checklist:**
- [ ] Vector property keyframes (`position`, `scale`, `anchor`, `skew`) have consistent array lengths across all keyframes
  - `position: [960, 540]` at time 0 and `position: [960, 660]` at time 1 is valid
  - Mismatched lengths (e.g., `[960, 540]` → `[960]`) cause silent truncation
- [ ] Animated `opacity` values stay within `0-100`
- [ ] Animated `scale` values produce intended size (100 = 100%)
- [ ] No unintended large jumps between adjacent keyframe values

#### Easing

**Review checklist:**
- [ ] Easing matches motion intent:
  - `easeOut` / `easeOutCubic`: natural entrances, smooth landings
  - `easeIn`: acceleration into exits
  - `easeInOut`: balanced, cinematic transitions
  - `easeOutBack`: overshoot and settle (playful)
  - `linear`: constant speed, technical motion only
- [ ] Elastic/bounce easings tested at actual fps — they can look different at different frame rates
- [ ] Custom `cubicBezier` values are in `[0, 1]` range for control points

#### Hold Behavior (Before/After Keyframe Range)

**Review checklist:**
- [ ] Before first keyframe: value holds at first keyframe (no unexpected jump)
- [ ] After last keyframe: value holds at last keyframe (no unexpected jump)
- [ ] If looping is intended, verify keyframes cover full loop range

#### Animation + Transform Interaction

**Review checklist:**
- [ ] Combined position + scale + rotation animations produce intended motion
- [ ] When animating both `position` and `anchor`, verify pivot behavior is as expected
- [ ] Parent rig animations tested — child inherits parent motion correctly

---

### 6. Track Matte Review

**Rule**: The layer with `trackMatte` uses the layer **immediately above** it as the matte source.

**Review checklist:**
- [ ] Matte layer is **directly above** the layer with `trackMatte` — no layers in between
- [ ] Matte mode matches source content:
  - `alpha`: use when matte has clean transparency (PNG, vector text, shapes)
  - `luma`: use when matte is grayscale with brightness variation
  - `alphaInverted` / `lumaInverted`: for cutout effects
- [ ] Matte and matted layers overlap spatially at the expected time
- [ ] Matte layer is active (`enabled: true`) and within its `startTime`/`duration` window
- [ ] Matte opacity is high enough to produce visible matte effect

**Debugging track matte:**
1. First check adjacency — this is the #1 cause of broken mattes
2. Then check mode — does the mode match the source type?
3. Then check contrast — does the matte have enough alpha/luma variation?
4. Then check timing — is the matte active when the matted layer is?

---

### 7. Blend Mode Review

**Rule**: Blend modes determine how the current layer combines with pixels beneath it. Layer order matters.

**Review checklist:**
- [ ] Blend mode matches creative intent:
  - `multiply`: darkens (shadows, texture integration)
  - `screen`: brightens (glows, light leaks)
  - `overlay`: contrast shaping
  - `add`: additive light accumulation
  - `colorDodge` / `colorBurn`: aggressive brightening/darkening
  - HSL modes (`hue`, `saturation`, `color`, `luminosity`): color-only transfers
- [ ] High-intensity modes (`add`, `colorDodge`, `colorBurn`, `divide`) have reduced opacity to avoid clipping
- [ ] HSL modes tested at target resolution — they are computationally expensive
- [ ] Layer order verified — swapping two blended layers changes the result
- [ ] Semi-transparent edges reviewed for expected appearance

**Common mistakes:**
- Using `add` at full opacity expecting a subtle glow — result is usually clipped white
- Using `multiply` on a light background expecting darkening — result is subtle or invisible
- Not testing blend results with actual content beneath — preview is essential

---

### 8. Coordinate System Review

OutOcut uses top-left origin `(0,0)` with Y increasing downward.

**Review checklist:**
- [ ] `position: [0, 0]` = top-left corner, not center
- [ ] Center calculation: `center_x = width / 2`, `center_y = height / 2`
- [ ] For 1920×1080: center is `[960, 540]`
- [ ] Shape `position` uses layer space (relative), not composition space
- [ ] Mask coordinates use composition space (absolute), not layer space
- [ ] Angle values: positive = clockwise

| Common Resolution | Center Position |
|------------------|----------------|
| 1920×1080 | [960, 540] |
| 1280×720 | [640, 360] |
| 3840×2160 | [1920, 1080] |
| 1080×1080 | [540, 540] |
| 1920×540 | [960, 270] |

---

## Common Failure Patterns and Fixes

### Pattern 1: Layer at position [0, 0] appears at top-left instead of center

**Cause**: Forgot that `[0, 0]` is top-left, not center.

**Fix**: Calculate center from `width/2` and `height/2`. For 1920×1080: `position: [960, 540]`.

### Pattern 2: Shape doesn't appear where expected

**Cause**: Confused layer-space position (shape `position` relative to layer origin) with composition-space position (layer transform `position` absolute on canvas).

**Fix**: Shape `position: [100, 50]` means the shape starts 100px right and 50px down from the shape layer's top-left origin. Layer `position: [960, 540]` places the layer's anchor at canvas center. These are independent.

### Pattern 3: Mask has no visible effect

**Cause**: Mask path coordinates are in the wrong coordinate space, or mask mode doesn't match the matte content type.

**Fix**: Mask paths are in **composition space** (absolute). Shape paths are in **layer space** (relative). Check that coordinates match the canvas area you expect. Verify `mode` is appropriate (`alpha` for transparency, `luma` for grayscale brightness).

### Pattern 4: Effect order produces wrong visual

**Cause**: Effects applied top-to-bottom in `effects[]`. Swapping blur and glow changes edge quality.

**Fix**: Follow the recommended effect stack order. Test with a simple scene before building complex stacks.

### Pattern 5: Track matte does nothing

**Cause**: Matte layer is not immediately above the matted layer.

**Fix**: The layer with `trackMatte` must have the matte layer as its **immediate predecessor** in the `layers[]` array. No other layers between them.

### Pattern 6: Negative scale causes effect to flip or misbehave

**Cause**: Negative `scale` can invert geometry and cause unexpected behavior with blur, shadow, and directional effects.

**Fix**: Prefer positive `scale` with rotation for flips. Re-test all directional effects after any negative scale. If negative scale is required, reduce effect intensity and verify output carefully.

### Pattern 7: Animation jumps instead of smoothly transitioning

**Cause**: Duplicate keyframe times, or vector length mismatch between keyframes.

**Fix**: For hard cuts, use adjacent times (`1.999` then `2.0`). For smooth motion, verify all vector keyframes have the same number of components. Use `outocut preview --time <sec>` at multiple points to identify exact jump locations.

### Pattern 8: Text unreadable or wrong color

**Cause**: Low contrast against background, or wrong hex format.

**Fix**: Ensure text `color` provides sufficient contrast ratio (minimum 4.5:1 for body text, 3:1 for large text per WCAG guidelines). Test on actual rendered output, not just in JSON inspection.

### Pattern 9: Blend mode produces unexpected color

**Cause**: Wrong layer order, wrong blend mode for the intended effect, or too high opacity.

**Fix**: Preview with `outocut preview` at the relevant moment. Start with reduced opacity (30-50%) for intense blend modes. Verify which layer is "base" (beneath) and which is "blend" (on top).

### Pattern 10: Layer completely invisible

**Cause**: `enabled: false`, or layer covered by opaque layer above, or outside active time range.

**Fix**: In order: (1) Check `enabled: true`. (2) Verify layer is within `startTime`/`duration`. (3) Check `inPoint`/`outPoint` trim range. (4) Verify no opaque layer above in the `layers[]` array.

---

## Pre-Render Checklist

Run through this list before every render:

### Structure
- [ ] `outocut validate project.outocut` passes with no errors
- [ ] All `assetId` references resolve to declared assets
- [ ] All `compositionId` references resolve to existing compositions
- [ ] All `parentId` references point to existing layers
- [ ] No duplicate layer IDs in any composition
- [ ] `settings.duration` matches main composition `duration`

### Timing
- [ ] Previewed at key moments with `outocut preview --time <sec>`
- [ ] All layers appear/disappear at intended times
- [ ] Animation timing verified at target fps
- [ ] No accidental time gaps in continuous sequences

### Visual
- [ ] Layout verified: elements in correct positions
- [ ] Layer ordering verified: no unintended occlusion
- [ ] Effect results match intent (intensity, order, stacking)
- [ ] Text readable and correctly positioned
- [ ] Colors consistent with brand/project reference
- [ ] Checked on target output resolution

### Audio (if applicable)
- [ ] Audio layers sync with visual events
- [ ] No audio artifacts from `inPoint`/`outPoint` trimming
- [ ] Audio level appropriate for delivery format

### Performance
- [ ] Review pass rendered (`--preset veryfast --crf 30+`) and reviewed
- [ ] No unexpected slowdowns in heavy scenes
- [ ] Heavy effect stacks verified at target resolution

---

## Post-Render Validation

After rendering, verify:

- [ ] Output file plays without errors
- [ ] Duration matches `settings.duration`
- [ ] Resolution matches intended output (not a downsample artifact)
- [ ] Frame rate is correct (30fps project → 30fps output)
- [ ] No compression artifacts in critical areas (text, graphics)
- [ ] Audio/video sync maintained throughout
- [ ] No visible layout breaks on playback in multiple players

---

## Quick Reference: Review Priority by Change Type

| If you changed... | Priority review items |
|---|---|
| Any `position` value | Anchor, coordinate space, canvas bounds |
| Any `scale` value | Negative flip, pixelation, effect interaction |
| Any `anchor` value | Pivot point, position makes sense |
| Effect `params` | Value ranges, effect order |
| Effect keyframes | Keyframe structure (`keyframes.<param>`), range validation |
| Shape `position` | Layer space vs composition space confusion |
| Mask `path` | Composition space, adjacency, mode |
| `trackMatte` | Layer order (immediate adjacency above), mode match |
| `blendMode` | Layer order, opacity, preview result |
| Animation keyframes | Time ordering, vector length consistency, easing |
| `parentId` | Parent active time, inheritance behavior |
| `enabled` | Intentional, not accidentally disabled |

---

## See Also

- [Best Practices](best-practices.md) — Project organization and workflow patterns
- [Coordinate System](coordinate-system.md) — Detailed coordinate space reference
- [Transforms](transforms.md) — Transform property reference
- [Effects](effects.md) — Effect parameter and stacking reference
- [Shapes and Masks](shapes-masks.md) — Shape and mask data structures
- [Animation System](animation-system.md) — Keyframe and easing reference
- [Track Matte](track-matte.md) — Track matte setup and troubleshooting
- [Blend Modes](blend-modes.md) — Blend mode formulas and use cases