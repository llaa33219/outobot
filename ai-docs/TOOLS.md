# OutObot Tools System

Documentation for the default tools available to all agents.

## Overview

All OutObot agents have access to a set of default tools for executing commands, viewing media, and searching memories.

## Available Tools

### run_bash

Execute a bash command and return output.

```python
@Tool
def run_bash(
    command: Annotated[str, "Command to execute"],
    timeout: Annotated[int, "Timeout in seconds"] = 60,
) -> str:
```

**Parameters:**
- `command` (string): Command to execute
- `timeout` (int): Timeout in seconds (default: 60)

**Returns:** Command stdout + stderr

**Example:**
```python
output = run_bash("ls -la", timeout=30)
```

---

### view_media

View and analyze media files (images, videos, audio). Returns metadata and basic analysis, with the actual media file attached for visual/audio analysis.

```python
@Tool
def view_media(
    path: Annotated[str, "File path to the media file"],
) -> ToolResult:
```

**Parameters:**
- `path` (string): Absolute or relative file path to the media file

**Returns:** `ToolResult` with:
- **content**: Media file metadata including:
  - **Images**: Dimensions, format, color mode, DPI
  - **Videos**: Resolution, codec, bitrate, duration
  - **Audio**: Sample rate, channels, codec, duration
- **attachments**: Actual media file (image, video, or audio) for visual/audio analysis

**Supported Formats:**
- Images: jpg, jpeg, png, gif, bmp, webp, tiff, ico
- Videos: mp4, avi, mov, mkv, webm, flv, wmv, m4v (full file attached, max 50MB)
- Audio: mp3, wav, flac, aac, ogg, m4a, wma, opus (full file attached, max 10MB)

**Example:**
```python
result = view_media("/home/luke/.outobot/uploads/image.png")
# result.content: "File: image.png, Path: ..., Size: 1.2 MB, Type: png\nDimensions: 1920 x 1080 pixels..."
# result.attachments: [Attachment(mime_type="image/png", data="...", name="image.png")]
```

**Note:** Requires Pillow for images and ffmpeg (ffprobe) for video/audio analysis.

---

### recall_memory

Recall memories using semantic search. Queries outowiki for relevant past context, with fallback to session-based search.

```python
@Tool
def recall_memory(
    query: Annotated[
        str, "Topic or question to recall. Empty string to check memory status."
    ] = "",
) -> str:
```

**Parameters:**
- `query` (string): Topic or question to search for. Pass empty string to check memory system status.

**Returns:** 
- With query: Relevant memory context from outowiki, or matching session excerpts
- Without query: Memory system status (outowiki availability, session count)

**Behavior:**
1. If query is empty: Returns memory system status
2. If outowiki is available: Performs semantic search via outowiki
3. Fallback: Searches session files for text matches

**Example:**
```python
# Check memory status
status = recall_memory("")
# Returns: "🧠 outowiki is ACTIVE\n📁 15 sessions stored"

# Search for context
context = recall_memory("user's preferred programming language")
# Returns relevant memory context from past conversations
```

**Storage Locations:**
- outowiki: `~/.outobot/wiki/` (markdown files)
- Fallback sessions: `~/.outobot/sessions/`

---

### record_to_wiki

Record important discoveries to wiki for future reference.

```python
@Tool
def record_to_wiki(
    content: Annotated[str, "Content to record to wiki. Include key facts, discoveries, or learnings."],
    category: Annotated[str, "Category/topic for the wiki entry (e.g., 'technology/ai', 'programming/python')"] = "",
) -> str:
```

**Parameters:**
- `content` (string): Content to record to wiki. Include key facts, discoveries, or learnings.
- `category` (string, optional): Category/topic for the wiki entry.

**Returns:** Confirmation message or error.

**When to use:**
- Learning a new library or framework usage
- Solving a complex bug or debugging technique
- Understanding a new algorithm or data structure
- Discovering best practices or design patterns
- User preferences or project-specific knowledge
- Important technical decisions or tradeoffs

**Example:**
```python
# Record a library usage discovery
result = record_to_wiki(
    "React useEffect cleanup: Return a function to clean up subscriptions",
    category="programming/react"
)

# Record a bug solution
result = record_to_wiki(
    "Python GIL workaround: Use multiprocessing instead of threading for CPU-bound tasks",
    category="programming/python"
)
```

---

## File Upload API

### POST /api/upload

Upload a file to the server. Files are stored in `~/.outobot/uploads/`.

**Request:**
```
POST /api/upload
Content-Type: multipart/form-data

Form Data:
- file: The file to upload
```

**Response:**
```json
{
  "path": "/home/luke/.outobot/uploads/1234567890_filename.png",
  "name": "filename.png",
  "type": "png"
}
```

**Example (curl):**
```bash
curl -X POST -F "file=@/path/to/image.png" http://localhost:7227/api/upload
```

---

## File Attachments in Chat

When users attach files in the chat UI:

1. Files are uploaded to the server via `/api/upload`
2. File metadata (path, name, type) is sent with the message
3. Agents receive the message with attached file information

**Message format sent to agent:**
```
[User message]

[Attached files]
- image.png: /home/luke/.outobot/uploads/... (type: png)
- audio.mp3: /home/luke/.outobot/uploads/... (type: mp3)

Use the 'view_media' tool to view these files when needed.
```

**ChatMessage model:**
```python
class ChatMessage(BaseModel):
    message: str
    agent: str = "outo"
    session_id: str | None = None
    attachments: list[dict] | None = None
```

---

## Tool Definitions

Tools are defined in `outo/tools.py`:

```python
DEFAULT_TOOLS = [
    run_bash,
    view_media,
    recall_memory,
    record_to_wiki,
]
```

## Adding Custom Tools

### Using @Tool Decorator

```python
from agentouto import Tool
from typing import Annotated

@Tool
def my_custom_tool(
    param1: Annotated[str, "Description of param1"],
    param2: Annotated[int, "Description of param2"] = 10,
) -> str:
    """Tool description."""
    # Implementation
    return result
```

### Registering Tools

Add to DEFAULT_TOOLS list:

```python
DEFAULT_TOOLS = [
    read_file,
    write_file,
    run_bash,
    search_code,
    view_media,
    list_memories,
    recall_memory,
    search_memory,
    my_custom_tool,
]
```

## Security Considerations

### File Access

- `read_file` and `write_file` have access to all files the server process can access
- No sandboxing by default
- Consider running in isolated container

### Command Execution

- `run_bash` can execute any shell command
- Runs with server process privileges
- Can be restricted via container isolation

## Troubleshooting

### Permission Denied

**Error:** Permission denied when reading/writing files

**Solutions:**
- Check file permissions
- Ensure server has appropriate access
- Run server with appropriate user

### Command Timeout

**Error:** Command execution timeout

**Solutions:**
- Increase timeout parameter
- Check command is not hanging
- Verify system resources

### File Not Found

**Error:** File path does not exist

**Solutions:**
- Verify file path is correct
- Check working directory
- Use absolute paths when possible
