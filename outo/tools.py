"""
OutObot Tools
Default tools available to all agents
"""

import json
import os
from pathlib import Path
from typing import Annotated
from agentouto import Tool

# Sessions directory - configured to ~/.outobot/sessions
SESSIONS_DIR = Path.home() / ".outobot" / "sessions"


@Tool
def list_memories() -> str:
    """List all available conversation memories (sessions)."""
    if not SESSIONS_DIR.exists():
        return "No memories found. No sessions directory exists."

    sessions = [f.stem for f in SESSIONS_DIR.glob("*.json")]
    if not sessions:
        return "No memories found. No previous conversations saved."

    # Sort by creation time (newest first)
    sessions.sort(reverse=True)

    result = f"Found {len(sessions)} memories:\n\n"
    for session in sessions[:20]:  # Show max 20
        result += f"- {session}\n"

    if len(sessions) > 20:
        result += f"\n... and {len(sessions) - 20} more"

    return result


@Tool
def recall_memory(
    session_id: Annotated[
        str, "The session ID to recall (e.g., session_20260315_143022)"
    ],
) -> str:
    """Recall a specific conversation memory by session ID."""
    if not SESSIONS_DIR.exists():
        return "Error: Sessions directory does not exist."

    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        available = [f.stem for f in SESSIONS_DIR.glob("*.json")]
        available_str = ", ".join(available[:10]) if available else "none"
        return f"Error: Session '{session_id}' not found. Available: {available_str}"

    with open(session_file) as f:
        data = json.load(f)

    messages = data.get("messages", [])
    if not messages:
        return f"Session '{session_id}' is empty."

    result = f"=== Memory: {session_id} ===\n"
    result += f"Created: {data.get('created_at', 'unknown')}\n\n"

    for msg in messages:
        sender = msg.get("sender", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        result += f"[{timestamp}] {sender}: {content}\n\n"

    return result


@Tool
def search_memory(
    query: Annotated[str, "Search query to find in conversation memories"],
) -> str:
    """Search through all conversation memories for a specific query."""
    if not SESSIONS_DIR.exists():
        return "Error: Sessions directory does not exist."

    sessions = list(SESSIONS_DIR.glob("*.json"))
    if not sessions:
        return "No memories found to search."

    query_lower = query.lower()
    results = []

    for session_file in sessions:
        with open(session_file) as f:
            data = json.load(f)

        session_id = data.get("session_id", session_file.stem)
        messages = data.get("messages", [])

        for msg in messages:
            content = msg.get("content", "").lower()
            if query_lower in content:
                sender = msg.get("sender", "unknown")
                timestamp = msg.get("timestamp", "")
                # Show context around the match
                result = f"[{session_id}] {sender} at {timestamp}: ...{msg.get('content', '')[:200]}..."
                results.append(result)

    if not results:
        return f"No memories found containing '{query}'."

    result = f"Found {len(results)} matches for '{query}':\n\n"
    for r in results[:10]:  # Max 10 results
        result += f"{r}\n\n"

    if len(results) > 10:
        result += f"... and {len(results) - 10} more matches"

    return result


@Tool
def search_web(
    query: Annotated[str, "Search keywords or question"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10,
) -> str:
    """Search the web for information."""
    return f"Web search for: {query} (max {max_results} results)"


@Tool
def read_file(
    path: Annotated[str, "File path to read"],
) -> str:
    """Read contents of a file."""
    with open(path, "r") as f:
        return f.read()


@Tool
def write_file(
    path: Annotated[str, "File path to write"],
    content: Annotated[str, "Content to write"],
) -> str:
    """Write content to a file."""
    with open(path, "w") as f:
        f.write(content)
    return f"Written to {path}"


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
def search_code(
    query: Annotated[str, "Code pattern to search for"],
    path: Annotated[str, "Directory path to search"] = ".",
    file_pattern: Annotated[str, "File pattern (e.g., *.py)"] = "*",
) -> str:
    """Search for code patterns in files."""
    import subprocess

    result = subprocess.run(
        f"grep -r '{query}' {path} --include='{file_pattern}' -l",
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


@Tool
def view_media(
    path: Annotated[str, "File path to the media file (image, video, or audio)"],
) -> str:
    """View and analyze media files (images, videos, audio). Returns metadata and basic analysis."""
    import os
    from pathlib import Path

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    file_path = Path(path)
    if not file_path.exists():
        return f"Error: File does not exist: {path}"

    file_ext = file_path.suffix.lower()
    file_size = os.path.getsize(path)
    file_size_str = (
        f"{file_size / 1024:.1f} KB"
        if file_size < 1024 * 1024
        else f"{file_size / (1024 * 1024):.1f} MB"
    )

    result = f"File: {file_path.name}\n"
    result += f"Path: {path}\n"
    result += f"Size: {file_size_str}\n"
    result += f"Type: {file_ext[1:] if file_ext else 'unknown'}\n"

    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico"]
    video_exts = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv", ".m4v"]
    audio_exts = [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".opus"]

    if file_ext in image_exts:
        try:
            from PIL import Image

            with Image.open(path) as img:
                result += f"Dimensions: {img.width} x {img.height} pixels\n"
                result += f"Format: {img.format}\n"
                result += f"Mode: {img.mode}\n"
                if hasattr(img, "info"):
                    if "dpi" in img.info:
                        result += f"DPI: {img.info['dpi']}\n"
        except Exception as e:
            result += f"Image analysis error: {str(e)}\n"

    elif file_ext in video_exts:
        result += "Video file detected. "
        try:
            import subprocess

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
                import json

                data = json.loads(probe.stdout)
                if "streams" in data:
                    for stream in data["streams"]:
                        if "width" in stream:
                            result += f"\nResolution: {stream.get('width', '?')}x{stream.get('height', '?')}\n"
                        if "codec_name" in stream:
                            result += f"Codec: {stream.get('codec_name')}\n"
                        if "bit_rate" in stream:
                            br = int(stream.get("bit_rate", 0))
                            result += f"Bitrate: {br // 1000} kbps\n"
                if "format" in data:
                    if "duration" in data["format"]:
                        result += f"Duration: {float(data['format']['duration']):.1f} seconds\n"
        except FileNotFoundError:
            result += "\nffprobe not available. Install ffmpeg for detailed video info."
        except Exception as e:
            result += f"\nVideo analysis error: {str(e)}\n"

    elif file_ext in audio_exts:
        result += "Audio file detected. "
        try:
            import subprocess

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
                import json

                data = json.loads(probe.stdout)
                if "streams" in data:
                    for stream in data["streams"]:
                        if "sample_rate" in stream:
                            result += f"\nSample Rate: {stream.get('sample_rate')} Hz\n"
                        if "channels" in stream:
                            ch = stream.get("channels", 0)
                            ch_str = f"{ch} channel"
                            if ch == 1:
                                ch_str = "Mono"
                            elif ch == 2:
                                ch_str = "Stereo"
                            result += f"Channels: {ch_str}\n"
                        if "codec_name" in stream:
                            result += f"Codec: {stream.get('codec_name')}\n"
                if "format" in data and "duration" in data["format"]:
                    result += (
                        f"Duration: {float(data['format']['duration']):.1f} seconds\n"
                    )
        except FileNotFoundError:
            result += "\nffprobe not available. Install ffmpeg for detailed audio info."
        except Exception as e:
            result += f"\nAudio analysis error: {str(e)}\n"

    else:
        result += (
            "\nUnsupported media type. Try with a known image, video, or audio format."
        )

    return result


DEFAULT_TOOLS = [
    search_web,
    read_file,
    write_file,
    run_bash,
    search_code,
    view_media,
    list_memories,
    recall_memory,
    search_memory,
]
