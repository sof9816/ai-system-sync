import os
import httpx
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database import get_db
from app.models import APIUsageRecord, APIBalanceSnapshot
from app.schemas import APIUsageRecordResponse, APIBalanceSnapshotResponse, UsageSummary, AllBalancesResponse
from app.config import settings

router = APIRouter()
HERMES_HOME = Path.home() / ".hermes"

# ---------------------------------------------------------------------------
# Helper: mask API key
# ---------------------------------------------------------------------------
def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "****"
    return key[:8] + "..." + key[-4:]

# ---------------------------------------------------------------------------
# Helper: resolve all configured API keys from env
# ---------------------------------------------------------------------------
def _get_all_api_keys() -> List[Dict[str, str]]:
    """Discover all API keys from environment and config files."""
    keys = []
    
    # Primary keys we know about
    key_configs = [
        ("kimi", "KIMI_API_KEY", "https://api.moonshot.ai/v1", "Kimi / Moonshot"),
        ("kimi-coding", "KIMI_CODE_API_KEY", "https://api.kimi.com/coding", "Kimi Code"),
        ("openrouter", "OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "OpenRouter"),
        ("openai", "OPENAI_API_KEY", "https://api.openai.com/v1", "OpenAI"),
        ("anthropic", "ANTHROPIC_API_KEY", "https://api.anthropic.com/v1", "Anthropic"),
        ("google", "GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai", "Google Gemini"),
        ("ollama", "OLLAMA_API_KEY", "http://localhost:11434/v1", "Ollama"),
        ("glm", "GLM_API_KEY", "https://api.z.ai/api/paas/v4", "GLM"),
        ("deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "DeepSeek"),
        ("minimax", "MINIMAX_API_KEY", "https://api.minimax.io/v1", "MiniMax"),
        ("qwen", "QWEN_API_KEY", "https://portal.qwen.ai/v1", "Qwen"),
    ]
    
    for provider, env_name, default_url, label in key_configs:
        key = os.environ.get(env_name, "")
        # Also check settings (which reads from ~/.hermes/.env)
        if not key:
            key = getattr(settings, env_name, "")
        # Also check backend .env
        if not key:
            backend_env_path = settings.AGENT_HOME / "dashboard" / "backend" / ".env"
            if backend_env_path.exists():
                with open(backend_env_path) as f:
                    for line in f:
                        if line.strip().startswith(f"{env_name}="):
                            key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                            break
        
        # Fallback: check ~/.hermes/.env for old kimi key
        if not key and env_name == "KIMI_API_KEY":
            hermes_env = HERMES_HOME / ".env"
            if hermes_env.exists():
                with open(hermes_env) as f:
                    for line in f:
                        if line.strip().startswith("KIMI_API_KEY="):
                            key = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                            break
        
        if key:
            # Check for custom base URL override
            base_url_env = f"{provider.upper().replace('-', '_')}_BASE_URL"
            base_url = os.environ.get(base_url_env, "")
            if not base_url:
                base_url = getattr(settings, base_url_env, "")
            if not base_url:
                base_url = default_url
            
            keys.append({
                "provider": provider,
                "env_name": env_name,
                "api_key": key,
                "base_url": base_url,
                "label": label,
            })
    
    return keys

# ---------------------------------------------------------------------------
# Helper: check balance for a single provider
# ---------------------------------------------------------------------------
async def _check_provider_balance(provider: str, api_key: str, base_url: str) -> Dict[str, Any]:
    """Check balance for a specific provider."""
    
    # Kimi / Moonshot balance endpoint (old platform only)
    if provider == "kimi":
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{base_url.rstrip('/')}/users/me/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw = data.get("data", {})
                    balance = raw.get("available_balance") or raw.get("cash_balance") or 0
                    return {
                        "status": "ok",
                        "balance": balance,
                        "currency": "USD",
                        "cash_balance": raw.get("cash_balance"),
                        "voucher_balance": raw.get("voucher_balance"),
                        "raw": data,
                    }
                elif resp.status_code == 401:
                    return {"status": "error", "message": "Invalid API key (401)", "balance": None}
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}", "balance": None, "raw": resp.text[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e), "balance": None}

    # Kimi Code API — no balance endpoint, test with /models
    elif provider == "kimi-coding":
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    model_count = len(data.get("data", [])) if isinstance(data, dict) else 0
                    return {
                        "status": "ok",
                        "balance": None,
                        "currency": "USD",
                        "message": f"API key valid — {model_count} models available (balance endpoint not available on coding API)",
                        "raw": data,
                    }
                elif resp.status_code == 401:
                    return {"status": "error", "message": "Invalid API key (401)", "balance": None}
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}", "balance": None, "raw": resp.text[:200]}
        except Exception as e:
            return {"status": "error", "message": str(e), "balance": None}
    
    # OpenRouter has a credits endpoint
    elif provider == "openrouter":
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    "https://openrouter.ai/api/v1/credits",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    credits = data.get("data", {}).get("total_credits", 0)
                    usage = data.get("data", {}).get("total_usage", 0)
                    return {
                        "status": "ok",
                        "balance": credits - usage,
                        "currency": "USD",
                        "cash_balance": credits,
                        "voucher_balance": None,
                        "raw": data,
                    }
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}", "balance": None}
        except Exception as e:
            return {"status": "error", "message": str(e), "balance": None}
    
    # DeepSeek has a user balance endpoint
    elif provider == "deepseek":
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{base_url.rstrip('/')}/user/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    balance = data.get("balance_infos", [{}])[0].get("total_balance", 0)
                    return {
                        "status": "ok",
                        "balance": balance,
                        "currency": "USD",
                        "raw": data,
                    }
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}", "balance": None}
        except Exception as e:
            return {"status": "error", "message": str(e), "balance": None}
    
    # Generic: try /models as a connectivity test (no balance info)
    else:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{base_url.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    return {
                        "status": "ok",
                        "balance": None,
                        "currency": "USD",
                        "message": "API key valid (balance endpoint not available for this provider)",
                    }
                elif resp.status_code == 401:
                    return {"status": "error", "message": "Invalid API key (401)", "balance": None}
                else:
                    return {"status": "error", "message": f"HTTP {resp.status_code}", "balance": None}
        except Exception as e:
            return {"status": "error", "message": str(e), "balance": None}


# ---------------------------------------------------------------------------
# POST /usage — record a usage event
# ---------------------------------------------------------------------------
class RecordUsageRequest(BaseModel):
    provider: str
    api_key_env: str
    endpoint: Optional[str] = None
    model: Optional[str] = None
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    cost_usd: Optional[float] = None
    request_status: str = "success"
    response_ms: Optional[int] = None
    source_system: Optional[str] = None


@router.post("/usage")
def record_usage(req: RecordUsageRequest, db: Session = Depends(get_db)):
    """Record an API usage event. Called by pi, hermes, or dashboard when making API calls."""
    api_key = os.environ.get(req.api_key_env, "") or getattr(settings, req.api_key_env, "")
    masked = _mask_key(api_key) if api_key else "unknown"
    
    record = APIUsageRecord(
        provider=req.provider,
        api_key_env=req.api_key_env,
        api_key_masked=masked,
        endpoint=req.endpoint,
        model=req.model,
        tokens_input=req.tokens_input,
        tokens_output=req.tokens_output,
        tokens_total=req.tokens_total or (req.tokens_input + req.tokens_output),
        cost_usd=req.cost_usd,
        request_status=req.request_status,
        response_ms=req.response_ms,
        source_system=req.source_system,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"recorded": True, "id": record.id}


# ---------------------------------------------------------------------------
# Helper: record usage from other routers
# ---------------------------------------------------------------------------
def record_ai_usage(
    db: Session,
    provider: str,
    api_key_env: str,
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
    tokens_input: int = 0,
    tokens_output: int = 0,
    cost_usd: Optional[float] = None,
    request_status: str = "success",
    response_ms: Optional[int] = None,
    source_system: Optional[str] = None,
):
    """Record an AI usage event from any router."""
    api_key = os.environ.get(api_key_env, "") or getattr(settings, api_key_env, "")
    masked = _mask_key(api_key) if api_key else "unknown"
    record = APIUsageRecord(
        provider=provider,
        api_key_env=api_key_env,
        api_key_masked=masked,
        endpoint=endpoint,
        model=model,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        tokens_total=tokens_input + tokens_output,
        cost_usd=cost_usd,
        request_status=request_status,
        response_ms=response_ms,
        source_system=source_system,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# GET /balance — check ALL configured API keys
# ---------------------------------------------------------------------------
@router.get("/balance")
async def get_all_balances(db: Session = Depends(get_db)):
    """Check balance for ALL configured API keys across all providers."""
    keys = _get_all_api_keys()
    checked_at = datetime.utcnow()
    
    accounts = []
    for cfg in keys:
        start = time.time()
        result = await _check_provider_balance(cfg["provider"], cfg["api_key"], cfg["base_url"])
        elapsed = int((time.time() - start) * 1000)
        
        masked = _mask_key(cfg["api_key"])
        
        # Save snapshot to DB
        snapshot = APIBalanceSnapshot(
            provider=cfg["provider"],
            api_key_env=cfg["env_name"],
            api_key_masked=masked,
            balance=result.get("balance"),
            currency=result.get("currency", "USD"),
            cash_balance=result.get("cash_balance"),
            voucher_balance=result.get("voucher_balance"),
            status=result["status"],
            error_message=result.get("message") if result["status"] != "ok" else None,
            checked_at=checked_at,
        )
        db.add(snapshot)
        
        accounts.append({
            "provider": cfg["provider"],
            "label": cfg["label"],
            "api_key_env": cfg["env_name"],
            "api_key_masked": masked,
            "base_url": cfg["base_url"],
            "balance": result.get("balance"),
            "currency": result.get("currency", "USD"),
            "cash_balance": result.get("cash_balance"),
            "voucher_balance": result.get("voucher_balance"),
            "status": result["status"],
            "message": result.get("message"),
            "response_ms": elapsed,
        })
    
    db.commit()
    
    # Summary
    total_balance = sum(a["balance"] or 0 for a in accounts)
    active_keys = sum(1 for a in accounts if a["status"] == "ok")
    error_keys = sum(1 for a in accounts if a["status"] == "error")
    
    return {
        "checked_at": checked_at.isoformat(),
        "accounts": accounts,
        "summary": {
            "total_accounts": len(accounts),
            "active_keys": active_keys,
            "error_keys": error_keys,
            "total_balance_usd": round(total_balance, 4),
            "providers_checked": list(set(a["provider"] for a in accounts)),
        },
    }


# ---------------------------------------------------------------------------
# GET /usage/summary — daily/weekly/monthly usage per key
# ---------------------------------------------------------------------------
@router.get("/usage/summary")
def get_usage_summary(db: Session = Depends(get_db)):
    """Get usage summary grouped by provider/api_key_env for today, this week, this month."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)
    
    # Get all distinct provider+key combos that have records
    combos = db.query(
        APIUsageRecord.provider,
        APIUsageRecord.api_key_env,
        APIUsageRecord.api_key_masked,
    ).distinct().all()
    
    summaries = []
    for provider, env_name, masked in combos:
        # Today
        today_stats = db.query(
            func.coalesce(func.sum(APIUsageRecord.tokens_total), 0).label("tokens"),
            func.count(APIUsageRecord.id).label("requests"),
            func.coalesce(func.sum(APIUsageRecord.cost_usd), 0.0).label("cost"),
        ).filter(
            and_(
                APIUsageRecord.provider == provider,
                APIUsageRecord.api_key_env == env_name,
                APIUsageRecord.created_at >= today_start,
            )
        ).first()
        
        # This week
        week_stats = db.query(
            func.coalesce(func.sum(APIUsageRecord.tokens_total), 0).label("tokens"),
            func.count(APIUsageRecord.id).label("requests"),
            func.coalesce(func.sum(APIUsageRecord.cost_usd), 0.0).label("cost"),
        ).filter(
            and_(
                APIUsageRecord.provider == provider,
                APIUsageRecord.api_key_env == env_name,
                APIUsageRecord.created_at >= week_start,
            )
        ).first()
        
        # This month
        month_stats = db.query(
            func.coalesce(func.sum(APIUsageRecord.tokens_total), 0).label("tokens"),
            func.count(APIUsageRecord.id).label("requests"),
            func.coalesce(func.sum(APIUsageRecord.cost_usd), 0.0).label("cost"),
        ).filter(
            and_(
                APIUsageRecord.provider == provider,
                APIUsageRecord.api_key_env == env_name,
                APIUsageRecord.created_at >= month_start,
            )
        ).first()
        
        # All time
        total_stats = db.query(
            func.coalesce(func.sum(APIUsageRecord.tokens_total), 0).label("tokens"),
            func.count(APIUsageRecord.id).label("requests"),
            func.coalesce(func.sum(APIUsageRecord.cost_usd), 0.0).label("cost"),
        ).filter(
            and_(
                APIUsageRecord.provider == provider,
                APIUsageRecord.api_key_env == env_name,
            )
        ).first()
        
        summaries.append({
            "provider": provider,
            "api_key_env": env_name,
            "api_key_masked": masked,
            "today_tokens": int(today_stats.tokens or 0),
            "today_requests": int(today_stats.requests or 0),
            "today_cost": round(float(today_stats.cost or 0), 4),
            "week_tokens": int(week_stats.tokens or 0),
            "week_requests": int(week_stats.requests or 0),
            "week_cost": round(float(week_stats.cost or 0), 4),
            "month_tokens": int(month_stats.tokens or 0),
            "month_requests": int(month_stats.requests or 0),
            "month_cost": round(float(month_stats.cost or 0), 4),
            "total_tokens": int(total_stats.tokens or 0),
            "total_requests": int(total_stats.requests or 0),
            "total_cost": round(float(total_stats.cost or 0), 4),
        })
    
    # Also include keys that have balance snapshots but no usage yet
    balance_keys = db.query(
        APIBalanceSnapshot.provider,
        APIBalanceSnapshot.api_key_env,
        APIBalanceSnapshot.api_key_masked,
    ).distinct().all()
    
    existing = set((s["provider"], s["api_key_env"]) for s in summaries)
    for provider, env_name, masked in balance_keys:
        if (provider, env_name) not in existing:
            summaries.append({
                "provider": provider,
                "api_key_env": env_name,
                "api_key_masked": masked,
                "today_tokens": 0,
                "today_requests": 0,
                "today_cost": 0.0,
                "week_tokens": 0,
                "week_requests": 0,
                "week_cost": 0.0,
                "month_tokens": 0,
                "month_requests": 0,
                "month_cost": 0.0,
                "total_tokens": 0,
                "total_requests": 0,
                "total_cost": 0.0,
            })
    
    return {
        "generated_at": now.isoformat(),
        "summaries": summaries,
        "grand_total": {
            "today_tokens": sum(s["today_tokens"] for s in summaries),
            "today_requests": sum(s["today_requests"] for s in summaries),
            "today_cost": round(sum(s["today_cost"] for s in summaries), 4),
            "week_tokens": sum(s["week_tokens"] for s in summaries),
            "week_requests": sum(s["week_requests"] for s in summaries),
            "week_cost": round(sum(s["week_cost"] for s in summaries), 4),
            "month_tokens": sum(s["month_tokens"] for s in summaries),
            "month_requests": sum(s["month_requests"] for s in summaries),
            "month_cost": round(sum(s["month_cost"] for s in summaries), 4),
        },
    }


# ---------------------------------------------------------------------------
# GET /usage/recent — recent usage records
# ---------------------------------------------------------------------------
@router.get("/usage/recent")
def get_recent_usage(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent API usage records."""
    records = db.query(APIUsageRecord).order_by(APIUsageRecord.created_at.desc()).limit(limit).all()
    return {
        "records": [{
            "id": r.id,
            "provider": r.provider,
            "api_key_env": r.api_key_env,
            "api_key_masked": r.api_key_masked,
            "endpoint": r.endpoint,
            "model": r.model,
            "tokens_total": r.tokens_total,
            "cost_usd": r.cost_usd,
            "request_status": r.request_status,
            "source_system": r.source_system,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in records],
        "count": len(records),
    }


# ---------------------------------------------------------------------------
# GET /balance/history — balance snapshot history
# ---------------------------------------------------------------------------
@router.get("/balance/history")
def get_balance_history(provider: Optional[str] = None, days: int = 7, db: Session = Depends(get_db)):
    """Get balance history over time."""
    since = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(APIBalanceSnapshot).filter(APIBalanceSnapshot.checked_at >= since)
    if provider:
        query = query.filter(APIBalanceSnapshot.provider == provider)
    
    snapshots = query.order_by(APIBalanceSnapshot.checked_at.desc()).all()
    
    return {
        "provider_filter": provider,
        "days": days,
        "snapshots": [{
            "id": s.id,
            "provider": s.provider,
            "api_key_env": s.api_key_env,
            "api_key_masked": s.api_key_masked,
            "balance": s.balance,
            "currency": s.currency,
            "status": s.status,
            "checked_at": s.checked_at.isoformat() if s.checked_at else None,
        } for s in snapshots],
    }


# ---------------------------------------------------------------------------
# Legacy: single balance check (redirects to all)
# ---------------------------------------------------------------------------
@router.get("/balance/legacy")
async def get_legacy_balance():
    """Legacy single-balance endpoint for backward compat."""
    api_key = settings.KIMI_API_KEY or settings.DASHBOARD_AI_API_KEY
    base_url = settings.KIMI_BASE_URL or settings.DASHBOARD_AI_BASE_URL or "https://api.moonshot.ai/v1"
    
    if not api_key:
        return {"status": "error", "message": "No API key configured"}
    
    result = await _check_provider_balance("kimi", api_key, base_url)
    return {
        "status": result["status"],
        "balance": result.get("balance"),
        "currency": result.get("currency", "USD"),
        "message": result.get("message"),
    }
