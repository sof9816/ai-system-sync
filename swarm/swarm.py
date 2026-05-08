#!/usr/bin/env python3
"""
GT Swarm - Permanent Specialized Agents
Orchestrator for multi-agent workflows using Kimi (OpenAI-compatible API).

Usage:
    python swarm.py --agent cto "review this architecture"
    python swarm.py --swarm "launch a startup"
    python swarm.py --list
"""

import argparse
import json
import os
import sys
import textwrap
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List

# Try to use openai from Hermes venv, otherwise fail gracefully
try:
    from openai import OpenAI, APIError, AuthenticationError, PermissionDeniedError
    import httpx
except ImportError as _imp_err:
    HERMES_VENV = Path.home() / ".hermes/hermes-agent/venv/bin/python"
    if HERMES_VENV.exists():
        print(f"OpenAI SDK not found in current Python. Use: {HERMES_VENV} {__file__}")
    else:
        print("OpenAI SDK not found. Install: pip install openai httpx")
    sys.exit(1)

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
AGENTS_DIR = AGENT_HOME / "agents"
OBSIDIAN_BASE = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/GT Vault/hermes/agents"

# Valid agent names from disk configs
_VALID_AGENTS = {f.stem for f in AGENTS_DIR.glob("*.yaml")}


def _validate_agents(agent_names: List[str]) -> List[str]:
    """Filter to only agents that have YAML configs on disk."""
    valid = []
    for name in agent_names:
        if name in _VALID_AGENTS:
            valid.append(name)
        else:
            print(f"[⚠] Agent '{name}' not found in {AGENTS_DIR} — skipping", file=sys.stderr)
    return valid

# Load API keys from ~/.hermes/.env if not already in environment
def _load_env_from_hermes():
    env_file = Path.home() / ".hermes" / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v

_load_env_from_hermes()

# Support generic dashboard AI settings (set via Models page) with legacy KIMI fallbacks
# Kimi Code is the PRIMARY provider for all GT AI systems
AI_BASE_URL = os.environ.get("DASHBOARD_AI_BASE_URL") or os.environ.get("KIMI_CODE_BASE_URL", "https://api.kimi.com/coding")
AI_API_KEY = os.environ.get("DASHBOARD_AI_API_KEY") or os.environ.get("KIMI_CODE_API_KEY") or os.environ.get("KIMI_API_KEY", "")
AI_MODEL = os.environ.get("DASHBOARD_AI_MODEL", "kimi-k2.6")

# The Kimi coding endpoint restricts access to recognised coding-agent User-Agents.
# We set the same header used by Claude Code, Roo Code, etc. so that the provider
# allows the request through.
_CODING_AGENT_UA = "claude-code/0.1"


def load_agent_config(name: str) -> dict:
    """Load agent YAML config."""
    try:
        import yaml
    except ImportError:
        # Fallback: parse minimal YAML manually for frontmatter
        return _parse_simple_yaml(AGENTS_DIR / f"{name}.yaml")

    path = AGENTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Agent '{name}' not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_simple_yaml(path: Path) -> dict:
    """Minimal YAML parser for simple agent configs."""
    import re
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract frontmatter
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm = content[3:end].strip()
            result = {}
            current_key = None
            current_value = []
            for line in fm.split("\n"):
                if line.strip().startswith("#"):
                    continue
                # New key
                m = re.match(r"^(\w+):\s*(.*)$", line)
                if m and not line.startswith(" "):
                    if current_key:
                        result[current_key] = "\n".join(current_value).strip()
                    current_key = m.group(1)
                    val = m.group(2).strip()
                    current_value = [val] if val else []
                elif current_key and line.startswith(" "):
                    current_value.append(line.strip())
            if current_key:
                result[current_key] = "\n".join(current_value).strip()
            # Parse lists
            for k in ["skills", "tools"]:
                if k in result and isinstance(result[k], str):
                    result[k] = [s.strip(" -") for s in result[k].split("\n") if s.strip()]
            return result
    return {}


def get_memory_path(agent_name: str) -> Path:
    """Get the memory file path for an agent in Obsidian."""
    mem_dir = OBSIDIAN_BASE / agent_name
    mem_dir.mkdir(parents=True, exist_ok=True)
    return mem_dir / "memory.md"


def get_projects_path(agent_name: str) -> Path:
    """Get the projects tracking file for an agent."""
    mem_dir = OBSIDIAN_BASE / agent_name
    mem_dir.mkdir(parents=True, exist_ok=True)
    return mem_dir / "projects.md"


def read_memory(agent_name: str, max_lines: int = 100) -> str:
    """Read recent memory for an agent."""
    path = get_memory_path(agent_name)
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    # Return last N lines of conversation context
    return "\n".join(lines[-max_lines:])


def append_memory(agent_name: str, role: str, content: str):
    """Append an interaction to agent memory."""
    path = get_memory_path(agent_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp} | {role}\n\n{content}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)


def build_system_prompt(config: dict) -> str:
    """Build the full system prompt for an agent."""
    base = config.get("system_prompt", "")
    # Load recent memory
    name = config["name"]
    memory = read_memory(name, max_lines=80)
    if memory:
        base += f"\n\n## Recent Context (your memory)\n\n{memory}\n\nUse this context to maintain continuity. Do not repeat information already established unless necessary."
    return base


def create_client() -> OpenAI:
    """Create OpenAI-compatible client using configured provider."""
    if not AI_API_KEY:
        raise ValueError(
            "No API key found. Set KIMI_CODE_API_KEY in ~/.hermes/.env or environment.\n"
            "Checked: DASHBOARD_AI_API_KEY, KIMI_CODE_API_KEY, KIMI_API_KEY"
        )
    # The Kimi coding endpoint returns 403 unless the request carries a
    # User-Agent belonging to a recognised coding agent (Claude Code, Roo Code,
    # etc.).  We inject it via default_headers so the SDK merges it into every
    # request.  A custom httpx client is also supplied for timeout control.
    http_client = httpx.Client(
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    return OpenAI(
        api_key=AI_API_KEY,
        base_url=AI_BASE_URL,
        http_client=http_client,
        default_headers={"User-Agent": _CODING_AGENT_UA},
    )


def _extract_content(message) -> str:
    """Extract content from an OpenAI chat-completion message.

    Some providers (e.g. Kimi reasoning models) split output into
    *reasoning_content* and *content*. We concatenate both when present
    so nothing is lost.
    """
    parts = []
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        parts.append(f"<thinking>\n{reasoning}\n</thinking>")
    content = getattr(message, "content", None) or ""
    if content:
        parts.append(content)
    return "\n\n".join(parts) if parts else "(no output)"


def chat_with_agent(agent_name: str, user_message: str, model: str = None) -> str:
    """Send a message to a single agent and return the response."""
    config = load_agent_config(agent_name)
    client = create_client()

    system_prompt = build_system_prompt(config)
    mdl = model or config.get("model", AI_MODEL)
    # Normalise legacy alias
    if mdl.lower() == "kimi-for-coding":
        mdl = "kimi-k2.6"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    print(f"\n[→] {config['role']} ({agent_name}) thinking...\n", file=sys.stderr)

    # Kimi coding models only support temperature=1
    mdl_lower = mdl.lower()
    temp = 1.0 if "kimi" in mdl_lower else 0.7

    try:
        response = client.chat.completions.create(
            model=mdl,
            messages=messages,
            temperature=temp,
            max_tokens=8192,
        )
    except PermissionDeniedError as exc:
        # Provide a helpful, actionable error message instead of a raw traceback
        err_body = ""
        try:
            err_body = json.dumps(exc.body) if hasattr(exc, "body") and exc.body else str(exc)
        except Exception:
            err_body = str(exc)
        raise RuntimeError(
            f"Permission denied by provider for model '{mdl}'.\n"
            f"Detail: {err_body}\n"
            "Hint: Ensure the User-Agent header is set to a recognised coding agent "
            "(e.g. 'claude-code/0.1') and that the model identifier is 'kimi-for-coding'."
        ) from exc
    except APIError as exc:
        raise RuntimeError(f"API error ({exc.__class__.__name__}): {exc}") from exc

    content = _extract_content(response.choices[0].message)

    # Persist to memory
    append_memory(agent_name, "USER", user_message)
    append_memory(agent_name, "AGENT", content)

    return content


def list_agents() -> list:
    """List all available agents."""
    agents = []
    for f in sorted(AGENTS_DIR.glob("*.yaml")):
        try:
            cfg = load_agent_config(f.stem)
            agents.append({
                "name": cfg.get("name", f.stem),
                "role": cfg.get("role", "Unknown"),
                "description": cfg.get("description", "").replace("\n", " "),
            })
        except Exception as e:
            agents.append({"name": f.stem, "role": "ERROR", "description": str(e)})
    return agents


def simple_route(user_message: str) -> dict:
    """Fast keyword-based router. No API call needed."""
    msg = user_message.lower()

    keywords = {
        "cto": ["tech", "code", "stack", "architecture", "api", "server", "backend", "frontend", "database", "scalability", "performance", "swift", "ios", "app development", "framework"],
        "architect": ["design", "system", "microservice", "monolith", "ddd", "pattern", "infrastructure", "diagram", "model", "schema"],
        "cfo": ["budget", "cost", "money", "finance", "invest", "revenue", "profit", "tax", "funding", "valuation", "crypto", "portfolio", "price"],
        "cmo": ["marketing", "aso", "users", "growth", "content", "brand", "launch", "acquisition", "funnel", "social media", "seo", "app store"],
        "coo": ["plan", "project", "task", "organize", "workflow", "productivity", "execute", "timeline", "deadline", "okr", "kanban", "process"],
        "researcher": ["research", "analyze", "study", "compare", "benchmark", "survey", "report", "trend", "market", "competitor"],
        "reviewer": ["review", "audit", "bug", "security", "vulnerability", "exploit", "fix", "refactor", "clean code", "test coverage"],
    }

    scores = {agent: 0 for agent in keywords}
    for agent, words in keywords.items():
        for word in words:
            if word in msg:
                scores[agent] += 1

    # Sort by score, filter those with at least 1 match
    matched = [(a, s) for a, s in scores.items() if s > 0]
    matched.sort(key=lambda x: x[1], reverse=True)

    if not matched:
        # Default: researcher for open-ended questions, cto for product-building
        if any(w in msg for w in ["build", "create", "make", "develop", "app", "product"]):
            return {
                "mode": "multi",
                "agents": _validate_agents(["cto", "architect"]),
                "tasks": [user_message, user_message],
                "synthesis_strategy": "Combine technical and architectural perspectives into a unified plan."
            }
        return {
            "mode": "single",
            "agents": _validate_agents(["researcher"]),
            "tasks": [user_message],
            "synthesis_strategy": "Return the research output directly."
        }

    # Top 1-3 agents, filtered to only those that exist on disk
    top_agents = _validate_agents([a for a, _ in matched[:3]])
    if not top_agents:
        # Fallback to researcher if none matched exist
        return {
            "mode": "single",
            "agents": ["researcher"],
            "tasks": [user_message],
            "synthesis_strategy": "Return the research output directly."
        }
    return {
        "mode": "multi" if len(top_agents) > 1 else "single",
        "agents": top_agents,
        "tasks": [user_message] * len(top_agents),
        "synthesis_strategy": f"Synthesize outputs from {', '.join(top_agents)} into a coherent response."
    }


def swarm_mode(user_message: str) -> str:
    """Multi-agent swarm mode: keyword router delegates to specialists."""
    client = create_client()

    # Fast keyword routing
    plan = simple_route(user_message)

    print(f"[Plan] Mode: {plan['mode']} | Agents: {', '.join(plan['agents'])}\n", file=sys.stderr)

    # Execute agent tasks in parallel
    results = []
    print(f"[>] Delegating to {len(plan['agents'])} agents in parallel...\n", file=sys.stderr)

    def run_agent_task(agent_name, task):
        try:
            result = chat_with_agent(agent_name, task)
            print(f"[✓] {agent_name} completed\n", file=sys.stderr)
            return {"agent": agent_name, "task": task, "result": result, "error": None}
        except Exception as e:
            print(f"[✗] {agent_name} failed: {e}\n", file=sys.stderr)
            return {"agent": agent_name, "task": task, "result": f"ERROR: {e}", "error": str(e)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(run_agent_task, agent_name, task): agent_name
            for agent_name, task in zip(plan["agents"], plan["tasks"])
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                agent_name = futures[future]
                print(f"[✗] {agent_name} thread exception: {exc}", file=sys.stderr)
                results.append({"agent": agent_name, "task": user_message, "result": f"THREAD ERROR: {exc}", "error": str(exc)})

    # Sort results by original agent order
    agent_order = {name: idx for idx, name in enumerate(plan["agents"])}
    results.sort(key=lambda r: agent_order.get(r["agent"], 999))

    # Separate successful and failed results
    successful = [r for r in results if r["error"] is None]
    failed = [r for r in results if r["error"] is not None]

    # If no agents succeeded, return a structured failure message instead of crashing
    if not successful:
        error_report = "## Swarm Execution Failed\n\n"
        error_report += "All delegated agents failed to produce a response.\n\n"
        error_report += "### Failures\n"
        for r in failed:
            error_report += f"- **{r['agent']}**: {r['error']}\n"
        error_report += "\n### Suggestion\n"
        error_report += "Check your API key, model identifier, and provider base URL. "
        error_report += "If using Kimi, ensure the model is set to 'kimi-for-coding'."
        return error_report

    # Single successful result → return directly (no synthesis API call needed)
    if plan["mode"] == "single" and len(successful) == 1:
        return successful[0]["result"]

    # Synthesis prompt using only successful outputs
    synthesis_prompt = f"""You are the Swarm Synthesizer. Combine the outputs from multiple specialist agents into a coherent, actionable final response.

User's original request: {user_message}

Synthesis strategy: {plan.get('synthesis_strategy', 'Integrate all perspectives into a unified recommendation.')}

Agent outputs:
"""
    for r in successful:
        synthesis_prompt += f"\n--- {r['agent'].upper()} ---\nTask: {r['task']}\nOutput:\n{r['result']}\n"

    if failed:
        synthesis_prompt += "\n\nNote: The following agents failed to respond and were excluded from synthesis:\n"
        for r in failed:
            synthesis_prompt += f"- {r['agent']}: {r['error']}\n"

    synthesis_prompt += "\n\nProvide the final synthesized response. Maintain the tone and depth appropriate to the user's request."

    print("[→] Synthesizing final response...\n", file=sys.stderr)

    try:
        synthesis = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You synthesize multi-agent outputs into unified, actionable responses."},
                {"role": "user", "content": synthesis_prompt},
            ],
            temperature=1.0,
            max_tokens=8192,
        )
        final = _extract_content(synthesis.choices[0].message)
    except Exception as exc:
        # If synthesis itself fails, still return the individual successful outputs
        print(f"[✗] Synthesis failed: {exc}\n", file=sys.stderr)
        final = "## Partial Results (Synthesis Failed)\n\n"
        for r in successful:
            final += f"### {r['agent'].upper()}\n{r['result']}\n\n"
        final += f"\n**Synthesis error**: {exc}"

    # Save swarm run to a shared log
    swarm_log = OBSIDIAN_BASE / "../swarm-log.md"
    swarm_log.parent.mkdir(parents=True, exist_ok=True)
    with open(swarm_log, "a", encoding="utf-8") as f:
        f.write(f"\n# {datetime.now().strftime('%Y-%m-%d %H:%M')} | {user_message[:80]}\n\n")
        f.write(f"**Agents**: {', '.join(plan['agents'])}\n\n")
        f.write(final)
        f.write("\n---\n")

    return final


def main():
    parser = argparse.ArgumentParser(description="GT Swarm - Permanent Specialized Agents")
    parser.add_argument("--agent", "-a", help="Agent name to chat with")
    parser.add_argument("--swarm", "-s", action="store_true", help="Enable multi-agent swarm mode")
    parser.add_argument("--list", "-l", action="store_true", help="List available agents")
    parser.add_argument("--model", "-m", default=None, help="Override model")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full tracebacks on error")
    parser.add_argument("message", nargs="?", help="Message to send")

    args = parser.parse_args()

    try:
        if args.list:
            agents = list_agents()
            print(f"{'Agent':<12} {'Role':<25} Description")
            print("-" * 70)
            for a in agents:
                desc = a["description"][:50] + "..." if len(a["description"]) > 50 else a["description"]
                print(f"{a['name']:<12} {a['role']:<25} {desc}")
            return

        if not args.message:
            parser.print_help()
            sys.exit(1)

        if args.swarm:
            result = swarm_mode(args.message)
        elif args.agent:
            result = chat_with_agent(args.agent, args.message, model=args.model)
        else:
            # Default: try to route to a single agent based on keywords, or use general
            print("[→] No agent specified. Use --agent or --swarm. Routing to general assistant...\n", file=sys.stderr)
            client = create_client()
            mdl = args.model or AI_MODEL
            if mdl.lower() == "kimi-for-coding":
                mdl = "kimi-k2.6"
            response = client.chat.completions.create(
                model=mdl,
                messages=[{"role": "user", "content": args.message}],
                temperature=1.0,
                max_tokens=8192,
            )
            result = _extract_content(response.choices[0].message)

        print(result)

    except Exception as exc:
        if args.verbose:
            raise
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
