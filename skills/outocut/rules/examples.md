# Usage Examples

Practical examples for common tasks — from quick inline snippets to full production-ready projects.

## Production Examples

The `examples/` directory contains 10 complete, render-ready `.outocut` projects demonstrating real-world motion graphics use cases. All files pass `outocut validate`.

| # | File | Description | Key Features |
|---|---|---|---|
| 01 | `examples/01-kinetic-typography.outocut` | Cinematic hero title intro | Scale bounce, glow, vignette, floating particles |
| 02 | `examples/02-lower-thirds.outocut` | Broadcast lower thirds | Slide-in panels, staggered timing, accent stripe |
| 03 | `examples/03-logo-reveal.outocut` | Geometric logo reveal | Track matte alpha reveal, light sweep, glow |
| 04 | `examples/04-gradient-background.outocut` | Animated motion background | Floating shapes, gradient orbs, light rays |
| 05 | `examples/05-social-card.outocut` | Social media post card | Avatar, stat bars, CTA button, staggered entrances |
| 06 | `examples/06-countdown-timer.outocut` | Dramatic countdown timer | "3, 2, 1, GO!", flash effects, glow pulses |
| 07 | `examples/07-glitch-text.outocut` | Digital glitch text | RGB split, scan lines, chromatic aberration |
| 08 | `examples/08-product-showcase.outocut` | Sleek product showcase | Trim path, feature bullets, CTA button, glow |
| 09 | `examples/09-particle-orbit.outocut` | Abstract particle orbit | Parent/child rotation, pulsing orb, orbiting dots |
| 10 | `examples/10-end-credits.outocut` | Elegant end credits | Sequential fade-ins, divider lines, gold accents |

**Rendering a production example:**
```bash
outocut render examples/01-kinetic-typography.outocut -o output.mp4
outocut preview examples/01-kinetic-typography.outocut --time 1.5
```

---

## Quick Reference Snippets

### Project Skeleton

```json
{
  "version": "1.0",
  "metadata": {
    "name": "my_project",
    "created": "2026-03-19T00:00:00Z",
    "author": "you",
    "description": "My project",
    "tags": []
  },
  "settings": {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration": 10.0,
    "backgroundColor": "#000000",
    "pixelAspect": 1.0,
    "sampleRate": 48000,
    "audioChannels": 2
  },
  "assets": [],
  "compositions": {
    "main": {
      "id": "comp_main",
      "duration": 10.0,
      "width": 1920,
      "height": 1080,
      "layers": []
    }
  },
  "mainCompositionId": "main",
  "exportPresets": []
}
```

### Layer Patterns

**Solid background:**
```json
{
  "id": "bg",
  "type": "solid",
  "name": "Background",
  "enabled": true,
  "startTime": 0,
  "duration": 10.0,
  "opacity": { "value": 100, "keyframes": null },
  "transform": {
    "anchor": { "value": [960, 540], "keyframes": null },
    "position": { "value": [960, 540], "keyframes": null },
    "scale": { "value": [100, 100], "keyframes": null },
    "rotation": { "value": 0, "keyframes": null },
    "skew": { "value": [0, 0], "keyframes": null },
    "skewAxis": { "value": 0, "keyframes": null }
  },
  "content": { "color": "#FF0000" }
}
```

**Text layer:**
```json
{
  "id": "title",
  "type": "text",
  "name": "Title",
  "enabled": true,
  "startTime": 0,
  "duration": 5.0,
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
    "text": "HELLO WORLD",
    "fontSize": 120,
    "color": "#FFFFFF",
    "alignment": "center"
  }
}
```

**Shape layer (rounded rectangle):**
```json
{
  "id": "panel",
  "type": "shape",
  "name": "Panel",
  "enabled": true,
  "startTime": 0,
  "duration": 10.0,
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
      "size": [800, 400],
      "position": [0, 0],
      "roundness": 32,
      "color": "#1a1a2e",
      "width": null,
      "copies": null,
      "offset": null
    },
    {
      "type": "stroke",
      "name": "Border",
      "size": null,
      "position": null,
      "roundness": null,
      "color": "#00D4FF",
      "width": 4,
      "copies": null,
      "offset": null
    }
  ]
}
```

### Animation Patterns

**Fade in / fade out:**
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

**Slide in from left:**
```json
"transform": {
  "position": {
    "value": [960, 540],
    "keyframes": [
      { "time": 0.0, "value": [-400, 540], "easing": "easeOutCubic" },
      { "time": 0.8, "value": [960, 540] }
    ]
  }
}
```

**Scale bounce entrance:**
```json
"transform": {
  "scale": {
    "value": [100, 100],
    "keyframes": [
      { "time": 0.0, "value": [0, 0], "easing": "easeOutBack" },
      { "time": 0.6, "value": [110, 110], "easing": "easeInOutCubic" },
      { "time": 0.9, "value": [100, 100] }
    ]
  }
}
```

### Effects Patterns

**Glow:**
```json
"effects": [
  {
    "id": "glow_1",
    "type": "glow",
    "enabled": true,
    "params": { "radius": 20, "color": "#00D4FF", "opacity": 60, "threshold": 0 },
    "keyframes": null
  }
]
```

**Drop shadow:**
```json
"effects": [
  {
    "id": "shadow_1",
    "type": "dropShadow",
    "enabled": true,
    "params": { "distance": 8, "angle": 45, "blur": 16, "color": "#000000", "opacity": 50 },
    "keyframes": null
  }
]
```

**Vignette (via adjustment layer):**
```json
{
  "id": "grade",
  "type": "adjustment",
  "name": "Global Grade",
  "enabled": true,
  "startTime": 0,
  "duration": 10.0,
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
  "effects": [
    { "id": "vig", "type": "vignette", "enabled": true, "params": { "amount": 35, "size": 60, "roundness": 25, "feather": 70, "color": "#000000" }, "keyframes": null }
  ]
}
```

### Scripting Examples

**Generate project with Python:**
```python
import json

def create_project(name, duration, width=1920, height=1080, fps=30):
    return {
        "version": "1.0",
        "metadata": {
            "name": name,
            "created": "2026-03-19T00:00:00Z",
            "author": "script",
            "description": "Generated project",
            "tags": []
        },
        "settings": {
            "width": width,
            "height": height,
            "fps": fps,
            "duration": duration,
            "backgroundColor": "#000000",
            "pixelAspect": 1.0,
            "sampleRate": 48000,
            "audioChannels": 2
        },
        "assets": [],
        "compositions": {
            "main": {
                "id": "comp_main",
                "duration": duration,
                "width": width,
                "height": height,
                "layers": []
            }
        },
        "mainCompositionId": "main",
        "exportPresets": []
    }

project = create_project("my_project", 30.0)
with open("project.outocut", "w") as f:
    json.dump(project, f, indent=2)
```

**Batch render:**
```bash
#!/bin/bash
mkdir -p output
for project in examples/*.outocut; do
    name=$(basename "$project" .outocut)
    outocut render "$project" -o "output/${name}.mp4"
done
```