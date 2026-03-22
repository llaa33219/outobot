# OutOcut CLI Commands

Comprehensive command reference for `outocut`.

- Author: BLOUplanet
- License: Apache 2.0
- CLI version covered: `0.1.0`

## Command Index

| Command | Purpose |
|---|---|
| `render` | Render a `.outocut` project into a video file via FFmpeg |
| `preview` | Print runtime layer state at a specific timestamp |
| `validate` | Validate project parsing and key structural constraints |
| `export-json` | Export normalized JSON (comments removed) |
| `watch` | Watch project file changes and auto-run validation |

## Global CLI Usage

```bash
outocut <COMMAND> [OPTIONS]
```

### Global Flags

| Flag | Description |
|---|---|
| `-h`, `--help` | Print help for root command or subcommand |
| `-V`, `--version` | Print CLI version |

### Global Examples

```bash
# Root help
outocut --help

# Version
outocut --version

# Command-specific help
outocut render --help
```

Expected output (`outocut --version`):

```text
outocut 0.1.0
```

## 1) `render`

Render a project to a video file.

### Syntax

```bash
outocut render <PROJECT> -o <OUTPUT> [--gpu] [--preset PRESET] [--crf CRF]
```

### Arguments and Flags

| Name | Required | Type | Description |
|---|---|---|---|
| `<PROJECT>` | Yes | path | Path to `.outocut` project file |
| `-o`, `--output <OUTPUT>` | Yes | path | Output video file path |
| `--gpu` | No | flag | Use NVIDIA NVENC encoder (`h264_nvenc`) instead of `libx264` |
| `--preset <PRESET>` | No | string | Encoder preset. Recommended: `ultrafast`, `fast`, `medium`, `slow`, `veryslow` |
| `--crf <CRF>` | No | integer | Constant Rate Factor. Lower = better quality, larger file |

### Detailed Behavior

- Parses project JSON (supports `//` and `/* ... */` comments in `.outocut`).
- Renders frames to an internal cache directory: `.outocut.cache` next to the project file.
- Invokes FFmpeg to encode `%06d.png` frames into final output.
- Defaults:
  - codec: `libx264` (or `h264_nvenc` when `--gpu` is set)
  - preset: `medium`
  - CRF: `23`

### Quality and Performance Notes

- CRF scale is generally `0-51` in x264 semantics:
  - `0`: lossless (very large files)
  - `23`: default balance
  - `51`: worst quality, smallest files
- `--preset veryslow` can significantly increase render time while reducing bitrate.
- GPU mode requires NVIDIA GPU + working NVENC support in your FFmpeg build.

### Examples

```bash
# Basic render
outocut render project.outocut -o output.mp4

# Better quality with slower encode
outocut render project.outocut -o output.mp4 --preset slow --crf 18

# GPU render
outocut render project.outocut -o output.mp4 --gpu
```

Expected output (success):

```text
INFO outocut: Rendering project: project.outocut -> output.mp4
```

Expected output (FFmpeg missing):

```text
INFO outocut: Rendering project: project.outocut -> output.mp4
Error: No such file or directory (os error 2)
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Render completed successfully |
| `1` | Runtime error (parse failure, FFmpeg failure, IO failure, etc.) |
| `2` | CLI usage error (missing required args/flags, invalid argument type) |

### Common Errors and Solutions

| Error | Cause | Solution |
|---|---|---|
| `required arguments were not provided: --output <OUTPUT>` | Missing `-o/--output` | Provide `-o output.mp4` |
| `invalid value 'abc' for '--crf <CRF>'` | Non-numeric CRF | Use numeric value, e.g. `--crf 18` |
| `FFmpeg failed: ...` | FFmpeg runtime/codec error | Verify FFmpeg install and codec support (`ffmpeg -encoders`) |
| `No such file or directory (os error 2)` | Project file or FFmpeg not found | Check file path and ensure `ffmpeg` is on `PATH` |
| NVENC-related FFmpeg error | No NVIDIA/NVENC support | Remove `--gpu` or install NVENC-capable FFmpeg |

## 2) `preview`

Print layer state snapshot at a specific timestamp.

### Syntax

```bash
outocut preview <PROJECT> --time <TIME> [--duration <DURATION>]
```

### Arguments and Flags

| Name | Required | Type | Description |
|---|---|---|---|
| `<PROJECT>` | Yes | path | Path to `.outocut` project file |
| `--time <TIME>` | Yes | float | Start time in seconds |
| `--duration <DURATION>` | No | float | Duration window (accepted but currently informational) |

### Detailed Behavior

- Parses project and evaluates active layers at `--time`.
- Prints project metadata and active layer transform/opacity values.
- Does not render images or open a preview window.

### Cautions

- This is a text/debug preview only (no visual output).
- Use it to inspect timing, activation windows, transforms, and opacity at a timestamp.

### Examples

```bash
# Snapshot at 2.5 seconds
outocut preview project.outocut --time 2.5

# With optional duration argument
outocut preview project.outocut --time 5 --duration 1.5
```

Expected output:

```text
INFO outocut: Previewing project: project.outocut at 2.5s
Preview at time: 2.5s
Project: test (1920x1080 @ 30fps)
Active layers: 1
  - Background (Solid) at (960.0, 540.0) scale 100.0% opacity 100%
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Preview data printed successfully |
| `1` | Runtime error (project parsing/loading failure) |
| `2` | CLI usage/type error (missing `--time`, invalid float, etc.) |

### Common Errors and Solutions

| Error | Cause | Solution |
|---|---|---|
| `required arguments were not provided: --time <TIME>` | Missing time flag | Add `--time`, e.g. `--time 3.0` |
| `invalid value 'nope' for '--time <TIME>'` | Non-float value | Use numeric seconds (`2`, `2.5`) |
| `No such file or directory (os error 2)` | Missing project file | Verify path to `.outocut` file |

## 3) `validate`

Validate project structure and required constraints.

### Syntax

```bash
outocut validate <PROJECT>
```

### Arguments

| Name | Required | Type | Description |
|---|---|---|---|
| `<PROJECT>` | Yes | path | Path to `.outocut` project file |

### Validation Coverage

#### Specification-level checks you should expect in validation workflows

- JSON syntax validity
- required fields presence
- valid enum values
- asset references consistency
- composition references consistency

#### Current CLI implementation checks (`0.1.0`)

- Parses JSON after removing comments.
- Ensures `settings.width > 0` and `settings.height > 0`.
- Ensures `settings.fps > 0`.
- Ensures `settings.duration > 0`.
- Ensures `mainCompositionId` exists in `compositions`.
- Ensures main composition duration equals project duration.

### Cautions

- Does not currently verify that asset files exist on disk.
- Does not currently detect circular composition references.

### Examples

```bash
# Validate project
outocut validate project.outocut

# CI usage example
outocut validate project.outocut && echo "Validation passed"
```

Expected output (success):

```text
INFO outocut: Validating project: project.outocut
✓ Project is valid
```

Expected output (failure):

```text
INFO outocut: Validating project: broken.outocut
Error: Invalid fps: must be > 0
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Project passes validation |
| `1` | Validation/runtime error |
| `2` | CLI usage/type error |

### Common Errors and Solutions

| Error | Cause | Solution |
|---|---|---|
| `Main composition '...' not found` | `mainCompositionId` missing in `compositions` | Add referenced composition or fix ID |
| `Main composition duration must match project duration` | Duration mismatch | Align both durations |
| `Invalid dimensions...` | Width/height is `0` | Set positive dimensions |
| `No such file or directory (os error 2)` | Project path invalid | Correct file path |

## 4) `export-json`

Export `.outocut` content as clean JSON (comments removed).

### Syntax

```bash
outocut export-json <PROJECT> [--pretty]
```

### Arguments and Flags

| Name | Required | Type | Description |
|---|---|---|---|
| `<PROJECT>` | Yes | path | Path to `.outocut` project file |
| `-p`, `--pretty` | No | flag | Pretty-print with indentation |

### Detailed Behavior

- Reads the project file.
- Strips `//` and `/* ... */` comments while preserving string content.
- Parses as project model and re-serializes to JSON.
- Prints JSON to stdout.

### Use Cases

- Convert commented `.outocut` files into strict JSON.
- Debug/inspect final parsed structure.
- Feed clean JSON to external tooling.

### Examples

```bash
# Minified JSON
outocut export-json project.outocut > project.json

# Pretty JSON
outocut export-json project.outocut --pretty > project.pretty.json
```

Expected output (pretty mode):

```text
INFO outocut: Exporting JSON: project.outocut
{
  "version": "1.0",
  "metadata": { ... },
  ...
}
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | JSON exported successfully |
| `1` | Runtime error (file missing, parse/serialization failure) |
| `2` | CLI usage/type error |

### Common Errors and Solutions

| Error | Cause | Solution |
|---|---|---|
| `No such file or directory (os error 2)` | Project file missing | Verify input path |
| JSON parse error | Invalid JSON or malformed comments | Fix `.outocut` syntax, then retry |

## 5) `watch`

Watch project file and re-run validation on changes.

### Syntax

```bash
outocut watch <PROJECT>
```

### Arguments

| Name | Required | Type | Description |
|---|---|---|---|
| `<PROJECT>` | Yes | path | Path to `.outocut` project file |

### Behavior

- Subscribes to file change notifications for the target project file.
- On modify event:
  - prints change notice
  - runs `validate`
  - prints validation result
- Runs continuously until interrupted.

### Cautions

- Does not auto-render.
- Only validation is triggered on change (no build or export).
- Stop with `Ctrl+C`.

### Example

```bash
outocut watch project.outocut
```

Expected output:

```text
INFO outocut: Watching project: project.outocut
Watching project.outocut for changes (Ctrl+C to stop)

✓ Project changed, reloading...
✓ Project is valid
```

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | Rare normal termination (watch loop ended without error) |
| `1` | Startup/watch runtime error (invalid path, watcher error) |
| `130` | User interrupted with `Ctrl+C` (typical shell-visible code) |
| `2` | CLI usage error |

### Common Errors and Solutions

| Error | Cause | Solution |
|---|---|---|
| `No such file or directory ...` at startup | File does not exist | Create file or fix path |
| `Watch error: ...` | OS watcher backend issue | Retry, check permissions, or move file to local filesystem |

## Unified Exit Code Reference

| Code | Category | Typical Triggers |
|---|---|---|
| `0` | Success | Command completed normally |
| `1` | Runtime/validation/render error | File IO errors, parse errors, FFmpeg failures, watcher startup errors |
| `2` | CLI argument/usage error | Missing required args, invalid value types, unknown options |
| `130` | Interrupted | `Ctrl+C` in long-running commands like `watch` |

## Environment Variables

### Supported

| Variable | Scope | Notes |
|---|---|---|
| `RUST_LOG` | Logging filter (`tracing`) | Logging is initialized with a default `INFO` directive; command `INFO` logs are still emitted in current `0.1.0` behavior |

Example:

```bash
RUST_LOG=debug outocut validate project.outocut
```

### Not currently supported as CLI config

- No documented `OUTOCUT_*` environment variable settings for command options.

## Configuration File Support

OutOcut CLI (`0.1.0`) does not load a dedicated CLI config file (no `.outocutrc`, no `outocut.toml` for command defaults).

All options are currently provided via command arguments/flags.

## Shell Completion

OutOcut CLI (`0.1.0`) does not currently expose a completion-generation command.

### Current status

- Built-in shell completion install flow: not available.
- Manual fallback: use `outocut --help` and per-command `--help`.

### If you need completion now

- Add a completion subcommand in source using Clap completion generation and distribute generated scripts for Bash/Zsh/Fish.
