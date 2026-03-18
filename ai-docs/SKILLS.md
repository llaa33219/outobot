# OutO Skills System

Documentation for the skills management system in OutO.

## Overview

Skills are reusable capabilities that agents can use to perform specialized tasks. OutO supports syncing skills from various AI agent tools and installing new skills from npm.

## Skill Sources

OutO can sync skills from 7 different AI agent tools:

| Agent | Path | Description |
|-------|------|-------------|
| claude-code | ~/.claude/skills/ | Claude Code skills |
| cursor | ~/.cursor/skills/ | Cursor skills |
| windsurf | ~/.windsurf/skills/ | Windsurf skills |
| gemini | ~/.gemini/skills/ | Gemini CLI skills |
| opencode | ~/.config/opencode/skills/ | OpenCode skills |
| copilot | ~/.copilot/skills/ | Copilot skills |
| agents | ~/.agents/skills/ | Universal agent skills |

## Skills Manager

The `SkillsManager` class in `outo/skills.py` handles skill synchronization and installation.

### Initialization

```python
from outo.skills import SkillsManager
from pathlib import Path

skills_manager = SkillsManager(Path("~/.outobot/skills"))
```

## Methods

### sync_from_agents()

Synchronizes skills from all available agent tool directories.

```python
def sync_from_agents(self) -> dict:
    """Returns: {"added": 2, "removed": 1, "updated": 3}"""
```

**Process:**
1. Scan each agent's skills directory for SKILL.md files
2. Copy new/updated skills to ~/.outobot/skills/
3. Deduplicate skills with same name from multiple sources
4. Track which sources each skill came from
5. Remove skills that no longer exist in source directories

**Example:**
```python
result = skills_manager.sync_from_agents()
print(f"Added: {result['added']}, Removed: {result['removed']}, Updated: {result['updated']}")
```

### add_skill_from_npm(command)

Installs a skill from npm registry using npx skills.

```python
def add_skill_from_npm(self, command: str) -> dict:
    """Returns: {"success": True, "message": "...", "sync": {...}}"""
```

**Parameters:**
- `command` (string): npm command, e.g., "npx skills add vercel-labs/agent-skills"

**Example:**
```python
result = skills_manager.add_skill_from_npm("npx skills add vercel-labs/agent-skills")
if result["success"]:
    print("Skill installed!")
```

### get_skills()

Returns list of all installed skills.

```python
def get_skills(self) -> list:
    """Returns: [{"name": "...", "description": "...", "sources": [...]}]"""
```

### get_sources()

Returns dictionary of sources with skill counts.

```python
def get_sources(self) -> dict:
    """Returns: {"claude-code": 5, "cursor": 3, ...}"""
```

### scan_agent_skills()

Returns dictionary of available skills per agent source.

```python
def scan_agent_skills(self) -> dict[str, list[Path]]:
    """Returns: {"claude-code": [Path, Path], "cursor": [Path]}"""
```

## Skill File Structure

Each skill should have:

```
skill-name/
├── SKILL.md          # Required - skill documentation
├── script.py         # Optional - skill code
├── config.json       # Optional - skill config
└── ...
```

### SKILL.md Format

```markdown
---
description: "Skill description here"
---

# Skill Name

Detailed skill documentation...

## When to Use

- Use case 1
- Use case 2

## How to Use

Step-by-step instructions...
```

## _skills.json Format

Skills metadata stored in `~/.outobot/skills/_skills.json`:

```json
{
  "version": "1.0.0",
  "skills": [
    {
      "name": "remotion",
      "description": "Best practices for Remotion",
      "agents": [],
      "enabled": true,
      "file": "remotion/SKILL.md",
      "sources": ["claude-code"]
    },
    {
      "name": "agent-browser",
      "description": "Browser automation for AI agents",
      "agents": [],
      "enabled": true,
      "file": "agent-browser/SKILL.md",
      "sources": ["agents"]
    }
  ],
  "sources": {}
}
```

## API Endpoints

### GET /api/skills

List all installed skills.

**Response:**
```json
{
  "skills": [
    {
      "name": "skill-name",
      "description": "Skill description",
      "sources": ["claude-code", "cursor"],
      "enabled": true,
      "file": "skill-name/SKILL.md"
    }
  ],
  "sources": {},
  "available_agents": [
    {"name": "claude-code", "path": "/home/user/.claude/skills"}
  ],
  "total": 1
}
```

### POST /api/skills/sync

Sync skills from agent tools.

**Response:**
```json
{
  "message": "Synced! Added: 2, Removed: 0, Updated: 1",
  "result": {"added": 2, "removed": 0, "updated": 1},
  "total_skills": 5
}
```

### POST /api/skills/install

Install skill from npm.

**Request:**
```json
{"command": "npx skills add vercel-labs/agent-skills"}
```

**Response:**
```json
{
  "message": "Skill installed successfully",
  "sync": {"added": 1, "removed": 0, "updated": 0}
}
```

## Using Skills

When an agent needs to use a skill:

1. **Read Skill Documentation**: Use Read tool to read `~/.outobot/skills/<skill-name>/SKILL.md`
2. **Understand Purpose**: Check the skill's description and instructions
3. **Apply Skill**: Follow the skill's guidelines to complete the task

```python
# Agent reads skill documentation
content = read_file("~/.outobot/skills/remotion/SKILL.md")
```

## Troubleshooting

### Skills Not Syncing

**Symptom:** "No skills found" after sync

**Solutions:**
- Ensure source agent tools are installed (Claude Code, Cursor, etc.)
- Check source skill directories exist
- Verify SKILL.md files exist in source directories
- Check agent paths in AGENT_SKILL_PATHS

### Skill Installation Fails

**Symptom:** npm install fails

**Solutions:**
- Ensure nodejs/npm is installed
- Check distrobox container is running
- Verify network connectivity
- Try manual installation in container

### Duplicate Skills

**Symptom:** Same skill from multiple sources

**Solution:** This is expected behavior. The system tracks all sources:
```json
{
  "name": "remotion",
  "sources": ["claude-code", "cursor"]
}
```

### Skill Not Found

**Symptom:** Agent cannot find skill

**Solutions:**
- Verify skill exists in ~/.outobot/skills/
- Check SKILL.md file exists
- Run sync to refresh skills
