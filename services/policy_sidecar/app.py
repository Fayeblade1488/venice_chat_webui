import os
import re
import json
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse

LITELLM_BASE = os.getenv("LITELLM_BASE_URL", "http://litellm:4000")
API_TOKEN = os.getenv("POLICY_API_TOKEN", "")  # if set, require Authorization: Bearer <token>

# Defaults (can be overridden via headers)
DEFAULT_STRIP_THINKING = os.getenv("POLICY_STRIP_THINKING_DEFAULT", "true").lower() == "true"
DEFAULT_DISABLE_THINKING = os.getenv("POLICY_DISABLE_THINKING_DEFAULT", "true").lower() == "true"
DEFAULT_SEARCH = os.getenv("POLICY_ENABLE_WEB_SEARCH_DEFAULT", "off")  # off|auto|on
DEFAULT_CITATIONS = os.getenv("POLICY_ENABLE_CITATIONS_DEFAULT", "false").lower() == "true"
DEFAULT_INCLUDE_RESULTS = os.getenv("POLICY_INCLUDE_RESULTS_IN_STREAM_DEFAULT", "false").lower() == "true"
DEFAULT_INCLUDE_SYS = os.getenv("POLICY_INCLUDE_VENICE_SYSTEM_PROMPT_DEFAULT", "true").lower() == "true"

ALLOW_HEADER_OVERRIDES = os.getenv("POLICY_ALLOW_HEADER_OVERRIDES", "true").lower() == "true"

# Redaction patterns (additive)
REDACT_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REDACT_OPENAI_KEY = re.compile(r"sk-[A-Za-z0-9]{16,}")
REDACT_GENERIC_KEY = re.compile(r"(?i)(api[_-]?key|authorization|bearer)\s*[:=]\s*[A-Za-z0-9._-]{10,}")
REDACT_VENICE_KEY = re.compile(r"vvv_[A-Za-z0-9._-]{10,}")  # generic example

def redact(s: str) -> str:
    s = REDACT_EMAIL.sub("[email redacted]", s)
    s = REDACT_OPENAI_KEY.sub("sk-REDACTED", s)
    s = REDACT_GENERIC_KEY.sub("API_KEY=REDACTED", s)
    s = REDACT_VENICE_KEY.sub("vvv_REDACTED", s)
    return s

def need_auth(auth_header: Optional[str]) -> None:
    if not API_TOKEN:
        return
    token = None
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def merge_policy(body: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    venice_params = body.get("venice_parameters", {}) if isinstance(body, dict) else {}

    # Apply defaults
    venice_params.setdefault("strip_thinking_response", DEFAULT_STRIP_THINKING)
    venice_params.setdefault("disable_thinking", DEFAULT_DISABLE_THINKING)
    venice_params.setdefault("enable_web_search", DEFAULT_SEARCH)
    venice_params.setdefault("enable_web_citations", DEFAULT_CITATIONS)
    venice_params.setdefault("include_search_results_in_stream", DEFAULT_INCLUDE_RESULTS)
    venice_params.setdefault("include_venice_system_prompt", DEFAULT_INCLUDE_SYS)

    # Header overrides (if allowed)
    if ALLOW_HEADER_OVERRIDES:
        hv = {k.lower(): v for k, v in headers.items()}
        def hget(name: str) -> Optional[str]:
            return hv.get(name.lower())

        v = hget("x-venice-search")
        if v in ("off","auto","on"):
            venice_params["enable_web_search"] = v

        v = hget("x-venice-citations")
        if v is not None:
            venice_params["enable_web_citations"] = v.lower() in ("1","true","yes","on")

        v = hget("x-include-search-results")
        if v is not None:
            venice_params["include_search_results_in_stream"] = v.lower() in ("1","true","yes","on")

        v = hget("x-strip-thinking")
        if v is not None:
            venice_params["strip_thinking_response"] = v.lower() in ("1","true","yes","on")

        v = hget("x-disable-thinking")
        if v is not None:
            venice_params["disable_thinking"] = v.lower() in ("1","true","yes","on")

        v = hget("x-include-venice-system-prompt")
        if v is not None:
            venice_params["include_venice_system_prompt"] = v.lower() in ("1","true","yes","on")

        v = hget("x-model")
        if v:
            body["model"] = v

    body["venice_parameters"] = venice_params
    return body

app = FastAPI(title="Policy Sidecar", version="1.0.0")

@app.middleware("http")
async def auth_and_log(request: Request, call_next):
    # Middle auth: apply only to /v1/*
    path = request.url.path
    if path.startswith("/v1/"):
        need_auth(request.headers.get("authorization"))
    # Log (redacted) basic request info
    try:
        body_bytes = await request.body()
        body_preview = redact(body_bytes.decode("utf-8")[:1000]) if body_bytes else ""
        print(f"[policy] {request.method} {path} body={body_preview}")
    except Exception:
        pass
    response = await call_next(request)
    try:
        if hasattr(response, "body_iterator"):
            # streaming, skip preview
            print(f"[policy] response status={response.status_code} (stream)")
        else:
            print(f"[policy] response status={response.status_code}")
    except Exception:
        pass
    return response

async def _forward(req: Request, target_path: str) -> Response:
    # Forward request to LiteLLM, optionally merging policy into JSON body
    url = f"{LITELLM_BASE}{target_path}"
    method = req.method
    headers = {k: v for k, v in req.headers.items() if k.lower() != "host"}

    body_bytes = await req.body()
    json_payload = None
    content_type = req.headers.get("content-type", "")

    if "application/json" in content_type and body_bytes:
        try:
            json_payload = json.loads(body_bytes.decode("utf-8"))
            # Only apply policy to chat completions
            if target_path == "/v1/chat/completions" and isinstance(json_payload, dict):
                json_payload = merge_policy(json_payload, headers)
        except Exception:
            json_payload = None

    async with httpx.AsyncClient(timeout=120) as http:
        r = await http.request(
            method, url,
            headers=headers,
            json=json_payload if json_payload is not None else None,
            content=None if json_payload is not None else body_bytes
        )
        return Response(
            content=r.content,
            status_code=r.status_code,
            headers={k: v for k, v in r.headers.items() if k.lower() not in ("content-encoding","transfer-encoding","connection")},
            media_type=r.headers.get("content-type")
        )

@app.api_route("/v1/chat/completions", methods=["POST"])
async def chat_completions(req: Request):
    return await _forward(req, "/v1/chat/completions")

@app.api_route("/v1/embeddings", methods=["POST"])
async def embeddings(req: Request):
    return await _forward(req, "/v1/embeddings")

@app.api_route("/v1/images/generations", methods=["POST"])
async def images(req: Request):
    return await _forward(req, "/v1/images/generations")

@app.get("/v1/models")
async def models(req: Request):
    return await _forward(req, "/v1/models")

@app.get("/healthz")
async def health():
    return {"ok": True}
