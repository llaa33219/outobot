# Animation System

Comprehensive, implementation-accurate reference for OutOcut animation behavior.

- Author: BLOUplanet
- License: Apache 2.0

## Overview

OutOcut animations are driven by `AnimatedProperty<T>` and runtime evaluation in `Animator` (`src/animation.rs`).

- All keyframe times are seconds (`f64`).
- Each animated segment uses the **starting keyframe's easing**.
- Values are linearly interpolated after easing remaps progress.
- Evaluator currently supports numeric scalar (`f64`) and numeric vector (`Vec<f64>`) interpolation.

## 1) Keyframe System

### How keyframes work

At render/preview time, OutOcut evaluates each property at current `time`:

1. If `keyframes` is `null` or empty, it returns static `value`.
2. Keyframes are sorted by `time` ascending before evaluation.
3. If `time <= first.time`, first keyframe value is returned (hold before start).
4. If `time >= last.time`, last keyframe value is returned (hold after end).
5. Otherwise, it finds the segment `[k1, k2]` containing `time`.
6. `progress = (time - k1.time) / (k2.time - k1.time)`.
7. `eased = apply_easing(progress, k1.easing)`.
8. Interpolate `k1.value -> k2.value` by `eased`.

### Keyframe JSON structure

```json
{
  "time": 1.25,
  "value": [960, 540],
  "easing": "easeInOutCubic"
}
```

- `time`: required `f64` seconds.
- `value`: required JSON value (number for scalar properties, array for vector properties).
- `easing`: optional; if omitted, behaves as `linear`.

### Multiple keyframes at the same time

OutOcut permits duplicate `time` values (no validation error), but results can be unintuitive:

- Keyframes are sorted by time; equal-time order follows sort behavior and should not be relied on for creative intent.
- During segment search, the first matching interval wins.
- At duplicate-time boundaries, the value may effectively "snap" to whichever interval is matched first.
- In practice: avoid same-time duplicates unless you intentionally want a discontinuity.

Recommended pattern for hard cuts:

```json
"keyframes": [
  { "time": 1.999, "value": 0 },
  { "time": 2.000, "value": 100 }
]
```

### Keyframe interpolation logic

Scalar interpolation (`f64`):

```text
v = v1 + (v2 - v1) * eased_t
```

Vector interpolation (`Vec<f64>`): component-wise linear interpolation using `zip`:

```text
out[i] = a[i] + (b[i] - a[i]) * eased_t
```

Important: `zip` truncates to the shorter vector length.

## 2) Easing Functions (All OutOcut Variants)

OutOcut currently exposes these easing variants in `Easing`:

- Basic: `linear`, `easeIn`, `easeOut`, `easeInOut`
- Cubic: `easeInCubic`, `easeOutCubic`, `easeInOutCubic`
- Back: `easeInBack`, `easeOutBack`, `easeInOutBack` (`c1 = 1.70158`)
- Elastic: `easeInElastic`, `easeOutElastic`, `easeInOutElastic`
- Bounce: `easeInBounce`, `easeOutBounce`, `easeInOutBounce`
- Custom: `cubicBezier(x1, y1, x2, y2)`

`t` below means normalized segment progress in `[0,1]`.

### Basic

#### `linear`

- Motion: constant speed, no acceleration.
- Formula: `f(t) = t`
- Use cases: technical motion, UI indicators, camera pans needing uniform velocity.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "linear" }
```

#### `easeIn`

- Motion: starts slow, accelerates.
- Formula: `f(t) = t^2`
- Use cases: objects beginning movement, energy build-up.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeIn" }
```

#### `easeOut`

- Motion: starts fast, decelerates smoothly.
- Formula: `f(t) = 1 - (1 - t)^2`
- Use cases: natural stops, settling into final position.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeOut" }
```

#### `easeInOut`

- Motion: slow start and slow end, faster middle.
- Formula:

```text
f(t) = 2t^2                              , t < 0.5
f(t) = 1 - ((-2t + 2)^2)/2              , t >= 0.5
```

- Use cases: general-purpose transitions, balanced UI/graphic motion.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInOut" }
```

### Cubic

#### `easeInCubic`

- Motion: very soft start, strong acceleration.
- Formula: `f(t) = t^3`
- Use cases: dramatic launches, kinetic typography entrances.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInCubic" }
```

#### `easeOutCubic`

- Motion: strong initial movement, very smooth landing.
- Formula: `f(t) = 1 - (1 - t)^3`
- Use cases: polished exits and snap-to-rest motion.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeOutCubic" }
```

#### `easeInOutCubic`

- Motion: pronounced S-curve, smooth and cinematic.
- Formula:

```text
f(t) = 4t^3                              , t < 0.5
f(t) = 1 - ((-2t + 2)^3)/2              , t >= 0.5
```

- Use cases: hero element motion, camera moves, premium-feeling transitions.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInOutCubic" }
```

### Back (`c1 = 1.70158`)

#### `easeInBack`

- Motion: moves slightly backward first, then accelerates forward.
- Formula:

```text
c1 = 1.70158
c3 = c1 + 1
f(t) = c3*t^3 - c1*t^2
```

- Use cases: anticipation before forward motion.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInBack" }
```

#### `easeOutBack`

- Motion: overshoots target, then settles.
- Formula:

```text
c1 = 1.70158
c3 = c1 + 1
f(t) = 1 + c3*(t - 1)^3 + c1*(t - 1)^2
```

- Use cases: punchy UI cards, pop-in endings.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeOutBack" }
```

#### `easeInOutBack`

- Motion: anticipation + overshoot on one curve.
- Formula:

```text
c1 = 1.70158
c2 = c1 * 1.525
f(t) = ((2t)^2 * ((c2 + 1) * 2t - c2)) / 2                                 , t < 0.5
f(t) = (((2t - 2)^2 * ((c2 + 1) * (2t - 2) + c2)) + 2) / 2                 , t >= 0.5
```

- Use cases: energetic logos and playful brand animations.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInOutBack" }
```

### Elastic

#### `easeInElastic`

- Motion: spring-like pullback and rapid oscillation while entering.
- Algorithm:

```text
if t == 0 or t == 1: return t
c4 = (2*pi)/3
f(t) = -abs(2^(10t - 10) * sin((10t - 10.75) * c4))
```

- Use cases: bouncy reveals, playful interfaces.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInElastic" }
```

#### `easeOutElastic`

- Motion: exits quickly then oscillates into rest.
- Formula:

```text
if t == 0 or t == 1: return t
c4 = (2*pi)/3
f(t) = 2^(-10t) * sin((10t - 0.75) * c4) + 1
```

- Use cases: friendly settle motion for popups/buttons.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeOutElastic" }
```

#### `easeInOutElastic`

- Motion: elastic at both start and end.
- Formula:

```text
if t == 0 or t == 1: return t
c5 = (2*pi)/4.5
f(t) = -(2^(20t - 10) * sin((20t - 11.125) * c5)) / 2                       , t < 0.5
f(t) =  (2^(-20t + 10) * sin((20t - 11.125) * c5)) / 2 + 1                  , t >= 0.5
```

- Use cases: stylized character/object motion.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInOutElastic" }
```

### Bounce

`easeOutBounce` uses piecewise quadratic segments:

```text
n1 = 7.5625
d1 = 2.75

if t < 1/d1:       n1*t^2
else if t < 2/d1:  n1*(t - 1.5/d1)^2 + 0.75
else if t < 2.5/d1:n1*(t - 2.25/d1)^2 + 0.9375
else:              n1*(t - 2.625/d1)^2 + 0.984375
```

#### `easeInBounce`

- Motion: bounce happens near start (inverted out-bounce).
- Formula: `f(t) = 1 - easeOutBounce(1 - t)`
- Use cases: comedic or attention-grabbing entrances.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInBounce" }
```

#### `easeOutBounce`

- Motion: drops and bounces near the end.
- Formula: `f(t) = easeOutBounce(t)`
- Use cases: landings and impact moments.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeOutBounce" }
```

#### `easeInOutBounce`

- Motion: bounce near both start and end.
- Formula:

```text
f(t) = (1 - easeOutBounce(1 - 2t)) / 2   , t < 0.5
f(t) = (1 + easeOutBounce(2t - 1)) / 2   , t >= 0.5
```

- Use cases: energetic loops and playful transitions.
- Example JSON:

```json
{ "time": 0.5, "value": 50, "easing": "easeInOutBounce" }
```

### Custom

#### `cubicBezier(x1, y1, x2, y2)`

- Motion: user-defined curve shape.
- Algorithm in OutOcut:
  - Computes cubic coefficients from control points.
  - Evaluates a cubic polynomial.
  - Runs Newton-style iteration (`solve_cubic_bezier`) for approximation.
  - Returns solved normalized progress in `[0,1]`.
- Use cases: matching brand timing curves or CSS-like custom motion.

Example JSON (serde enum tuple form):

```json
{ "time": 0.5, "value": 50, "easing": { "cubicBezier": [0.42, 0.0, 0.58, 1.0] } }
```

## 3) `AnimatedProperty` Structure

Every animatable field follows this shape:

```json
{
  "value": 100,
  "keyframes": null
}
```

Or animated:

```json
{
  "value": 100,
  "keyframes": [
    { "time": 0.0, "value": 0, "easing": "easeOutCubic" },
    { "time": 1.0, "value": 100 }
  ]
}
```

- `value`: default/static value; also fallback when keyframes missing.
- `keyframes`: optional array; when present and non-empty, runtime uses keyframed values.

Common transform usage:

```json
"transform": {
  "anchor":   { "value": [960, 540], "keyframes": null },
  "position": { "value": [960, 540], "keyframes": [ ... ] },
  "scale":    { "value": [100, 100], "keyframes": [ ... ] },
  "rotation": { "value": 0, "keyframes": [ ... ] },
  "skew":     { "value": [0, 0], "keyframes": null },
  "skewAxis": { "value": 0, "keyframes": null }
}
```

Also animatable at layer level:

```json
"opacity": {
  "value": 100,
  "keyframes": [
    { "time": 0.0, "value": 0, "easing": "easeOut" },
    { "time": 0.5, "value": 100 }
  ]
}
```

## 4) Interpolation Details

### `f64` interpolation

Used for scalar properties such as:

- `opacity`
- `rotation`
- `skewAxis`

Implementation:

```text
v = v1 + (v2 - v1) * eased_t
```

### `Vec<f64>` interpolation

Used for vector properties such as:

- `position` (`[x, y]`)
- `scale` (`[x%, y%]`)
- `anchor` (`[x, y]`)
- `skew` (`[x, y]`)

Implementation is pairwise interpolation with `zip`.

Practical implication:

- `[x, y]` -> `[x, y]` works as expected.
- If lengths differ, extra components are dropped.

### Color interpolation notes

Current OutOcut runtime does **not** provide dedicated color keyframe interpolation in `Animator`.

- Colors in layer content are hex strings (e.g. `"#ff0000"`) and are rendered as-is.
- Numeric interpolation paths (`evaluate_f64`, `evaluate_vec_f64`) do not blend color strings.

Recommended approaches:

1. Use crossfades between two layers/colors via animated `opacity`.
2. Use effects pipeline when color-keyframing support is added.

## 5) Common Animation Patterns (Practical)

### Fade in / fade out

```json
"opacity": {
  "value": 100,
  "keyframes": [
    { "time": 0.0, "value": 0, "easing": "easeOut" },
    { "time": 0.6, "value": 100 },
    { "time": 4.0, "value": 100 },
    { "time": 4.6, "value": 0, "easing": "easeIn" }
  ]
}
```

### Scale up / scale down (pop)

```json
"scale": {
  "value": [100, 100],
  "keyframes": [
    { "time": 0.0, "value": [70, 70], "easing": "easeOutBack" },
    { "time": 0.4, "value": [100, 100] },
    { "time": 2.8, "value": [100, 100] },
    { "time": 3.2, "value": [85, 85], "easing": "easeInCubic" }
  ]
}
```

### Position slide (left to center)

```json
"position": {
  "value": [960, 540],
  "keyframes": [
    { "time": 0.0, "value": [-300, 540], "easing": "easeOutCubic" },
    { "time": 1.0, "value": [960, 540] }
  ]
}
```

### Rotation spin

```json
"rotation": {
  "value": 0,
  "keyframes": [
    { "time": 0.0, "value": 0 },
    { "time": 2.0, "value": 360, "easing": "linear" }
  ]
}
```

### Combined animation (intro reveal)

```json
{
  "opacity": {
    "value": 100,
    "keyframes": [
      { "time": 0.0, "value": 0, "easing": "easeOut" },
      { "time": 0.5, "value": 100 }
    ]
  },
  "transform": {
    "position": {
      "value": [960, 540],
      "keyframes": [
        { "time": 0.0, "value": [960, 620], "easing": "easeOutCubic" },
        { "time": 0.5, "value": [960, 540] }
      ]
    },
    "scale": {
      "value": [100, 100],
      "keyframes": [
        { "time": 0.0, "value": [92, 92], "easing": "easeOutBack" },
        { "time": 0.5, "value": [100, 100] }
      ]
    },
    "rotation": {
      "value": 0,
      "keyframes": [
        { "time": 0.0, "value": -6, "easing": "easeOutCubic" },
        { "time": 0.5, "value": 0 }
      ]
    },
    "anchor": { "value": [960, 540], "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  }
}
```

## Cautions and Edge Cases

### Keyframe time ordering

- Runtime sorts by `time`, but you should author keyframes in ascending order for readability and predictability.

### Time outside keyframe range

- Before first keyframe: first keyframe value is held.
- After last keyframe: last keyframe value is held.

### Many keyframes and performance

- Evaluation scans sorted keyframes linearly per property per frame.
- Large keyframe counts across many layers increase CPU cost.
- Practical guidance:
  - Keep only perceptually necessary keys.
  - Prefer fewer keys with stronger easing.
  - Avoid redundant keys with identical values.

### Floating-point precision

- Times and interpolation use `f64`; tiny precision differences can happen at boundaries.
- Use clean decimal times aligned to frame rate when exact timing matters.
  - Example at 30fps: step size is `1/30 = 0.033333...`.
- Avoid over-reliance on exact equality checks when generating keyframes programmatically.

### Vector shape consistency

- For vector properties, keep array lengths consistent across keyframes.
- Mismatched lengths can silently drop trailing components due to pairwise `zip` interpolation.

## Quick Reference Snippet

```json
"rotation": {
  "value": 0,
  "keyframes": [
    { "time": 0.0, "value": 0, "easing": "easeInOutCubic" },
    { "time": 1.0, "value": 90 },
    { "time": 2.0, "value": 180, "easing": { "cubicBezier": [0.22, 0.61, 0.36, 1.0] } },
    { "time": 3.0, "value": 360 }
  ]
}
```