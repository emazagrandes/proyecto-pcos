"""
llm_client.py — Backend-agnostic LLM interface for PCOS Research System
========================================================================

Abstracts all LLM calls so the rest of the codebase is backend-independent.
Drop-in replacement for direct Ollama HTTP calls.

BACKENDS
--------
  LLM_BACKEND=ollama   (default) — Ollama running at localhost:11434
  LLM_BACKEND=gemini   — Google Gemini API  (set GEMINI_API_KEY)
  LLM_BACKEND=groq     — Groq API           (set GROQ_API_KEY)

SETUP
-----
  1. Copy .env.example to .env and fill in the key for your backend.
  2. Or export the env vars before running any script:
       export LLM_BACKEND=gemini
       export GEMINI_API_KEY=your_key_here

DEFAULT MODELS
--------------
  Ollama:  OLLAMA_GENERATE_MODEL  (default: gemma4:31b-cloud)
           OLLAMA_EMBED_MODEL     (default: nomic-embed-text)
  Gemini:  GEMINI_MODEL           (default: gemini-2.0-flash)
  Groq:    GROQ_MODEL             (default: llama-3.3-70b-versatile)

PUBLIC API
----------
  generate(prompt, *, temperature, max_tokens)  -> str
      Simple text-in / text-out. Used by: anomaly_scan synthesis, labeling.

  chat(messages, *, temperature, max_tokens)    -> str
      Multi-turn conversation without tools. Used by: labeling, extraction.
      messages = [{"role": "system"|"user"|"assistant", "content": "..."}]

  chat_with_tools(messages, tool_schemas, *, temperature, max_tokens) -> dict
      Multi-turn with function calling. Used by: research_agent.
      Returns Ollama-compatible dict:
        {"message": {"content": "...", "tool_calls": [...]}}
      tool_calls element: {"function": {"name": "...", "arguments": {...}}}

  embed(text)  -> list[float] | None
      Returns embedding vector. Only available with Ollama backend.
      Returns None on other backends (embeddings already computed).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LLM_BACKEND: str = os.environ.get("LLM_BACKEND", "ollama").lower()

# Ollama
OLLAMA_BASE_URL: str    = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_GENERATE_MODEL   = os.environ.get("OLLAMA_GENERATE_MODEL", "gemma4:31b-cloud")
OLLAMA_EMBED_MODEL      = os.environ.get("OLLAMA_EMBED_MODEL",    "nomic-embed-text")

# Gemini — lista de keys para rotación automática cuando se agota cuota diaria
GEMINI_MODEL    = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
_raw_keys = [
    os.environ.get("GEMINI_API_KEY", ""),
    os.environ.get("GEMINI_API_KEY_2", ""),
]
GEMINI_API_KEYS = [k for k in _raw_keys if k]
GEMINI_API_KEY  = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

# Groq
GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL      = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

log.info("LLM backend: %s", LLM_BACKEND)

# ---------------------------------------------------------------------------
# Type helpers
# ---------------------------------------------------------------------------

Message  = dict[str, Any]    # {"role": ..., "content": ..., ...}
ToolCall = dict[str, Any]    # {"function": {"name": ..., "arguments": {...}}}


# ---------------------------------------------------------------------------
# OLLAMA backend
# ---------------------------------------------------------------------------

def _ollama_generate(prompt: str, *, temperature: float, max_tokens: int) -> str:
    import requests
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model":  OLLAMA_GENERATE_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 8192},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def _ollama_chat(messages: list[Message], *, temperature: float, max_tokens: int) -> str:
    import requests
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model":    OLLAMA_GENERATE_MODEL,
            "messages": messages,
            "stream":   False,
            "options":  {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 8192},
        },
        timeout=180,
    )
    resp.raise_for_status()
    return ((resp.json().get("message") or {}).get("content") or "").strip()


def _ollama_chat_with_tools(
    messages: list[Message],
    tool_schemas: list[dict],
    *,
    temperature: float,
    max_tokens: int,
) -> dict:
    import requests
    payload = {
        "model":    OLLAMA_GENERATE_MODEL,
        "messages": messages,
        "tools":    tool_schemas,
        "stream":   False,
        "options":  {"temperature": temperature, "num_predict": max_tokens, "num_ctx": 8192},
    }
    for attempt in range(1, 4):
        try:
            resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=300)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == 3:
                raise
            wait = 2 ** attempt
            log.warning("Ollama error (attempt %d/3): %s — retrying in %ds", attempt, e, wait)
            time.sleep(wait)


def _ollama_embed(text: str) -> list[float] | None:
    import requests
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={"model": OLLAMA_EMBED_MODEL, "input": text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]
    except Exception as e:
        log.warning("Ollama embed failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# GEMINI backend
# ---------------------------------------------------------------------------

_gemini_client = None
_gemini_key_idx = 0


def _get_gemini_client():
    global _gemini_client, _gemini_key_idx
    if _gemini_client is None:
        if not GEMINI_API_KEYS:
            raise ValueError("GEMINI_API_KEY not set. Add it to .env or export it.")
        import google.genai as genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEYS[_gemini_key_idx])
    return _gemini_client


def _rotate_gemini_key():
    """Switch to the next API key when daily quota is exhausted."""
    global _gemini_client, _gemini_key_idx
    next_idx = (_gemini_key_idx + 1) % len(GEMINI_API_KEYS)
    if next_idx == _gemini_key_idx:
        raise RuntimeError("All Gemini API keys exhausted for today.")
    _gemini_key_idx = next_idx
    _gemini_client = None  # force re-init with new key
    log.warning("Gemini daily quota exhausted — rotando a key %d/%d", _gemini_key_idx + 1, len(GEMINI_API_KEYS))


def _parse_retry_delay(err: str) -> float:
    """Extract retryDelay seconds from Google API error string, default 65s."""
    import re as _re
    m = _re.search(r"retryDelay['\"]:\s*['\"](\d+)s", err)
    return float(m.group(1)) + 5 if m else 65.0


def _gemini_call_with_rotation(fn, *args, **kwargs):
    """Wrapper that catches 429s and either waits (per-minute) or rotates key (per-day)."""
    import time as _time
    for attempt in range(len(GEMINI_API_KEYS) * 2 + 4):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            err = str(e)
            if "429" not in err and "RESOURCE_EXHAUSTED" not in err:
                raise
            per_day = "PerDay" in err or "per_day" in err.lower()
            per_min = "PerMinute" in err or "per_minute" in err.lower()
            # Rotate only when daily is the SOLE cause (per-minute errors also list PerDay as a side effect)
            if per_day and not per_min:
                if len(GEMINI_API_KEYS) > 1:
                    _rotate_gemini_key()
                else:
                    raise RuntimeError("Daily quota exhausted and no backup key available.") from e
            else:
                wait = _parse_retry_delay(err)
                log.warning("Gemini rate limit (per-minute) — esperando %.0fs...", wait)
                _time.sleep(wait)
    raise RuntimeError("All Gemini API keys and retries exhausted.")


def _gemini_generate(prompt: str, *, temperature: float, max_tokens: int) -> str:
    import google.genai.types as gtypes

    def _call():
        client = _get_gemini_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                thinking_config=gtypes.ThinkingConfig(thinking_budget=0),
            ),
        )
        return (response.text or "").strip()

    return _gemini_call_with_rotation(_call)


def _gemini_chat(messages: list[Message], *, temperature: float, max_tokens: int) -> str:
    """Convert Ollama-format messages to Gemini format and call the API."""
    import google.genai.types as gtypes

    system_instruction = None
    contents = []
    for msg in messages:
        role    = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_instruction = content
        elif role == "user":
            contents.append(gtypes.Content(role="user",  parts=[gtypes.Part(text=content)]))
        elif role == "assistant":
            contents.append(gtypes.Content(role="model", parts=[gtypes.Part(text=content)]))

    config = gtypes.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system_instruction,
        thinking_config=gtypes.ThinkingConfig(thinking_budget=0),
    )

    def _call():
        client = _get_gemini_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        return (response.text or "").strip()

    return _gemini_call_with_rotation(_call)


def _build_gemini_tools(tool_schemas: list[dict]):
    """Convert Ollama tool schema format → google.genai FunctionDeclaration list."""
    import google.genai.types as gtypes

    TYPE_MAP = {
        "string":  gtypes.Type.STRING,
        "integer": gtypes.Type.INTEGER,
        "number":  gtypes.Type.NUMBER,
        "boolean": gtypes.Type.BOOLEAN,
        "array":   gtypes.Type.ARRAY,
        "object":  gtypes.Type.OBJECT,
    }

    def _build_schema(schema_dict: dict) -> gtypes.Schema:
        t = TYPE_MAP.get((schema_dict.get("type") or "string").lower(), gtypes.Type.STRING)
        props = {}
        required = schema_dict.get("required", [])
        for pname, pdef in (schema_dict.get("properties") or {}).items():
            props[pname] = gtypes.Schema(
                type=TYPE_MAP.get((pdef.get("type") or "string").lower(), gtypes.Type.STRING),
                description=pdef.get("description", ""),
            )
        return gtypes.Schema(type=t, properties=props, required=required)

    declarations = []
    for ts in tool_schemas:
        fn = ts.get("function", ts)   # handle both wrapped {"type":"function","function":{...}} and bare
        params = fn.get("parameters", {})
        declarations.append(
            gtypes.FunctionDeclaration(
                name=fn["name"],
                description=fn.get("description", ""),
                parameters=_build_schema(params),
            )
        )
    return [gtypes.Tool(function_declarations=declarations)]


def _messages_to_gemini_contents(messages: list[Message]) -> tuple[str | None, list]:
    """Convert Ollama-format message list → (system_instruction, gemini_contents).

    Handles: user, assistant (text), assistant (tool_calls), tool (results).
    """
    import google.genai.types as gtypes

    system_instruction = None
    contents = []
    # We need to track tool name for tool result messages (Gemini needs it)
    last_tool_name: str | None = None

    for msg in messages:
        role    = msg.get("role", "user")
        content = msg.get("content", "") or ""

        if role == "system":
            system_instruction = content

        elif role == "user":
            contents.append(gtypes.Content(role="user", parts=[gtypes.Part(text=content)]))

        elif role == "assistant":
            tool_calls = msg.get("tool_calls") or []
            parts = []
            if content:
                parts.append(gtypes.Part(text=content))
            for tc in tool_calls:
                fn   = tc.get("function", {})
                name = fn.get("name", "")
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                parts.append(gtypes.Part.from_function_call(name=name, args=args))
                last_tool_name = name   # remember for next tool-result message
            if parts:
                contents.append(gtypes.Content(role="model", parts=parts))

        elif role == "tool":
            # Gemini expects a "user" turn with a function_response part
            fn_name = last_tool_name or "unknown_tool"
            try:
                result_obj = json.loads(content)
            except Exception:
                result_obj = {"result": content}
            contents.append(gtypes.Content(
                role="user",
                parts=[gtypes.Part.from_function_response(name=fn_name, response=result_obj)],
            ))

    return system_instruction, contents


def _gemini_chat_with_tools(
    messages: list[Message],
    tool_schemas: list[dict],
    *,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call Gemini with tool use. Returns Ollama-compatible dict."""
    import google.genai.types as gtypes

    system_instruction, contents = _messages_to_gemini_contents(messages)
    gemini_tools = _build_gemini_tools(tool_schemas)

    config = gtypes.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system_instruction,
        tools=gemini_tools,
        thinking_config=gtypes.ThinkingConfig(thinking_budget=0),
    )

    def _call():
        c = _get_gemini_client()
        return c.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

    response = _gemini_call_with_rotation(_call)

    # Convert Gemini response → Ollama-compatible dict
    text_parts    = []
    tool_calls_out: list[ToolCall] = []

    candidate = response.candidates[0] if response.candidates else None
    if candidate:
        for part in (candidate.content.parts or []):
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                args = dict(fc.args) if fc.args else {}
                tool_calls_out.append({
                    "id":       f"gemini_{fc.name}",
                    "function": {"name": fc.name, "arguments": args},
                })

    return {
        "message": {
            "role":       "assistant",
            "content":    "\n".join(text_parts).strip(),
            "tool_calls": tool_calls_out,
        }
    }


# ---------------------------------------------------------------------------
# GROQ backend  (OpenAI-compatible)
# ---------------------------------------------------------------------------

_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set. Add it to .env or export it.")
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def _groq_messages_for_chat(messages: list[Message]) -> list[dict]:
    """Ollama messages → Groq messages (drop system if first, keep others)."""
    out = []
    for msg in messages:
        role    = msg.get("role", "user")
        content = msg.get("content") or ""
        if role in ("system", "user", "assistant"):
            out.append({"role": role, "content": content})
        elif role == "tool":
            out.append({
                "role":         "tool",
                "content":      content,
                "tool_call_id": msg.get("tool_call_id", "call_0"),
            })
    return out


def _groq_generate(prompt: str, *, temperature: float, max_tokens: int) -> str:
    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def _groq_chat(messages: list[Message], *, temperature: float, max_tokens: int) -> str:
    client = _get_groq_client()
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=_groq_messages_for_chat(messages),
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def _groq_chat_with_tools(
    messages: list[Message],
    tool_schemas: list[dict],
    *,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call Groq with tool use. Returns Ollama-compatible dict."""
    client = _get_groq_client()

    for attempt in range(1, 4):
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=_groq_messages_for_chat(messages),
                tools=tool_schemas,        # already in OpenAI format — same as Ollama
                tool_choice="auto",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            break
        except Exception as e:
            if attempt == 3:
                raise
            log.warning("Groq error (attempt %d/3): %s — retrying in %ds", attempt, e, 2**attempt)
            time.sleep(2 ** attempt)

    msg = resp.choices[0].message
    tool_calls_out: list[ToolCall] = []
    for tc in (msg.tool_calls or []):
        try:
            args = json.loads(tc.function.arguments)
        except Exception:
            args = {}
        tool_calls_out.append({
            "id":       tc.id,
            "function": {"name": tc.function.name, "arguments": args},
        })

    return {
        "message": {
            "role":       "assistant",
            "content":    (msg.content or "").strip(),
            "tool_calls": tool_calls_out,
        }
    }


# ---------------------------------------------------------------------------
# PUBLIC API  (the only functions the rest of the code should call)
# ---------------------------------------------------------------------------

def generate(prompt: str, *, temperature: float = 0.20, max_tokens: int = 800) -> str:
    """Simple text-in / text-out generation."""
    if LLM_BACKEND == "gemini":
        return _gemini_generate(prompt, temperature=temperature, max_tokens=max_tokens)
    if LLM_BACKEND == "groq":
        return _groq_generate(prompt, temperature=temperature, max_tokens=max_tokens)
    return _ollama_generate(prompt, temperature=temperature, max_tokens=max_tokens)


def chat(messages: list[Message], *, temperature: float = 0.0, max_tokens: int = 800) -> str:
    """Multi-turn chat without tools. Returns assistant text."""
    if LLM_BACKEND == "gemini":
        return _gemini_chat(messages, temperature=temperature, max_tokens=max_tokens)
    if LLM_BACKEND == "groq":
        return _groq_chat(messages, temperature=temperature, max_tokens=max_tokens)
    return _ollama_chat(messages, temperature=temperature, max_tokens=max_tokens)


def chat_with_tools(
    messages: list[Message],
    tool_schemas: list[dict],
    *,
    temperature: float = 0.15,
    max_tokens: int = 2000,
) -> dict:
    """Multi-turn chat with function calling.

    Returns Ollama-compatible dict:
      {"message": {"content": "...", "tool_calls": [{"function": {"name": ..., "arguments": {...}}}]}}
    """
    if LLM_BACKEND == "gemini":
        return _gemini_chat_with_tools(messages, tool_schemas, temperature=temperature, max_tokens=max_tokens)
    if LLM_BACKEND == "groq":
        return _groq_chat_with_tools(messages, tool_schemas, temperature=temperature, max_tokens=max_tokens)
    return _ollama_chat_with_tools(messages, tool_schemas, temperature=temperature, max_tokens=max_tokens)


def embed(text: str) -> list[float] | None:
    """Embedding vector. Only available with Ollama. Returns None otherwise."""
    if LLM_BACKEND == "ollama":
        return _ollama_embed(text)
    log.warning("embed() called with backend=%s — not supported. Returning None.", LLM_BACKEND)
    return None


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    print(f"\nTesting backend: {LLM_BACKEND}")
    print("-" * 40)

    try:
        # Test generate
        resp = generate("Reply with exactly: PCOS_OK", max_tokens=10)
        print(f"generate()  → {repr(resp)}")

        # Test chat
        resp2 = chat([
            {"role": "system",  "content": "You are a helpful assistant."},
            {"role": "user",    "content": "Say: CHAT_OK"},
        ], max_tokens=10)
        print(f"chat()      → {repr(resp2)}")

        # Test tool use
        test_tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"],
                },
            }
        }]
        resp3 = chat_with_tools(
            [{"role": "user", "content": "What's the weather in Madrid?"}],
            test_tools,
            max_tokens=200,
        )
        msg3 = resp3.get("message", {})
        print(f"chat_with_tools() → content={repr(msg3.get('content','')[:50])}, "
              f"tool_calls={len(msg3.get('tool_calls', []))}")

        print("\n✅ All tests passed.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
