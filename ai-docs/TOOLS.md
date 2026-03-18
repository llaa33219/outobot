# OutObot Tools System

Documentation for the default tools available to all agents.

## Overview

All OutObot agents have access to a set of default tools for interacting with the filesystem, running commands, and searching for information.

## Available Tools

### search_web

Search the web for information.

```python
@Tool
def search_web(
    query: Annotated[str, "Search keywords or question"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10,
) -> str:
```

**Parameters:**
- `query` (string): Search keywords or question
- `max_results` (int): Maximum number of results (default: 10)

**Returns:** Web search results as string

**Example:**
```python
result = search_web("Python async best practices", max_results=5)
```

---

### read_file

Read contents of a file.

```python
@Tool
def read_file(
    path: Annotated[str, "File path to read"],
) -> str:
```

**Parameters:**
- `path` (string): Absolute or relative file path

**Returns:** File contents as string

**Example:**
```python
content = read_file("/home/user/project/README.md")
```

---

### write_file

Write content to a file.

```python
@Tool
def write_file(
    path: Annotated[str, "File path to write"],
    content: Annotated[str, "Content to write"],
) -> str:
```

**Parameters:**
- `path` (string): File path to write
- `content` (string): Content to write

**Returns:** Confirmation message

**Example:**
```python
result = write_file("/home/user/project/test.py", "print('Hello')")
```

---

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

### search_code

Search for code patterns in files.

```python
@Tool
def search_code(
    query: Annotated[str, "Code pattern to search for"],
    path: Annotated[str, "Directory path to search"] = ".",
    file_pattern: Annotated[str, "File pattern (e.g., *.py)"] = "*",
) -> str:
```

**Parameters:**
- `query` (string): Code pattern to search for
- `path` (string): Directory path to search (default: current directory)
- `file_pattern` (string): File pattern glob (default: * - all files)

**Returns:** List of matching file paths

**Example:**
```python
# Find all Python files containing "async def"
results = search_code("async def", path="/home/user/project", file_pattern="*.py")
```

---

### view_media

View and analyze media files (images, videos, audio). Returns metadata and basic analysis.

```python
@Tool
def view_media(
    path: Annotated[str, "File path to the media file"],
) -> str:
```

**Parameters:**
- `path` (string): Absolute or relative file path to the media file

**Returns:** Media file metadata including:
- **Images**: Dimensions, format, color mode, DPI
- **Videos**: Resolution, codec, bitrate, duration
- **Audio**: Sample rate, channels, codec, duration

**Supported Formats:**
- Images: jpg, jpeg, png, gif, bmp, webp, tiff, ico
- Videos: mp4, avi, mov, mkv, webm, flv, wmv, m4v
- Audio: mp3, wav, flac, aac, ogg, m4a, wma, opus

**Example:**
```python
result = view_media("/home/luke/.outobot/uploads/image.png")
# Returns: File: image.png, Path: ..., Size: 1.2 MB, Type: png
# Dimensions: 1920 x 1080 pixels, Format: PNG, Mode: RGB
```

**Note:** Requires Pillow for images and ffmpeg (ffprobe) for video/audio analysis.

---

### list_memories

List all available conversation memories (sessions). This allows agents to see what previous conversations are stored.

```python
@Tool
def list_memories() -> str:
```

**Returns:** List of available session IDs, sorted by creation time (newest first). Shows up to 20 sessions.

**Example:**
```python
result = list_memories()
# Returns: "Found 5 memories:
#
# - session_20260317_231312
# - session_20260317_231156
# - ..."
```

**Storage Location:** `~/.outobot/sessions/`

---

### recall_memory

Recall a specific conversation memory by session ID.

```python
@Tool
def recall_memory(
    session_id: Annotated[str, "The session ID to recall"],
) -> str:
```

**Parameters:**
- `session_id` (string): The session ID (e.g., "session_20260315_143022")

**Returns:** Full conversation content including:
- Session ID and creation time
- All messages with sender, content, and timestamp

**Example:**
```python
result = recall_memory("session_20260317_231156")
# Returns: "=== Memory: session_20260317_231156 ===
# Created: 2026-03-17T23:11:56.123456
#
# [2026-03-17T23:11:56] You: 너 스킬 뭐 쓸 수 있어?
#
# [2026-03-17T23:12:01] outo: 저는 outo입니다..."
```

**Error Handling:**
- Returns error if session not found
- Lists available sessions in error message

---

### search_memory

Search through all conversation memories for a specific query.

```python
@Tool
def search_memory(
    query: Annotated[str, "Search query to find in conversation memories"],
) -> str:
```

**Parameters:**
- `query` (string): Search text to find in all conversations

**Returns:** List of matching messages with:
- Session ID
- Sender
- Timestamp
- Message content (truncated to 200 chars)

**Example:**
```python
result = search_memory("Python")
# Returns: "Found 3 matches for 'Python':
#
# [session_20260317_231156] outo at 2026-03-17T23:12:01: ...Python async best practices...
#
# [session_20260317_230045] You at 2026-03-17T23:00:45: ...Python로 코드 작성해줘..."
```

**Note:** Search is case-insensitive and searches both user and agent messages.

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
    search_web,
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
