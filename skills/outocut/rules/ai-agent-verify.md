# AI Agent Visual Self-Verification Guide

Guide for AI agents that render OutOcut projects and need to verify, visually, whether the output matches their own intent.

- **Audience**: AI agents using multimodal LLMs (vision-capable)
- **Purpose**: Enable agents to autonomously check rendered output and self-correct without human intervention
- **Prerequisite**: Agent has a defined intent for the video (from user instruction, task prompt, or self-generated spec)

---

## Core Principle

An AI agent generates JSON based on its **intent**. Visual self-verification confirms whether the rendered output **satisfies that intent**.

```
Intent (from task/instruction)
    │
    ▼
Generate .outocut JSON
    │
    ▼
Render → Extract frame(s)
    │
    ▼
Analyze: "Does this match my intent?"
    │
    ├── YES ──→ Finalize
    │
    └── NO ──→ Identify problem → Fix JSON → Re-render → Loop
```

The agent's intent is the **ground truth** for verification. Everything in this guide exists to operationalize that comparison.

---

## Phase 1: Define Verification Criteria Before Authoring

**Do this before writing a single line of JSON.** Verification is only possible if the agent knows what it is verifying.

### 1.1 Decompose Intent into Specific Criteria

Break the overall intent into **observable, verifiable statements**:

```
❌ Vague: "Make an intro that looks professional"

✅ Specific and verifiable:
  - Title text "OUTOCUT" appears centered at [960, 540]
  - Background is dark (#0F172A)
  - Logo appears in bottom-right corner at [1700, 920] with 60% scale
  - Fade-in animation completes within 1.5 seconds
  - Glow effect on title is visible but subtle (not overwhelming)
  - Total duration: 5 seconds
```

For each criterion, note:
- **Type**: position | color | timing | animation | effect | layout | composition
- **How to verify**: coordinate check | color sampling | frame extraction | sequence analysis
- **Priority**: critical (must pass) | important (should pass) | nice-to-have (warn but proceed)

### 1.2 Store Intent as Verification Checklist

Keep the decomposed intent accessible throughout the workflow. Example format:

```json
{
  "verification_checklist": [
    {
      "criterion": "Title centered horizontally",
      "type": "position",
      "detail": "text anchor at [960, 540], text alignment center",
      "verify_via": "frame_extraction",
      "priority": "critical"
    },
    {
      "criterion": "Glow not overwhelming",
      "type": "effect",
      "detail": "glow opacity 30-50, radius 12-20",
      "verify_via": "frame_extraction",
      "priority": "important"
    },
    {
      "criterion": "Animation completes in 1.5s",
      "type": "timing",
      "detail": "keyframes up to t=1.5",
      "verify_via": "sequence_extraction",
      "priority": "important"
    }
  ]
}
```

This checklist is the **contract** between the agent's intent and the verification process.

---

## Phase 2: Render and Extract for Verification

### 2.1 When to Extract Frames

Extract frames at **strategic moments**, not continuously:

| Animation phase | When to extract | What to check |
|---------------|----------------|---------------|
| Start state | `time = startTime` | Initial positions, opacity before animation |
| Key moments | `time = t_k` for each keyframe | Each keyframe value visually confirmed |
| Mid-animation | `time = halfway between keys` | Smooth interpolation, no jumps |
| End state | `time = endTime` | Final resting state |
| Specific check moments | Time when specific elements are critical | Effect peak, text fully readable, etc. |

### 2.2 Render Commands for Verification

**For single-frame checks** (fast, most common):

```bash
# Extract one frame at a specific time
outocut preview project.outocut --time 1.5 --duration 0.001 -o /tmp/verify_frame.png
# Note: if preview doesn't support direct PNG, render a tiny section:
outocut render project.outocut -o /tmp/verify_section.mp4 --time 1.5 --duration 0.1 --preset ultrafast --crf 35
ffmpeg -i /tmp/verify_section.mp4 -vf "fps=1" -frames:v 1 /tmp/verify_frame.png
```

**For animation checks** (verify motion path):

```bash
# Extract frames at regular intervals
outocut render project.outocut -o /tmp/verify_timeline.mp4 --preset ultrafast --crf 35
mkdir -p /tmp/frames
ffmpeg -i /tmp/verify_timeline.mp4 -vf "fps=2" /tmp/frames/frame_%03d.png
# Review frames: frame_001.png, frame_003.png, frame_005.png, etc.
```

**For effect intensity checks** (isolate a specific moment):

```bash
# Render just the relevant segment
outocut render project.outocut -o /tmp/verify_effect.mp4 \
  --time 0.8 --duration 0.5 --preset ultrafast --crf 35
ffmpeg -i /tmp/verify_effect.mp4 -vf "select=eq(n\,5)" -frames:v 1 /tmp/verify_effect_frame.png
```

### 2.3 Selective Rendering Strategy

Full-quality renders are slow. Use a tiered approach:

```
Tier 1 — Fast check (first pass):
  --preset ultrafast --crf 40 --width 640 --height 360
  Purpose: Verify layout, positioning, rough effect visibility

Tier 2 — Medium check (second pass, after fixes):
  --preset veryfast --crf 30 --width 1280 --height 720
  Purpose: Verify color, effect intensity, text readability

Tier 3 — Full check (final pass):
  --preset medium --crf 22 --width 1920 --height 1080
  Purpose: Final quality confirmation before delivery
```

Only advance to the next tier after the current tier passes.

---

## Phase 3: Visual Analysis Protocol

This is the core of self-verification. The agent (via its multimodal LLM) analyzes extracted frames against its intent.

### 3.1 Frame Analysis Prompt Template

Use a structured prompt for consistent analysis:

```
## Frame Analysis Prompt

CONTEXT: [Brief description of what this video should show]
INTENT CHECKLIST:
  1. [Criterion 1, e.g., "Title text is centered horizontally"]
  2. [Criterion 2, e.g., "Background is dark (#0F172A range)"]
  3. [Criterion 3, e.g., "Logo appears in bottom-right quadrant"]
  [...]

FRAME INFO:
  - Extracted at: t=[seconds]
  - Composition: [width]×[height]
  - Expected: [what you expect to see at this time based on your JSON]

ANALYSIS REQUEST:
  For each criterion in the INTENT CHECKLIST:
    - PASS: Describe exactly what you see that confirms it
    - FAIL: Describe exactly what you see that contradicts it
    - UNCERTAIN: State why you cannot determine from this frame

  Overall assessment: Does this frame match the intent? [YES / PARTIAL / NO]

  If NO or PARTIAL:
    - What specifically is wrong?
    - What is the likely cause in the JSON? (position? scale? opacity? effect param?)
    - What specific fix would resolve it?
```

### 3.2 What to Look For by Category

**Position and Layout**:
```
What to check: Is the element where it should be?
How to check: 
  - Draw invisible crosshair at canvas center [width/2, height/2]
  - Is the element's visual center at that point? (for centered elements)
  - Is the element in the correct quadrant/corner?
  - Are multiple elements correctly spaced relative to each other?

⚠️ AI AGENT COORDINATE WARNING:
  - (0, 0) is ALWAYS TOP-LEFT, NOT center
  - Center of 1920×1080 is [960, 540]
  - Bottom-left is [0, 1080], NOT [0, 0]
  - NEVER use [0, 0] for "center" positioning

Typical failures:
  - Element appears at top-left when it should be centered (position: [0,0] instead of [960,540])
  - Element off-screen (position outside canvas bounds)
  - Elements overlapping when they should be separate
  - Agent assumes (0,0) means center → element ends up at top-left instead
  - Agent assumes layer anchor is "center by default" → rotation/scale pivots wrong
    * FIX: Always explicitly set anchor: [width/2, height/2] for center pivot
```

**Scale and Size**:
```
What to check: Is the element the right size?
How to check:
  - Estimate what percentage of the canvas the element occupies
  - Compare relative sizes of elements (is A twice as big as B?)
  - Check if logos/icons are legible at intended scale
Typical failures:
  - Logo too small to read (scale < 40% when should be 60%)
  - Title text too large, overflowing or too small
  - Shape fills the whole canvas when it should be a small accent
```

**Color and Brightness**:
```
What to check: Does the color match the intent?
How to check:
  - Note the dominant background color — is it in the right range?
  - Check text/element contrast against background
  - Check if glow/lighting effects are the intended color
Typical failures:
  - Background #FFFFFF instead of #0F172A (wrong solid color)
  - Text unreadable due to poor contrast
  - Effect color not matching the intended accent color
```

**Animation and Timing**:
```
What to check: Does the motion look right?
How to check:
  - Review the frame sequence from start to key moment
  - Check: does the element start where expected?
  - Check: does the element end where expected?
  - Check: does the motion path look smooth? (no sudden jumps)
  - Check: does the timing feel right? (too fast, too slow, or just right)
Typical failures:
  - Element jumps to final position instead of animating
  - Animation starts from wrong position
  - Easing looks wrong (linear when it should ease out, or vice versa)
  - Animation completes too early or too late
```

**Effect Intensity**:
```
What to check: Is the effect visible but appropriate?
How to check:
  - Glow: does it illuminate without overwhelming the underlying content?
  - Shadow: does it separate the element from background without looking heavy?
  - Blur: does it create appropriate softness or depth?
  - Stroke: is it visible without dominating?
Typical failures:
  - Glow so bright it washes out the text (opacity > 80 or radius > 40)
  - Shadow so heavy it looks like a separate object
  - Blur so strong it becomes a blob
  - Stroke so thick it obscures the shape interior
```

**Text and Typography**:
```
What to check: Is the text readable and correctly placed?
How to check:
  - Is the text legible at this resolution?
  - Is the text in the right position?
  - Does the tracking/leading look natural?
  - Is alignment correct (left/center/right)?
Typical failures:
  - Text positioned wrong (off-center when it should be centered)
  - Text too small or too crowded
  - Wrong text content (agent typo in the JSON string)
```

**Layering and Occlusion**:
```
What to check: Is the correct element on top?
How to check:
  - Identify which element is visually foremost
  - Check if foreground/background relationship is correct
  - Verify that no important element is hidden behind another
Typical failures:
  - Title hidden behind a background element (wrong layer order)
  - Logo occluded by text
  - Adjustment layer affecting wrong layers
```

### 3.3 Sequence Analysis (for animation verification)

When checking animation across time:

```
Step 1: Extract frames at key moments
  - Frame A: t = startTime (initial state)
  - Frame B: t = first_keyframe_time (first motion point)
  - Frame C: t = mid_animation (between keys)
  - Frame D: t = last_keyframe_time (final state)
  - Frame E: t = endTime (resting state, hold complete)

Step 2: Compare sequentially
  - Does A → B show the expected start-to-first-key motion?
  - Does B → C show smooth interpolation, not a jump?
  - Does C → D show the expected end motion?
  - Does D → E show proper hold (no drift)?

Step 3: Check for specific animation issues
  - Jump: sudden change between frames instead of smooth motion
  - Overshoot: element goes past intended position then returns
  - Stutter: element pauses or jitters during motion
  - Early/late: animation starts or ends at wrong time
```

---

## Phase 4: Self-Correction Protocol

After analysis, the agent acts on findings.

### 4.1 Map Visual Observation to JSON Fix

```
OBSERVATION                          LIKELY JSON CAUSE                    FIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Element at top-left, not centered    position: [0, 0]                    → position: [960, 540]
Element too small                    scale: [30, 30]                     → scale: [60, 60]  
Element invisible                   enabled: false, OR opacity: 0        → enabled: true / opacity: 100
Glow overwhelming                   glow opacity: 90                     → reduce to 40-60
Glow barely visible                 glow opacity: 15                     → increase to 30-50
Animation jumps (no smooth motion)  keyframe easing: "linear"            → add "easeOutCubic"
Animation too fast                  keyframe time gap too small          → increase time between keys
Animation too slow                  keyframe time gap too large          → decrease time between keys
Animation not starting              keyframe time > startTime            → align first keyframe to startTime
Element cut off by mask            mask path coords outside element      → adjust mask path to cover area
Track matte reveals wrong area      matte layer not immediately above    → reorder layers
Blend mode looks wrong              wrong blendMode for the interaction  → try different mode or reduce opacity
Text unreadable (too small)          fontSize: 24 on 1080p               → increase to 48-72
Text unreadable (bad contrast)       light text on light background       → adjust text or background color
Shape in wrong position             shapeContents[].position confused     → verify layer space vs composition space
```

### 4.2 Fix Priority

When multiple issues are found, fix in this order:

```
1. CRITICAL (blocks understanding):
   - Missing elements (enabled, timing, reference breaks)
   - Completely wrong position (off-canvas)
   - Wrong text content
   
2. IMPORTANT (affects quality):
   - Effect intensity adjustments
   - Animation timing/easing corrections
   - Color/contrast corrections
   - Scale adjustments
   
3. OPTIONAL ( polish):
   - Layer ordering refinements
   - Subtle timing adjustments
   - Minor effect fine-tuning
```

### 4.3 One Fix Per Iteration

**Rule**: Change one thing at a time. Verify each fix independently before moving to the next.

```
❌ Change position, scale, AND opacity in one render → cannot identify which fix worked

✅ Fix position → render → verify → 
   Fix scale → render → verify →
   Fix opacity → render → verify
```

This discipline prevents "improved but don't know why" and "made it worse but don't know which change caused it."

### 4.4 Iteration Limits

```
Max iterations: 3 per critical issue
Max total iterations: 10 per project

If not resolved after max iterations:
  → Log what was tried and the specific remaining issue
  → Request human review with:
      - Original intent
      - All attempted fixes
      - Last rendered frame
      - Specific remaining problem description
```

---

## Phase 5: Verification-by-Category Protocol

### 5.1 Quick Verification (Fast Pass)

Use when time is limited or during iterative development:

```
1. Extract ONE frame at the most critical moment (e.g., t = 0 for intro, t = peak for animation)
2. Check only CRITICAL criteria from the checklist
3. Ask: "Is the element in the right place? Is the effect visible? Is the text readable?"
4. If all critical pass → proceed. If any critical fails → fix and re-verify.
```

### 5.2 Full Verification (Before Delivery)

Use before final render or delivery:

```
1. Verify all criteria in the checklist (not just critical)
2. Extract frames at:
   - Start state
   - Each keyframe moment
   - End state
3. Run animation sequence check (A→B→C→D→E as described in 3.3)
4. Render at Tier 2 (medium quality) and verify
5. Final render at Tier 3 (full quality)
6. Final frame check at full resolution
```

### 5.3 Differential Verification (After Targeted Changes)

Use when you made a specific change and want to confirm only that change:

```
1. Identify exactly what changed (e.g., "increased glow opacity from 30 to 50")
2. Extract frames at the moment the changed effect is most visible
3. Verify ONLY the changed aspect (not re-checking unrelated elements)
4. Confirm the change had the intended effect
5. Check that no unintended side effects occurred
```

---

## Phase 6: Handling Ambiguous Cases

Some visual assessments are not binary pass/fail. Handle them explicitly:

### 6.1 Subjective Quality

```
SITUATION: "The glow intensity is a matter of taste — is 45 better than 35?"

PROTOCOL:
1. Render at 35, render at 45, extract both frames
2. Present to self: "Both are within acceptable range. 
   Which matches the project's mood better?"
3. If still ambiguous: default to SUBTLE (lower intensity)
   — overdone effects are harder to fix than underdone ones
4. Document the choice: "Glow opacity: 40 (subtle, safe default)"
```

### 6.2 Context-Dependent Correctness

```
SITUATION: "Position [1700, 920] for logo — is this right?"

PROTOCOL:
1. Recalculate from intent: "Logo should be in bottom-right with 5% margin"
2. For 1920×1080: right margin = 1920 * 0.05 = 96px
   → x_max = 1920 - 96 = 1824
   → y_max = 1080 - 96 = 984
3. If [1700, 920] is within [960-1824, 540-984] → PASS
4. If ambiguous: "bottom-right" defaults to upper-left of bottom-right quadrant 
   ([960, 540] to [1920, 1080]) → confirm center of that region is [1440, 810]
```

### 6.3 Trade-offs

```
SITUATION: "Increasing glow opacity makes text more readable, but increases glare"

PROTOCOL:
1. Identify the PRIMARY goal: "Text must be readable" > "minimal glare"
2. Set glow to readable threshold first
3. Check if glare is within acceptable range
4. If glare is unacceptable: try alternative (stroke outline for readability instead of glow)
5. Document the trade-off decision
```

---

## Putting It Together: Complete Verification Loop

```
┌─────────────────────────────────────────────────────────┐
│  1. DEFINE INTENT                                       │
│     Decompose into specific, verifiable criteria         │
│     Store as verification checklist                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. AUTHOR JSON                                          │
│     Generate .outocut based on intent + checklist        │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. RENDER (Tier 1 - Fast)                              │
│     outocut render --preset ultrafast --crf 40          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  4. EXTRACT FRAME                                       │
│     ffmpeg at strategic moments                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  5. ANALYZE (Multimodal LLM)                            │
│     Use structured prompt from §3.1                     │
│     Check against verification checklist                 │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │                       │
           PASS                    FAIL
              │                       │
              ▼                       ▼
┌──────────────────────┐  ┌─────────────────────────────────┐
│  6a. FINALIZE or     │  │  6b. IDENTIFY PROBLEM           │
│      Advance Tier     │  │     Map observation → JSON fix  │
│                      │  │     Fix ONE thing per iteration  │
│                      │  └─────────────┬───────────────────┘
│                      │                │
│                      │                ▼
│                      │  ┌─────────────────────────────────┐
│                      │  │  7. FIX JSON                   │
│                      │  │     Apply targeted fix           │
│                      │  └─────────────┬───────────────────┘
│                      │                │
│                      │                ▼
│                      │  [Loop back to Step 3]              │
│                      │  (max 10 iterations)               │
└──────────────────────┘  └─────────────────────────────────┘
```

---

## Quick Reference

> ⚠️ **CRITICAL: AI AGENT COORDINATE WARNING**
>
> **OutOcut uses TOP-LEFT origin (0, 0)**
> - Center of 1920×1080 = [960, 540], NOT [0, 0]
> - Bottom-left = [0, height], NOT [0, 0]
> - **When checking positions, ask yourself: "Is this position relative to top-left?"**

### Frame Extraction One-Liner

```bash
# Render and extract frame at specific time (t=1.5s, 1920×1080)
outocut render project.outocut -o /tmp/check.mp4 --time 1.5 --duration 0.033 --preset ultrafast --crf 38 && \
ffmpeg -i /tmp/check.mp4 -vf "fps=1" -frames:v 1 /tmp/check_frame.png
```

### Sequence Extraction One-Liner

```bash
# Extract all frames at 2fps for animation review
mkdir -p /tmp/seq && \
outocut render project.outocut -o /tmp/seq.mp4 --preset ultrafast --crf 38 && \
ffmpeg -i /tmp/seq.mp4 -vf "fps=2" /tmp/seq/frame_%03d.png
```

### Analysis Summary Template

After each frame analysis, update:

```
## Verification Log

[time=X.Xs] Frame: check_frame.png
  - [criterion 1]: PASS/FAIL (detail)
  - [criterion 2]: PASS/FAIL (detail)
  ...
  Overall: PASS / PARTIAL / FAIL
  
  If FAIL:
    - Issue: [specific problem]
    - Fix: [specific JSON change]
    - Next action: [render → re-extract]
```

### Maximum Iteration Budget

| Phase | Max Iterations | Purpose |
|-------|:--------------:|---------|
| Tier 1 (fast) | 5 | Layout, position, structure |
| Tier 2 (medium) | 3 | Effect intensity, color, timing |
| Tier 3 (full) | 2 | Final polish |
| **Total** | **10** | Per project |

### Severity Classification

| Severity | What it means | Action |
|----------|--------------|--------|
| **Critical** | Intent fundamentally broken | Fix immediately, do not proceed |
| **Important** | Quality degraded but recognizable | Fix before final, warn if skipped |
| **Minor** | Slight deviation from ideal | Fix if easy, document if not |
| **Nice-to-have** | Enhancement opportunity | Optional, deferred |

---

## Common Self-Verification Scenarios

### Scenario 1: Intro Animation

```
Intent: Title fades in from center over 1s, settles at [960, 540]

Verification:
  1. Extract frame at t=0.0 → should show empty/dark background
  2. Extract frame at t=0.5 → title partially visible, centered
  3. Extract frame at t=1.0 → title fully visible, centered, no longer fading
  4. Verify: title position matches [960, 540], glow intensity appropriate
```

### Scenario 2: Layer Composition

```
Intent: Dark background → colored panel → logo on panel

Verification:
  1. Extract frame → identify three layers visually
  2. Check: background is dark (#0F172A range), panel is visible, logo on top of panel
  3. Check: no element hidden or occluded unexpectedly
  4. Check: panel and logo have correct z-order (logo in front of panel)
```

### Scenario 3: Effect Stack

```
Intent: Text with subtle glow and drop shadow

Verification:
  1. Extract frame at peak visibility
  2. Check: glow visible as soft halo, not overwhelming (text still readable)
  3. Check: shadow separates text from background (visible but not heavy)
  4. If glow too strong: reduce opacity or radius
  5. If shadow too heavy: reduce opacity or distance
```

---

## See Also

- [best-practices.md](best-practices.md) — Project organization and workflow patterns
- [effects.md](effects.md) — Effect parameter reference and stacking guidance
- [transforms.md](transforms.md) — Transform property reference
- [coordinate-system.md](coordinate-system.md) — Position and coordinate reference
