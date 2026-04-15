# OutObot Configuration

Documentation for configuration files in OutObot.

## Configuration Directory

```
~/.outobot/config/
├── providers.json    # Saved provider configuration
├── config.yaml       # Sample configuration (reference)
└── .env.example     # Environment variables template
```

## providers.json

Location: `~/.outobot/config/providers.json`

Active provider configuration with API keys and settings. This is the main configuration file used by the system.

```json
{
  "openai": {
    "enabled": true,
    "api_key": "sk-...",
    "model": "gpt-5.4"
  },
  "anthropic": {
    "enabled": false,
    "api_key": "",
    "model": "claude-sonnet-4-6"
  },
  "google": {
    "enabled": false,
    "api_key": "",
    "model": "gemini-3.1-pro"
  },
  "minimax": {
    "enabled": false,
    "api_key": "",
    "model": "MiniMax-M2.7"
  },
  "glm": {
    "enabled": false,
    "api_key": "",
    "region": "international",
    "model": "GLM-5"
  },
  "glm_coding": {
    "enabled": false,
    "api_key": "",
    "model": "GLM-5"
  },
  "kimi": {
    "enabled": false,
    "api_key": "",
    "model": "kimi-k2.5"
  },
  "kimi_code": {
    "enabled": false,
    "api_key": "",
    "model": "kimi-k2.5"
  }
}
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| enabled | boolean | Enable/disable provider |
| api_key | string | API key for provider |
| model | string | Default model to use |
| region | string | Region for GLM (international/china) |
| base_url | string | Custom base URL (for local) |

## Supported Providers

### OpenAI

| Setting | Value |
|---------|-------|
| Name | OpenAI |
| Models | gpt-5.4-pro, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3 |
| Base URL | https://api.openai.com/v1 |
| API Key | sk-... |

### Anthropic

| Setting | Value |
|---------|-------|
| Name | Anthropic |
| Models | claude-opus-4-6, claude-sonnet-4-6 |
| Base URL | https://api.anthropic.com |
| API Key | sk-ant-... |

### Google

| Setting | Value |
|---------|-------|
| Name | Google |
| Models | gemini-3.1-pro, gemini-3-flash |
| Base URL | https://generativelanguage.googleapis.com/v1 |
| API Key | AIza... |

### MiniMax

| Setting | Value |
|---------|-------|
| Name | MiniMax |
| Models | MiniMax-M2.7, MiniMax-M2.5-highspeed, MiniMax-M2.5, MiniMax-M2.1 |
| Base URL | https://api.minimax.io/v1 |
| API Key | Required |

### GLM (Zhipu AI)

| Setting | Value |
|---------|-------|
| Name | GLM (Zhipu AI) |
| Models | GLM-5, GLM-4.7 |
| Base URL (International) | https://api.z.ai/api/paas/v4 |
| Base URL (China) | https://open.bigmodel.cn/api/paas/v4 |
| API Key | Required |
| Region | international or china |

### GLM Coding Plan

| Setting | Value |
|---------|-------|
| Name | GLM Coding Plan |
| Models | GLM-5, GLM-4.7 |
| Base URL | https://open.bigmodel.cn/api/coding/paas/v4 |
| API Key | Required |

### Kimi (Moonshot AI)

| Setting | Value |
|---------|-------|
| Name | Kimi (Moonshot AI) |
| Models | kimi-k2.5, kimi-k2.5-thinking, kimi-k2 |
| Base URL | https://api.moonshot.ai/v1 |
| API Key | Required |

### Kimi Code Plan

| Setting | Value |
|---------|-------|
| Name | Kimi Code Plan |
| Models | kimi-k2.5, kimi-k2.5-thinking, kimi-k2 |
| Base URL | https://api.moonshot.ai/v1 |
| API Key | Required |

### Local (Ollama/vLLM)

| Setting | Value |
|---------|-------|
| Name | Local |
| Models | Any (from Ollama) |
| Base URL | http://localhost:11434/v1 |
| API Key | not-needed |

## config.yaml

Location: `~/.outobot/config/config.yaml`

Sample configuration file (reference only - actual config via web UI):

```yaml
# OutObot Configuration
# Edit this file to configure your agents and providers

server:
  host: "localhost"
  port: 7227
  
# Provider configurations
# Add your API keys here
providers:
  openai:
    enabled: false
    api_key: ""
    # models: gpt-5.4-pro, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3
    
  anthropic:
    enabled: false
    api_key: ""
    # models: claude-opus-4-6, claude-sonnet-4-6
    
  google:
    enabled: false
    api_key: ""
    # models: gemini-3.1-pro, gemini-3-flash
    
  # For local models (Ollama, vLLM, LM Studio)
  local:
    enabled: false
    base_url: "http://localhost:11434/v1"
    api_key: "not-needed"
    # models: llama3, mistral, etc.

# Agent configurations
agents:
  outo:
    model: "gpt-5.4"
    provider: "openai"
    temperature: 1.0
    
  peritus:
    model: "claude-sonnet-4-6"
    provider: "anthropic"
    temperature: 0.9
    
  # ... other agents

# UI Settings
ui:
  theme: "neo-brutalism"
  title: "OutObot - Multi-Agent AI System"
  session_timeout: 3600
```

## .env.example

Location: `~/.outobot/config/.env.example`

Template for environment variables:

```bash
# OpenAI API Key
OPENAI_API_KEY=sk-your-openai-key-here

# Anthropic API Key  
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Google API Key
GOOGLE_API_KEY=AIza-your-google-key-here

# MiniMax API Key
MINIMAX_API_KEY=your-minimax-key-here

# GLM API Key
GLM_API_KEY=your-glm-key-here

# Kimi API Key
KIMI_API_KEY=your-kimi-key-here
```

## Discord Bot Configuration

Location: `~/.outobot/config/discord.json`

Discord bot settings are stored separately from `providers.json`.

```json
{
  "enabled": true,
  "token": "your-discord-bot-token"
}
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| enabled | boolean | Enable/disable Discord bot |
| token | string | Discord bot token from Developer Portal |

### How to Get a Discord Bot Token

1. Go to Discord Developer Portal (https://discord.com/developers/applications)
2. Create a new application
3. Go to Bot section and create a bot
4. Copy the bot token
5. Enable MESSAGE CONTENT INTENT in Bot settings

### Configure via Web UI

1. Open http://localhost:7227
2. Go to Settings
3. Open Discord Bot section
4. Enable bot and paste token
5. Save configuration

### Configure via API

- `GET /api/discord`
- `POST /api/discord`

### Bot Behavior

- Only responds to @mentions
- Maintains per-channel sessions
- Splits responses longer than 2000 characters into multiple messages

## Memory Configuration

Location: `~/.outobot/config/memory.json`

OutObot uses an intelligent memory system powered by **outomem** (Neo4j + LanceDB) for persistent agent memory across conversations.

### Configuration File

```json
{
  "enabled": true,
  "provider": "openai",
  "memory_model": "",
  "embed_provider": "openai",
  "embed_api_url": "https://api.openai.com/v1",
  "embed_api_key": "sk-...",
  "embed_model": "text-embedding-3-small",
  "neo4j_uri": "bolt://localhost:17241",
  "neo4j_user": "neo4j",
  "neo4j_password": "outobot-neo4j-pass",
  "neo4j_container_name": "outobot-neo4j",
  "neo4j_image": "neo4j:latest",
  "db_path": "~/.outobot/config/outomem.lance",
  "max_tokens": 4096
}
```

### Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| enabled | boolean | true | Enable/disable memory system |
| provider | string | "openai" | AI provider for memory processing |
| memory_model | string | "" | Custom model for memory (uses provider default if empty) |
| embed_provider | string | "" | Embedding provider (openai, google, cohere, voyage, qwen, mistral, custom) |
| embed_api_url | string | "" | Embedding API URL (auto-set from presets) |
| embed_api_key | string | "" | Embedding API key |
| embed_model | string | "text-embedding-3-small" | Embedding model name |
| neo4j_uri | string | "bolt://localhost:17241" | Neo4j connection URI |
| neo4j_user | string | "neo4j" | Neo4j username |
| neo4j_password | string | "" | Neo4j password |
| neo4j_container_name | string | "outobot-neo4j" | Distrobox container name for Neo4j |
| neo4j_image | string | "neo4j:latest" | Neo4j Docker image |
| db_path | string | "" | LanceDB path (auto-generated if empty) |
| max_tokens | int | 4096 | Max tokens for memory context |

### Embedding Provider Presets

| Provider | Default URL | Default Model |
|----------|-------------|---------------|
| openai | https://api.openai.com/v1 | text-embedding-3-small |
| google | https://generativelanguage.googleapis.com/v1beta2 | text-embedding-004 |
| cohere | https://api.cohere.ai/v1 | embed-english-v3.0 |
| voyage | https://api.voyageai.com/v1 | voyage-4-lite |
| qwen | https://dashscope.aliyuncs.com/api/v1 | text-embedding-v3 |
| mistral | https://api.mistral.ai/v1 | mistral-embed |
| custom | (user-provided) | (user-provided) |

### Neo4j Setup

The memory system uses Neo4j for knowledge graph storage. It's managed automatically via distrobox:

1. **Auto-creation**: On first use, a distrobox container named `outobot-neo4j` is created
2. **Ports**: Neo4j exposes bolt (17241) and HTTP (17242) ports
3. **Data**: Stored in `~/.outobot/config/neo4j_data/`
4. **Default password**: `outobot-neo4j-pass` (change in config)

### Configure via Web UI

1. Open http://localhost:7227
2. Go to Settings
3. Open Memory section
4. Configure embedding provider and API key
5. Set Neo4j password
6. Save configuration

### Configure via API

- `GET /api/memory/config`
- `POST /api/memory/config`
- `GET /api/memory/health`

### How It Works

1. **Storage**: After each conversation, messages are stored in both LanceDB (vector embeddings) and Neo4j (entities/relationships)
2. **Retrieval**: Before each response, relevant past context is retrieved via semantic search
3. **Context Injection**: Retrieved memory is prepended as a system message

### Dependencies

The memory system requires:
- `outomem` Python library
- `neo4j` (managed via distrobox container)
- `lancedb` (vector database)

### Troubleshooting

#### Memory Not Available

**Symptom**: `recall_memory("")` shows "outomem not available"

**Solutions**:
1. Check if outomem is installed: `pip show outomem`
2. Verify embedding API key is configured
3. Check Neo4j is running: `distrobox enter outobot-neo4j -- neo4j status`
4. View health check: `curl http://localhost:7227/api/memory/health`

#### Neo4j Connection Failed

**Symptom**: Health check shows `"neo4j": {"connected": false}`

**Solutions**:
1. Check container exists: `distrobox list | grep neo4j`
2. Start Neo4j: `distrobox enter outobot-neo4j -- neo4j start`
3. Verify port 17241 is accessible: `nc -zv localhost 17241`
4. Check password matches config

#### Embedding API Errors

**Symptom**: `"embedding": {"working": false}`

**Solutions**:
1. Verify embed_api_key is correct
2. Check embed_api_url matches provider
3. Ensure model name is valid for provider
4. Test API key: `curl -H "Authorization: Bearer $KEY" $URL/models`

## Web UI Configuration

The easiest way to configure OutObot is via the web UI:

1. Open http://localhost:7227
2. Go to Settings tab
3. Enable providers
4. Enter API keys
5. Select models
6. Click Save Configuration

## Configuration Priority

1. providers.json (active config)
2. config.yaml (reference)
3. .env.example (template)

## Backup Configuration

```bash
# Backup
cp -r ~/.outobot/config ~/backup/outobot_config

# Restore
cp -r ~/backup/outobot_config/* ~/.outobot/config/
```

## Troubleshooting

### Config Not Loading

**Symptom:** Providers not available

**Solutions:**
- Check providers.json exists: `ls ~/.outobot/config/`
- Verify JSON is valid: `python -m json.tool ~/.outobot/config/providers.json`
- Ensure at least one provider is enabled

### Invalid API Key

**Symptom:** "Invalid API key" error

**Solutions:**
- Verify API key in providers.json
- Check key format (no extra spaces, correct prefix)
- Ensure provider is enabled

### Model Not Available

**Symptom:** "Model not found" error

**Solutions:**
- Check model name is correct
- Verify model is available for provider
- Try different model

### Region Not Set for GLM

**Symptom:** GLM requests fail

**Solutions:**
- Set region in providers.json: "international" or "china"
- Verify base URL matches region

---

## Dependencies

OutObot requires the following Python packages:

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn[standard] | ASGI server with WebSocket support |
| python-multipart | Form data parsing |
| aiohttp | Async HTTP client |
| pydantic | Data validation |
| agentouto | Multi-agent framework |
| wsproto | WebSocket protocol support |
| websockets | WebSocket server implementation |
| discord.py | Discord bot integration |

**Important:** Always use `uvicorn[standard]` (not plain `uvicorn`) to ensure WebSocket support is installed. The `[standard]` extra includes the `websockets` library required for real-time chat.

If WebSocket errors occur (e.g., "No supported WebSocket library detected"):
```bash
pip install wsproto websockets --upgrade
```
