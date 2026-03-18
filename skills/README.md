# OutO Skills

Skills define the capabilities of agents. This directory contains registered skills that can be loaded by agents.

## Structure

```
SKILLS/
├── README.md           # This file
├── _skills.json        # Skill registry
├── code_review/        # Code review skill
├── research/           # Research skill
├── creative/           # Creative writing skill
└── ...
```

## Creating a Skill

1. Create a directory for your skill
2. Add `skill.py` with your skill implementation
3. Add `SKILL.md` with documentation
4. Register in `_skills.json`

## Skill Format

```json
{
  "skills": [
    {
      "name": "code_review",
      "description": "Review code for issues",
      "agents": ["recensor", "peritus"],
      "enabled": true
    }
  ]
}
```

## Example Skill

### skill.py

```python
from agentouto import Tool
from typing import Annotated

@Tool
def code_review(
    code: Annotated[str, "Code to review"],
    language: Annotated[str, "Programming language"] = "python"
) -> str:
    """Review code and provide feedback."""
    issues = []
    
    if len(code) > 500:
        issues.append("Consider breaking into smaller functions")
    
    if "password" in code.lower() or "secret" in code.lower():
        issues.append("Ensure no hardcoded credentials")
    
    if not issues:
        return "Code looks good!"
    
    return "Issues found:\n" + "\n".join(f"- {i}" for i in issues)
```

### SKILL.md

```markdown
# Code Review Skill

Review code for common issues and best practices.

## Usage

Pass code to the tool for review.

## Checks

- Code length and complexity
- Security issues
- Best practices
- Style consistency
```

## Built-in Skills

- **code_review**: Review code for issues
- **research**: Research topics thoroughly
- **creative**: Creative writing assistance
- **analysis**: Deep analysis of complex topics
