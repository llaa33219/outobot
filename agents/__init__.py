"""
OutO Agent Definitions
Core agents for the multi-agent system
"""

from typing import Annotated, Literal
from agentouto import Agent, Tool


def create_agents(providers: dict) -> dict:
    agents = {}

    if "openai" in providers:
        agents["outo"] = Agent(
            name="outo",
            instructions="Main coordinator. Orchestrate tasks by delegating to appropriate agents. Manage workflow and ensure quality output.",
            model="gpt-5.2",
            provider="openai",
            temperature=1.0,
        )

        agents["inquisitor"] = Agent(
            name="inquisitor",
            instructions="Research specialist. Investigate topics thoroughly, gather information, and provide detailed findings.",
            model="gpt-5.2",
            provider="openai",
            temperature=0.8,
        )

        agents["rimor"] = Agent(
            name="rimor",
            instructions="Precision explorer. Find exact information quickly and accurately.",
            model="gpt-5.2",
            provider="openai",
            temperature=0.7,
        )

        agents["creativus"] = Agent(
            name="creativus",
            instructions="Creative specialist. Generate innovative ideas and approaches.",
            model="gpt-5.2",
            provider="openai",
            temperature=1.2,
        )

        agents["artifex"] = Agent(
            name="artifex",
            instructions="Artistic craftsman. Create aesthetic and visually pleasing outputs.",
            model="gpt-5.2",
            provider="openai",
            temperature=1.1,
        )

    if "anthropic" in providers:
        agents["peritus"] = Agent(
            name="peritus",
            instructions="Professional expert. Handle complex professional tasks with expertise and precision.",
            model="claude-sonnet-4-6",
            provider="anthropic",
            temperature=0.9,
        )

        agents["recensor"] = Agent(
            name="recensor",
            instructions="Quality reviewer. Review work critically, verify facts, and ensure excellence.",
            model="claude-sonnet-4-6",
            provider="anthropic",
            temperature=0.6,
        )

    if "google" in providers:
        agents["cogitator"] = Agent(
            name="cogitator",
            instructions="Deep thinker. Contemplate complex problems deeply and provide thoughtful analysis.",
            model="gemini-3.1-pro",
            provider="google",
            temperature=1.0,
        )

    if "local" in providers:
        agents["local_fallback"] = Agent(
            name="local_fallback",
            instructions="Local fallback agent. Handle tasks when other providers are unavailable.",
            model="llama3",
            provider="local",
            temperature=0.8,
        )

    return agents


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


DEFAULT_TOOLS = [
    search_web,
    read_file,
    write_file,
    run_bash,
    search_code,
]
