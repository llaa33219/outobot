---
name: outocut
description: OutOcut video editor - CLI commands, JSON project format (.outocut), animation system, effects, blend modes, and AI visual self-verification workflow
metadata:
  tags: outocut, video, motion-graphics, animation, cli, video-editing, composition
---

# OutOcut

## ⚠️ MANDATORY: Read Rules First

**CRITICAL - READ THESE FILES BEFORE WORKING:**

You MUST read the following rule files before performing any OutOcut task:

```
skill/rules/file-format.md      # JSON format specification (REQUIRED)
skill/rules/cli-commands.md    # CLI reference (REQUIRED)
skill/rules/coordinate-system.md # Position/coordinate system (REQUIRED)
skill/rules/layer-types.md     # Layer types (REQUIRED)
skill/rules/transforms.md      # Transform properties (REQUIRED)
skill/rules/effects.md         # Effect reference (REQUIRED)
skill/rules/animation-system.md # Keyframes & easing (REQUIRED)
```

**Do NOT skip reading these files. The Quick Reference below is NOT sufficient.**

## When to Use

This skill activates when working with:
- OutOcut CLI commands (render, preview, validate, watch, export-json)
- Creating or editing .outocut project files (JSON format)
- Video composition with layers (video, audio, text, shape, solid, image)
- Animation with keyframes and easing functions
- Applying effects (glow, blur, color correction, etc.)
- Blend modes and track matte compositing
- AI agents rendering and verifying video output visually

## Quick Reference (INSUFFICIENT - READ RULES ABOVE)

### CLI Commands
| Command | Description |
|---------|-------------|
| `outocut render <file> -o <output>` | Render project to video |
| `outocut preview <file> --time <seconds>` | Preview at specific time |
| `outocut validate <file>` | Validate project structure |
| `outocut watch <file>` | Watch mode for auto-reload |
| `outocut export-json <file>` | Export formatted JSON |

### Coordinate System
- Origin: Top-left (0,0)
- X increases rightward, Y increases downward
- Default canvas: 1920×1080

## Required Rule Files

You MUST read these files - they contain the detailed specifications:

| File | Purpose | When to Read |
|------|---------|--------------|
| [rules/file-format.md](rules/file-format.md) | Complete .outocut JSON format specification | ALWAYS - before creating/editing projects |
| [rules/cli-commands.md](rules/cli-commands.md) | Full CLI reference with all options | When using CLI commands |
| [rules/ai-agent-verify.md](rules/ai-agent-verify.md) | AI visual self-verification protocol | When rendering and verifying output |
| [rules/best-practices.md](rules/best-practices.md) | Production best practices | Before production work |
| [rules/coordinate-system.md](rules/coordinate-system.md) | Position and coordinate reference | When positioning elements |
| [rules/transforms.md](rules/transforms.md) | Transform properties | When animating transforms |
| [rules/effects.md](rules/effects.md) | Effect reference | When adding effects |
| [rules/layer-types.md](rules/layer-types.md) | Layer type reference | When using layers |
| [rules/blend-modes.md](rules/blend-modes.md) | Blend mode reference | When using blend modes |
| [rules/shapes-masks.md](rules/shapes-masks.md) | Shape and mask data | When creating shapes/masks |
| [rules/track-matte.md](rules/track-matte.md) | Track matte reference | When using track matte |
| [rules/animation-system.md](rules/animation-system.md) | Animation system | When creating animations |
| [rules/examples.md](rules/examples.md) | Usage examples | For reference patterns |
| [rules/review-guide.md](rules/review-guide.md) | Production review & QA checklist | Before final render |

## Core Concepts

### Everything is a Layer
Video, audio, text, shapes, images - all are layers with transform, opacity, and effects.

### Everything is Keyframable
Time, value, easing - all can be animated with keyframe interpolation.

### Deterministic Render
Same JSON = 100% identical output. No randomness during render.

### Expression Support (planned)
JavaScript-like expressions: `position.x = time * 50`

## Architecture
CLI (clap) → Parser → Models → Composition → Animation → Render → FFmpeg encode

---

**REMINDER: Read the required rule files listed above before starting any OutOcut task. The Quick Reference section is NOT sufficient for accurate work.**
