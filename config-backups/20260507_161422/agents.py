import os
import sys
import json
import subprocess
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import AgentSession
from app.schemas import AgentChatRequest, SwarmRequest
from app.config import settings
from app.routers.billing import record_ai_usage

router = APIRouter()

AGENT_HOME = Path("/Users/gt/Public/MyFiles/agent-home")
SWARM_PY = AGENT_HOME / "swarm/swarm.py"
PYTHON = Path.home() / ".hermes/hermes-agent/venv/bin/python"


def _prepare_agent_env():
    """Build env dict for swarm.py using the active dashboard AI config."""
    env = os.environ.copy()
    # Generic dashboard AI settings (set via Models page)
    if settings.DASHBOARD_AI_API_KEY:
        env["DASHBOARD_AI_API_KEY"] = settings.DASHBOARD_AI_API_KEY
    if settings.DASHBOARD_AI_BASE_URL:
        env["DASHBOARD_AI_BASE_URL"] = settings.DASHBOARD_AI_BASE_URL
    if settings.DASHBOARD_AI_MODEL:
        env["DASHBOARD_AI_MODEL"] = settings.DASHBOARD_AI_MODEL
    if settings.DASHBOARD_AI_PROVIDER:
        env["DASHBOARD_AI_PROVIDER"] = settings.DASHBOARD_AI_PROVIDER
    # Legacy KIMI fallback so old swarm.py still works if not updated
    if settings.KIMI_API_KEY:
        env["KIMI_API_KEY"] = settings.KIMI_API_KEY
    if settings.KIMI_BASE_URL:
        env["KIMI_BASE_URL"] = settings.KIMI_BASE_URL
    return env


def _api_key_is_set() -> bool:
    return bool(settings.DASHBOARD_AI_API_KEY or settings.KIMI_API_KEY)

AGENTS = [
    {"name": "cto", "role": "Chief Technology Officer", "icon": "Cpu", "tab": "projects"},
    {"name": "cfo", "role": "Chief Financial Officer", "icon": "DollarSign", "tab": "finance"},
    {"name": "coo", "role": "Chief Operations Officer", "icon": "ClipboardList", "tab": "health"},
    {"name": "cmo", "role": "Chief Marketing Officer", "icon": "TrendingUp", "tab": "obsidian"},
    {"name": "architect", "role": "Software Architect", "icon": "Building2", "tab": "projects"},
    {"name": "researcher", "role": "Deep Research Agent", "icon": "Search", "tab": "obsidian"},
    {"name": "reviewer", "role": "Code Reviewer", "icon": "ShieldCheck", "tab": "projects"},
    {"name": "pi", "role": "AI Coder (pi.dev)", "icon": "Code", "tab": "projects"},
]


@router.get("", response_model=List[dict])
@router.get("/", response_model=List[dict])
def list_agents():
    return AGENTS


@router.post("/{name}/chat")
def chat_with_agent(name: str, req: AgentChatRequest, db: Session = Depends(get_db)):
    if name not in [a["name"] for a in AGENTS]:
        raise HTTPException(status_code=404, detail="Agent not found")

    env = _prepare_agent_env()

    if not _api_key_is_set():
        raise HTTPException(status_code=500, detail="No AI API key configured. Set one in Models page.")

    # Save user message
    db.add(AgentSession(agent_name=name, role="user", message=req.message))
    db.commit()

    import time as _time
    start_ms = int(_time.time() * 1000)
    try:
        result = subprocess.run(
            [str(PYTHON), str(SWARM_PY), "--agent", name, req.message],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        output = result.stdout.strip() or result.stderr.strip()
        status = "success" if result.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        status = "timeout"
        raise HTTPException(status_code=504, detail="Agent timeout")
    except Exception as e:
        status = "error"
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        elapsed = int(_time.time() * 1000) - start_ms
        # Record usage
        provider = settings.DASHBOARD_AI_PROVIDER or "kimi"
        model = settings.DASHBOARD_AI_MODEL or "kimi-k2.6"
        api_key_env = "KIMI_API_KEY"
        if provider == "kimi-coding":
            api_key_env = "KIMI_CODE_API_KEY"
        elif provider == "openrouter":
            api_key_env = "OPENROUTER_API_KEY"
        elif provider == "openai":
            api_key_env = "OPENAI_API_KEY"
        elif provider == "anthropic":
            api_key_env = "ANTHROPIC_API_KEY"
        record_ai_usage(
            db=db,
            provider=provider,
            api_key_env=api_key_env,
            model=model,
            endpoint="/agents/{name}/chat",
            request_status=status,
            response_ms=elapsed,
            source_system="dashboard",
        )

    # Save agent response
    db.add(AgentSession(agent_name=name, role="agent", message=output))
    db.commit()

    return {"agent": name, "response": output}


@router.post("/swarm")
def run_swarm(req: SwarmRequest, db: Session = Depends(get_db)):
    env = _prepare_agent_env()

    if not _api_key_is_set():
        raise HTTPException(status_code=500, detail="No AI API key configured. Set one in Models page.")

    import time as _time
    start_ms = int(_time.time() * 1000)
    try:
        result = subprocess.run(
            [str(PYTHON), str(SWARM_PY), "--swarm", req.message],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        output = result.stdout.strip() or result.stderr.strip()
        status = "success" if result.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        status = "timeout"
        raise HTTPException(status_code=504, detail="Swarm timeout")
    except Exception as e:
        status = "error"
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        elapsed = int(_time.time() * 1000) - start_ms
        provider = settings.DASHBOARD_AI_PROVIDER or "kimi"
        model = settings.DASHBOARD_AI_MODEL or "kimi-k2.6"
        api_key_env = "KIMI_API_KEY"
        if provider == "kimi-coding":
            api_key_env = "KIMI_CODE_API_KEY"
        elif provider == "openrouter":
            api_key_env = "OPENROUTER_API_KEY"
        elif provider == "openai":
            api_key_env = "OPENAI_API_KEY"
        elif provider == "anthropic":
            api_key_env = "ANTHROPIC_API_KEY"
        record_ai_usage(
            db=db,
            provider=provider,
            api_key_env=api_key_env,
            model=model,
            endpoint="/agents/swarm",
            request_status=status,
            response_ms=elapsed,
            source_system="dashboard",
        )

    return {"response": output}


@router.get("/{name}/history", response_model=List[dict])
def agent_history(name: str, limit: int = 50, db: Session = Depends(get_db)):
    sessions = (
        db.query(AgentSession)
        .filter(AgentSession.agent_name == name)
        .order_by(AgentSession.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "role": s.role,
            "message": s.message,
            "timestamp": s.timestamp.isoformat() if s.timestamp else None,
        }
        for s in reversed(sessions)
    ]
