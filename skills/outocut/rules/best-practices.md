# OutOcut Best Practices Guide

Comprehensive production guide for building maintainable, performant, and reliable OutOcut projects.

- Author: BLOUplanet
- License: Apache 2.0

## 1. Project Organization

Strong organization prevents timeline complexity from turning into debugging cost later.

### Recommended directory structure

Use a predictable structure that separates source assets, reusable compositions, and delivery outputs.

```text
my-project/
  project.outocut
  assets/
    video/
    audio/
    images/
    fonts/
    pre-rendered/
  compositions/
    main/
    precomps/
  exports/
    review/
    final/
  refs/
    storyboards/
    styleframes/
```

Practical rules:

- Keep `project.outocut` at repository root for simple CLI usage.
- Use relative paths in assets so the project is portable.
- Reserve `exports/review` for draft renders and `exports/final` for delivery files.
- Keep pre-rendered intermediates in `assets/pre-rendered` so they can be reused as media layers.

### Asset management best practices

Treat assets like code dependencies: stable naming, clear ownership, and minimal duplication.

- Use stable `id` values in `assets[]` and avoid renaming unless necessary.
- Prefer one source file per creative element, then reuse it across compositions.
- Normalize incoming assets before import:
  - Video: consistent frame rate and color space.
  - Audio: consistent sample rate and channels.
  - Images: size close to target resolution to avoid excessive scaling cost.
- Keep original source files immutable; create explicit optimized proxies when needed.

Example asset block with clear naming:

```json
"assets": [
  { "id": "vid_intro_main", "type": "video", "path": "assets/video/intro-main-4k.mp4" },
  { "id": "aud_bgm_primary", "type": "audio", "path": "assets/audio/bgm-primary.wav" },
  { "id": "img_logo_white", "type": "image", "path": "assets/images/logo-white.png" },
  { "id": "font_heading_bold", "type": "font", "path": "assets/fonts/Heading-Bold.ttf" }
]
```

### Composition organization (main vs pre-comps)

Split compositions by responsibility:

- `main`: final assembly, timing, global transitions, and audio mix alignment.
- `precomps`: reusable modules (titles, lower-thirds, logo bumpers, icon rigs, repeated cards).

Recommended pattern:

1. Build each visual module as a precomp.
2. Keep module logic local to that precomp.
3. Reference precomps from `main` using composition layers.
4. Apply scene-level timing and transforms in `main` only.

Benefits:

- Lower cognitive load while editing.
- Reusable animation modules.
- Safer iteration without breaking unrelated scenes.

### Naming conventions

Use deterministic names that encode role and category.

Suggested schema:

- Composition IDs: `comp_<area>_<purpose>`
- Layer IDs: `lyr_<type>_<purpose>`
- Null controllers: `ctrl_<group>_<purpose>`
- Assets: `<kind>_<content>_<variant>`

Examples:

- `comp_main_master`
- `comp_title_intro`
- `lyr_text_headline`
- `ctrl_cards_global`
- `img_bg_gradient_soft`

Avoid:

- Generic names (`layer1`, `new comp`, `text copy`).
- Ambiguous reuse IDs (`logo`, `audio1`).
- Mixed casing conventions in the same project.

---

## 2. Performance Tips

Performance in OutOcut depends heavily on layer count, keyframe complexity, and effect cost.

### Limit number of active layers

The renderer evaluates active layers at a given time. Reduce overlap windows.

- Shorten `duration` and use precise `inPoint`/`outPoint` trimming.
- Stagger elements that do not need to overlap.
- Disable heavy layers outside visible windows.

```json
{
  "id": "lyr_fx_glow",
  "enabled": true,
  "startTime": 3.0,
  "duration": 1.2,
  "inPoint": 0.0,
  "outPoint": 1.2
}
```

### Use null layers for grouping instead of deeply nested compositions

Parenting via `null` controller layers is often cheaper and easier to debug than over-nesting precomps.

- Group related layers under a single controller.
- Animate shared transforms once at parent level.
- Keep parent chains short and intentional.

```json
{
  "id": "ctrl_title_block",
  "type": "null",
  "name": "Title Block Controller"
}
```

Child layers set `parentId: "ctrl_title_block"`.

### Pre-render complex effects when possible

Heavy blur/glow/repeater stacks can be pre-rendered and re-imported as media assets.

- Pre-render static or low-variation sections.
- Keep the original procedural comp for future edits.
- Swap to pre-rendered footage for final assembly and fast previews.

### Optimize keyframe count (do not animate every frame)

Dense keyframe data increases file size and per-frame interpolation work.

- Keep only perceptually meaningful keys.
- Use easing to shape motion between sparse keys.
- Remove duplicate-value keys unless needed for hard timing boundaries.

### Use appropriate resolution for output

Work at the lowest resolution that still reflects quality decisions.

- Iteration: 720p or proxy workflows.
- Review: 1080p moderate quality.
- Delivery: target platform resolution (1080p/4K) with final quality settings.

---

## 3. Animation Best Practices

Good animation is intentional timing, not keyframe quantity.

### Use keyframes sparingly; fewer is better

- Start with two keys (start/end).
- Add a third key only to create a specific story beat (overshoot, settle, anticipation).
- Prefer stronger easing curves before adding extra keys.

### Choose easing based on motion type

Quick guide:

- `linear`: technical or constant-speed movement.
- `easeOut` / `easeOutCubic`: natural entrances and smooth landings.
- `easeIn`: acceleration into exits.
- `easeInOutCubic`: premium, balanced transitions.
- `easeOutBack` / bounce variants: expressive or playful motion.

### Match easing to creative feel

- Playful brand: back/bounce/elastic families in moderation.
- Corporate/professional: cubic and standard ease families.
- Editorial/technical: linear + subtle ease only where needed.

Example expressive pop-in:

```json
"scale": {
  "value": [100, 100],
  "keyframes": [
    { "time": 0.0, "value": [70, 70], "easing": "easeOutBack" },
    { "time": 0.35, "value": [100, 100] }
  ]
}
```

### Test animations at actual frame rate

Animation can look correct at coarse checks but fail at final fps.

- Validate timing on the project's target fps (24/30/60).
- Check fast motions and short reveals frame-by-frame.
- Avoid sub-frame timing assumptions.

### Use hold-style keyframes for on/off behavior

For binary visibility states, abrupt transitions are clearer than micro-fades.

Practical approach:

- Keep opacity/value constant until switch point.
- Snap to next value at switch boundary.

```json
"opacity": {
  "value": 100,
  "keyframes": [
    { "time": 1.999, "value": 0 },
    { "time": 2.000, "value": 100 }
  ]
}
```

---

## 4. Layer Management

Layer hygiene is one of the highest-leverage habits for large projects.

### Name layers descriptively

Layer names should communicate function and scope immediately.

Good examples:

- `Headline Primary`
- `LowerThird Background`
- `Product Shot B-Roll`
- `Global Color Grade`

### Use null layers as parent anchors

- Create one null controller per logical group.
- Parent visual layers to this controller.
- Animate the null for coherent multi-layer motion.

### Keep composition tree flat when possible

- Prefer a flat structure with a few reusable precomps over deep nesting.
- Avoid precomp chains where each layer only wraps one child.
- Keep precomps task-focused (one module, one purpose).

### Disable unused layers instead of deleting

Use `enabled: false` to preserve alternatives during iteration.

```json
{
  "id": "lyr_alt_title_v2",
  "enabled": false,
  "name": "Alt Title Option"
}
```

This allows A/B versions without permanently losing work.

---

## 5. Color Management

Color consistency is both a technical and creative requirement.

### Use consistent color format (hex recommended)

- Standardize on hex values in project JSON.
- Prefer uppercase or lowercase consistently across project files.
- Include alpha explicitly when needed (`#RRGGBBAA`).

```json
"content": {
  "color": "#0F172A"
}
```

### Be aware of sRGB vs linear color behavior

- Most asset pipelines and displays are sRGB-oriented.
- Mixed sources (graded footage, exported graphics) can shift contrast/saturation.
- Review brand colors against trusted references after compositing and encoding.

### Test on multiple displays

At minimum, verify on:

- Primary editing monitor.
- Consumer laptop display.
- Mobile display (if social delivery).

Check for:

- Midtone contrast.
- Highlight clipping.
- Text/background readability.
- Skin tone shifts.

---

## 6. Rendering Workflow

Use an iterative pipeline that separates fast feedback from final quality output.

### Test with lower quality settings first

Use faster presets and higher CRF values during development.

```bash
outocut render project.outocut -o exports/review/iteration.mp4 --preset veryfast --crf 30
```

### Use watch mode during iteration

`watch` keeps validation feedback tight while editing.

```bash
outocut watch project.outocut
```

Pair with quick checks:

```bash
outocut preview project.outocut --time 5.0 --duration 2.0
```

### Render to PNG sequence for complex projects

For heavy scenes and safer recovery workflows, render image sequences first (where your pipeline supports sequence output), then encode.

Why:

- Recovery after interruption starts from last frame, not full re-render.
- Easier frame-level QA.
- Better handoff to external encode pipelines.

### Use appropriate CRF for delivery vs review

Suggested targets:

- Review drafts: `CRF 28-32`
- Internal approvals: `CRF 22-26`
- Final delivery master: `CRF 16-20` (content-dependent)

Final quality example:

```bash
outocut render project.outocut -o exports/final/master-1080p.mp4 --preset slow --crf 18
```

---

## 7. Common Mistakes to Avoid

### Circular composition references

Do not create recursive chains like `A -> B -> A`.

- Keep a one-way composition dependency graph.
- Validate after structural changes.

### Orphaned assets (referenced but not used)

- Periodically audit `assets[]` against actual layer references.
- Remove dead assets to reduce project noise and confusion.

### Too many keyframes causing large files

- Avoid exported keyframes for every frame unless strictly required.
- Decimate keyframes from external tools before import.

### Forgetting layer enabled state

- A disabled layer can look like missing assets or broken animation.
- Check `enabled` first before deep debugging.

### `trackMatte` ordering errors

Matte behavior is order-sensitive.

- Keep matte-related layers adjacent.
- Confirm expected stacking and matte mode (`alpha`, `luma`, inverted variants).

### Negative scale with some effects

Negative scale can invert geometry and produce unexpected effect behavior.

- Prefer positive scale with rotation/anchor adjustments when possible.
- Re-test blur, shadow, and directional effects after flips.

### Blend mode compatibility not verified

Blend modes can differ visually by content and pipeline.

- Test critical shots at target output settings.
- Verify text readability and color consistency after blend interactions.

---

## 8. Debugging Tips

### Use preview with `--time` to inspect layer state

Jump directly to problematic moments.

```bash
outocut preview project.outocut --time 12.4
```

For short windows:

```bash
outocut preview project.outocut --time 12.4 --duration 1.0
```

### Use validate to catch project/schema issues

```bash
outocut validate project.outocut
```

Use this after major edits, especially composition rewires and asset refactors.

### Export JSON to inspect final structure

```bash
outocut export-json project.outocut --pretty > debug-project.json
```

Inspect exported structure when authored files use comments or generated tooling.

### Check layer ordering (bottom renders first)

OutOcut layer arrays are back-to-front.

- Earlier layer entries render first (background).
- Later layer entries render on top (foreground).

When visuals are missing, first verify:

1. Is the layer active at current time?
2. Is `enabled` true?
3. Is another opaque layer above it?
4. Are blend/matte settings hiding it?

---

## 9. File Size Optimization

Large project files are slower to review, diff, and maintain.

### Remove unused assets

- Delete asset entries not referenced by any layer.
- Remove stale alternate media that is no longer in use.

### Reuse references to shared compositions

Instead of duplicating layer logic, reference one precomp from multiple places.

- Smaller JSON.
- Easier change propagation.
- Lower risk of drift between duplicated modules.

### Keep keyframe count reasonable

- Keep essential timing keys.
- Remove redundant keys with unchanged values.
- Prefer easing adjustments to keyframe inflation.

### Pre-render static sections

Long static or repeatable motion sections can be replaced with rendered clips.

- Reduces project complexity.
- Can improve render stability for very dense scenes.
- Makes final assembly cleaner.

---

## Practical Workflow Checklist

Use this as a quick pre-delivery pass:

1. `outocut validate project.outocut`
2. Review critical timestamps with `outocut preview --time ...`
3. Confirm layer naming and disabled alternatives are intentional.
4. Verify no circular composition references.
5. Confirm color consistency on at least two displays.
6. Render review output (`--preset veryfast --crf 28+`).
7. Render final output (`--preset slow --crf 16-20`, target-specific).

If any step fails, fix structure first (IDs, references, ordering), then retune animation/effects.
