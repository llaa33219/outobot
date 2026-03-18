# ChatOutO Style Integration - OutO Frontend

## Overview

This document describes the frontend style changes applied to OutO, integrating the Neo-brutalist design system from [chatouto](https://github.com/llaa33219/chatouto).

## Changes Made

### 1. New Static Files Created

| File | Description |
|------|-------------|
| `static/style.css` | Complete Neo-brutalist CSS with all styling |
| `static/index.html` | HTML structure matching chatouto layout |
| `static/script.js` | Frontend JavaScript for chat functionality |

### 2. Modified Files

| File | Changes |
|------|---------|
| `run.py` | Added StaticFiles import, mounted static directory, updated home endpoint to serve static/index.html |

## Design System

### Colors
- **Primary**: `#000000` (Black)
- **Secondary**: `#ffffff` (White)
- **Background Primary**: `#ffffff`
- **Background Secondary**: `#f0f0f0`
- **Error**: `#ff0000`

### Typography
- **Font Family**: Space Grotesk (Google Fonts)
- **Fallback**: Inter, system-ui, sans-serif

### Neo-brutalist Elements

| Element | Style |
|---------|-------|
| Borders | 3px solid black (major), 2px solid black (minor) |
| Shadows | `8px 8px 0px #000` (default), `2px 2px 0px #000` (hover), `0px 0px 0px #000` (active) |
| Border Radius | 0px (square corners everywhere) |
| Transitions | 0.15s ease |

## Components

### Header
- Logo with OutO branding
- Version badge
- Agent bar (for delegation visualization)
- Connection status indicator
- Sidebar toggle button
- Settings toggle button

### Sidebar
- **Agents Panel**: List of available agents with icons and status
- **Activity Log**: Real-time event log with timestamps

### Chat Area
- **Welcome Screen**: Logo, description, agent list
- **Message Container**: Scrollable area for messages
- **Message Types**: User messages (right-aligned, black bg), Agent messages (left-aligned, white bg, shadow)

### Input Area
- Provider/Model selectors
- Custom model input field
- File attachment button
- Text input (textarea with auto-resize)
- Send button

### Session Management UI
- **New Chat Button**: Creates fresh session, clears all messages, agent cards, tool cards, and breadcrumb
- **Session List**: Sidebar shows all saved sessions
- **Session Continuity**: Previous messages automatically loaded when continuing a session

### Settings Modal
- API Key configuration for 8 providers
- Default provider/model selection
- Save/Cancel actions

### Interactive Components
- **Interaction Cards**: Expandable cards for tool calls and agent delegations
- **Thinking Indicator**: Animated dots while processing
- **Breadcrumb**: Agent delegation trail
- **Activity Chips**: Quick view of active agents/tools
- **Agent Cards**: Nested cards for sub-agents (depth tracking for unlimited nesting)

#### Agent Card Structure
```
.interaction-card.agent-card
├── .ic-header (clickable to collapse)
│   ├── .ic-toggle (▼)
│   ├── .ic-header-text
│   │   ├── caller (e.g., "outo")
│   │   ├── .ic-arrow (→)
│   │   └── target (e.g., "inquisitor")
│   ├── .ic-status (Processing/Done)
│   └── .ic-elapsed
└── .ic-body
    └── .ic-body-inner
        ├── .ic-delegation-msg (optional)
        ├── .ic-content-stream
        │   └── text-segment (streaming content)
        └── .ic-result-section
```

#### Tool Card Structure
```
.interaction-card.tool-card
├── .ic-header
│   ├── .ic-toggle
│   ├── .ic-header-text (agent → ⚡ tool_name)
│   └── .ic-status (Executed)
└── .ic-body
    └── .ic-body-inner
        └── .ic-tool-args
```

## API Endpoints

The frontend uses the following existing API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve index.html |
| `/static/*` | GET | Serve static files |
| `/ws/chat` | WebSocket | Real-time chat with session management |
| `/api/providers` | GET/POST | Provider configuration |
| `/api/agents` | GET | List available agents |
| `/api/sessions` | GET | List chat sessions |
| `/api/session/{id}` | GET | Load specific session |
| `/api/chat/stream` | POST | Streaming chat (SSE) - legacy |
| `/api/chat` | POST | Non-streaming chat |
| `/api/skills` | GET | List skills |
| `/api/skills/sync` | POST | Sync skills from agents |
| `/api/skills/install` | POST | Install new skill |

## Technical Notes

### WebSocket Communication
The chat uses WebSocket (`/ws/chat`) for real-time bidirectional communication. The JavaScript handles:
- `token`: Regular text output
- `tool_call`: Tool call notifications
- `tool_result`: Tool execution result
- `agent_call`: Agent delegation events
- `agent_return`: Agent delegation completion
- `thinking`: Agent reasoning display
- `error`: Error messages
- `finish`: Response completion (triggers session save)

### Markdown & Code Highlighting
- **Markdown**: Rendered using marked.js
- **Code**: Syntax highlighting using highlight.js with GitHub Dark theme

### Session Management
- Sessions stored in `~/.outobot/sessions/`
- JSON format with message history
- Real-time save via WebSocket (finish event triggers save)
- Session ID passed with each message for continuity
- History automatically loaded when continuing session

## Troubleshooting

### Frontend Not Loading
1. Check that static files exist in `/home/luke/outobot/static/`
2. Verify run.py is serving from the correct directory
3. Check browser console for errors

### API Errors
- Ensure providers are configured in Settings
- Check server logs for provider initialization errors

### Style Issues
- Verify style.css is loaded (check network tab)
- Confirm Space Grotesk font is loading
- Check for CSS conflicts

### Agent Card Issues
If sub-agent outputs appear outside their cards instead of inside:

1. **Check Backend Event Mapping**:
   - Verify `agent_call` has correct `data.agent_name` (should be sub-agent name)
   - Verify `data.from` (should be caller name)
   - See `CHANGELOG.md` for the fixed code

2. **Check WebSocket Connection**:
   - Agent cards only work with `/ws/chat` (WebSocket)
   - `/api/chat/stream` (SSE) doesn't forward `agent_name` correctly

3. **Restart Server After Changes**:
   ```bash
   pkill -f "python3 run.py" && cd /home/luke/outobot && python3 run.py &
   ```

4. **Clear Browser Cache**:
   - Use Ctrl+Shift+R for hard refresh

## Future Enhancements

Potential improvements to consider:
1. Add keyboard shortcuts help modal
2. Implement message search functionality
3. Add export session feature
4. Improve mobile responsiveness
5. Add sound notifications option
