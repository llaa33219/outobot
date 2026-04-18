"""
OutObot Tools
Default tools available to all agents
"""

import base64
import json
import os
import tempfile
from pathlib import Path
from typing import Annotated
from agentouto import Tool, ToolResult, Attachment

SESSIONS_DIR = Path.home() / ".outobot" / "sessions"

_memory_manager = None


def set_memory_manager(manager):
    global _memory_manager
    _memory_manager = manager


@Tool
def recall_memory(
    query: Annotated[
        str, "Topic or question to recall. Empty string to check memory status."
    ] = "",
) -> str:
    """Recall memories. Pass a query for semantic search, or empty string to check status."""
    if not query:
        if _memory_manager is not None and _memory_manager.is_available:
            status = "🧠 outowiki is ACTIVE"
        else:
            status = "⚠️ outowiki not available (fallback to session search)"

        if SESSIONS_DIR.exists():
            count = len(list(SESSIONS_DIR.glob("*.json")))
            return f"{status}\n📁 {count} sessions stored"
        return status

    if _memory_manager is not None and _memory_manager.is_available:
        try:
            results = _memory_manager._outowiki.search(query, max_results=5, return_mode="full")
            if results:
                content_parts = []
                for r in results:
                    content_parts.append(r.content if hasattr(r, "content") else str(r))
                context = "\n\n---\n\n".join(content_parts)
                if context:
                    return context
        except Exception:
            pass

    if not SESSIONS_DIR.exists():
        return "No memories found."

    sessions = list(SESSIONS_DIR.glob("*.json"))
    if not sessions:
        return "No memories found."

    query_lower = query.lower()
    results = []

    for session_file in sessions:
        with open(session_file) as f:
            data = json.load(f)

        session_id = data.get("session_id", session_file.stem)
        for msg in data.get("messages", []):
            content = msg.get("content", "").lower()
            if query_lower in content:
                sender = msg.get("sender", "unknown")
                results.append(
                    f"[{session_id}] {sender}: {msg.get('content', '')[:200]}..."
                )

    if not results:
        return f"No memories found for '{query}'."

    result = f"Found {len(results)} matches:\n\n"
    for r in results[:10]:
        result += f"{r}\n\n"
    if len(results) > 10:
        result += f"... and {len(results) - 10} more"

    return result


@Tool
def run_bash(
    command: Annotated[str, "Command to execute"],
    timeout: Annotated[int, "Timeout in seconds"] = 60,
) -> str:
    """Execute a bash command and return output."""
    import subprocess

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=timeout
    )
    return result.stdout + result.stderr


@Tool
def view_media(
    path: Annotated[str, "File path to the media file (image, video, or audio)"],
) -> ToolResult:
    """View and analyze media files (images, videos, audio). Returns metadata and basic analysis.

    Returns a ToolResult with:
    - content: Text metadata (dimensions, format, codec, duration, etc.)
    - attachments: Actual media file (image, video frame, or audio) for visual/audio analysis
    """
    import subprocess
    from PIL import Image

    if not os.path.exists(path):
        return ToolResult(content=f"Error: File not found: {path}")

    file_path = Path(path)
    if not file_path.exists():
        return ToolResult(content=f"Error: File does not exist: {path}")

    file_ext = file_path.suffix.lower()
    file_size = os.path.getsize(path)
    file_size_str = (
        f"{file_size / 1024:.1f} KB"
        if file_size < 1024 * 1024
        else f"{file_size / (1024 * 1024):.1f} MB"
    )

    content = f"File: {file_path.name}\n"
    content += f"Path: {path}\n"
    content += f"Size: {file_size_str}\n"
    content += f"Type: {file_ext[1:] if file_ext else 'unknown'}\n"

    attachments = []

    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico"]
    video_exts = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"]
    audio_exts = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"]

    # MIME type mapping
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".ico": "image/x-icon",
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".flv": "video/x-flv",
        ".wmv": "video/x-ms-wmv",
        ".m4v": "video/x-m4v",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".wma": "audio/x-ms-wma",
        ".opus": "audio/opus",
    }

    if file_ext in image_exts:
        try:
            with Image.open(path) as img:
                content += f"Dimensions: {img.width} x {img.height} pixels\n"
                content += f"Format: {img.format}\n"
                content += f"Mode: {img.mode}\n"
                if hasattr(img, "info") and "dpi" in img.info:
                    content += f"DPI: {img.info['dpi']}\n"

            # Attach the actual image for visual analysis
            with open(path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            mime_type = mime_types.get(file_ext, "image/png")
            attachments.append(
                Attachment(mime_type=mime_type, data=img_data, name=file_path.name)
            )

        except Exception as e:
            content += f"Image analysis error: {str(e)}\n"

    elif file_ext in video_exts:
        content += "Video file detected. "
        try:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=width,height,duration,codec_name,bit_rate",
                    "-of",
                    "json",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if probe.returncode == 0:
                data = json.loads(probe.stdout)
                if "streams" in data:
                    for stream in data["streams"]:
                        if "width" in stream:
                            content += f"\nResolution: {stream.get('width', '?')}x{stream.get('height', '?')}\n"
                        if "codec_name" in stream:
                            content += f"Codec: {stream.get('codec_name')}\n"
                        if "bit_rate" in stream:
                            br = int(stream.get("bit_rate", 0))
                            content += f"Bitrate: {br // 1000} kbps\n"
                if "format" in data and "duration" in data["format"]:
                    content += (
                        f"Duration: {float(data['format']['duration']):.1f} seconds\n"
                    )

            # Attach the full video file for analysis (limit to 50MB to avoid memory issues)
            if file_size < 50 * 1024 * 1024:
                with open(path, "rb") as f:
                    video_data = base64.b64encode(f.read()).decode("utf-8")
                mime_type = mime_types.get(file_ext, "video/mp4")
                attachments.append(
                    Attachment(
                        mime_type=mime_type,
                        data=video_data,
                        name=file_path.name,
                    )
                )
                content += "\n[Full video attached for analysis]"
            else:
                content += "\n[Video too large to attach - showing metadata only]"

        except FileNotFoundError:
            content += "\nffprobe/ffmpeg not available. Install ffmpeg for detailed video info."
        except Exception as e:
            content += f"\nVideo analysis error: {str(e)}\n"

    elif file_ext in audio_exts:
        content += "Audio file detected. "
        try:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=sample_rate,channels,codec_name,bit_rate",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if probe.returncode == 0:
                data = json.loads(probe.stdout)
                if "streams" in data:
                    for stream in data["streams"]:
                        if "sample_rate" in stream:
                            content += (
                                f"\nSample Rate: {stream.get('sample_rate')} Hz\n"
                            )
                        if "channels" in stream:
                            ch = stream.get("channels", 0)
                            if ch == 1:
                                ch_str = "Mono"
                            elif ch == 2:
                                ch_str = "Stereo"
                            else:
                                ch_str = f"{ch} channel"
                            content += f"Channels: {ch_str}\n"
                        if "codec_name" in stream:
                            content += f"Codec: {stream.get('codec_name')}\n"
                if "format" in data and "duration" in data["format"]:
                    content += (
                        f"Duration: {float(data['format']['duration']):.1f} seconds\n"
                    )

            # Attach the actual audio file for analysis
            # Skip if file is too large (> 10MB)
            if file_size < 10 * 1024 * 1024:
                with open(path, "rb") as f:
                    audio_data = base64.b64encode(f.read()).decode("utf-8")
                mime_type = mime_types.get(file_ext, "audio/mpeg")
                attachments.append(
                    Attachment(
                        mime_type=mime_type, data=audio_data, name=file_path.name
                    )
                )
                content += "\n[Audio file attached for analysis]"
            else:
                content += "\n[Audio file too large to attach for analysis]"

        except FileNotFoundError:
            content += (
                "\nffprobe not available. Install ffmpeg for detailed audio info."
            )
        except Exception as e:
            content += f"\nAudio analysis error: {str(e)}\n"

    else:
        content += (
            "\nUnsupported media type. Try with a known image, video, or audio format."
        )
        return ToolResult(content=content)

    return ToolResult(content=content, attachments=attachments if attachments else None)


DEFAULT_TOOLS = [
    run_bash,
    view_media,
    recall_memory,
]
