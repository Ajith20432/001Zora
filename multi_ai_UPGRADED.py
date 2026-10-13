"""
multi_ai.py — UPGRADED 5-AI Expert Council + Google Gemini Supreme Judge
====================================================================
Provides concurrent evaluation from Groq, OpenRouter, Mistral, HuggingFace,
with Gemini-2.0-Flash synthesizing final verdicts using Bayesian weighting.

Features:
- Thread-safe concurrent API calls with 12s timeout
- Robust JSON extraction with fallback regex parsing
- Circuit breaker pattern for rate limits (429/500/503)
- Adaptive Bayesian weighting based on historical accuracy
- Confidence threshold enforcement (>=75% to trade)
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
import os
import re
import threading
import time
import requests
from typing import Optional, Tuple, List, Dict, Any

# Import the Adaptive Brain for Bayesian weighting
try:
    from brain import BRAIN
except ImportError:
    BRAIN = None

logger = logging.getLogger("zora.multi_ai")

# Configuration Constants
TIMEOUT = 12
MAX_RETRIES = 2
CONFIDENCE_THRESHOLD = 75

# Thread-safe cooldown tracking
_COOLDOWNS: Dict[str, float] = {}
_LOCK = threading.Lock()
_CALL_CACHE: Dict[str, Tuple[float, Optional[Dict]]] = {}
_CACHE_TTL = 300  # 5-minute cache for same prompts

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def _is_cooling(provider_name: str) -> bool:
    """Check if a provider is in cooldown due to rate limiting."""
    with _LOCK:
        return time.time() < _COOLDOWNS.get(provider_name, 0.0)

def _set_cooldown(provider_name: str, seconds: float = 60.0) -> None:
    """Set cooldown for a provider after rate limit hit."""
    with _LOCK:
        _COOLDOWNS[provider_name] = time.time() + seconds
        logger.warning(f"Cooldown set for {provider_name} for {seconds}s")

def _get_cache(prompt_hash: str) -> Optional[Dict]:
    """Retrieve cached response if within TTL."""
    with _LOCK:
        if prompt_hash in _CALL_CACHE:
            timestamp, result = _CALL_CACHE[prompt_hash]
            if time.time() - timestamp < _CACHE_TTL:
                return result
            del _CALL_CACHE[prompt_hash]
    return None

def _set_cache(prompt_hash: str, result: Dict) -> None:
    """Cache a response with timestamp."""
    with _LOCK:
        _CALL_CACHE[prompt_hash] = (time.time(), result)

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text with robust fallback parsing.
    Handles LLM output that includes explanatory text before/after JSON.
    """
    if not text or not isinstance(text, str):
        return None
    
    # First try direct parsing
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try extracting JSON block with regex
    try:
        match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError, AttributeError):
        pass
    
    # Try finding multiple JSON objects
    try:
        matches = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text)
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception:
        pass
    
    logger.debug(f"Could not extract JSON from response: {text[:200]}")
    return None

def _validate_council_response(response: Optional[Dict]) -> bool:
    """Validate that a council response has required fields."""
    if not response or not isinstance(response, dict):
        return False
    
    required_fields = {"lean", "confidence"}
    if not all(field in response for field in required_fields):
        return False
    
    # Validate confidence is numeric and in range
    try:
        conf = int(response.get("confidence", 0))
        if not (0 <= conf <= 100):
            return False
    except (TypeError, ValueError):
        return False
    
    # Validate lean is one of the expected values
    lean = response.get("lean", "").upper()
    if lean not in ("BUY", "SELL", "HOLD", "NEUTRAL"):
        return False
    
    return True

# ==============================================================================
# AI PROVIDER CALLERS
# ==============================================================================

def _call_groq(prompt: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Call Groq Llama-3.3-70b for momentum & price action analysis.
    Fast, reliable, ideal for real-time evaluation.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key or _is_cooling("groq"):
        return None
    
    if retry_count >= MAX_RETRIES:
        logger.warning("Groq: Max retries exceeded")
        return None
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a crypto momentum & price action expert analyzing market microstructure. "
                    "Output ONLY valid JSON: {\"lean\": \"BUY\"|\"SELL\"|\"HOLD\", \"confidence\": int(0-100), \"reason\": \"brief insight\"}"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                content = response.json()["choices"][0]["message"]["content"]
                result = _extract_json(content)
                if _validate_council_response(result):
                    return result
            except (KeyError, IndexError, TypeError) as e:
                logger.debug(f"Groq parsing error: {e}")
                return None
        
        elif response.status_code in (429, 500, 503):
            _set_cooldown("groq", 90)
            logger.warning(f"Groq rate limited or server error: {response.status_code}")
        
        elif response.status_code >= 500:
            _set_cooldown("groq", 120)
            logger.warning(f"Groq server error: {response.status_code}")
    
    except requests.Timeout:
        logger.warning("Groq: Request timeout")
    except requests.RequestException as e:
        logger.warning(f"Groq request error: {e}")
    except Exception as e:
        logger.error(f"Groq unexpected error: {e}")
    
    return None

def _call_openrouter(prompt: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Call OpenRouter for cross-model validation & deep reasoning.
    Selects best available model for reasoning quality.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key or _is_cooling("openrouter"):
        return None
    
    if retry_count >= MAX_RETRIES:
        return None
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "zora-trading-bot",
        "X-Title": "zora"
    }
    
    payload = {
        "model": "openrouter/auto",  # Auto-selects best available model
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a quantitative risk validator analyzing market setup quality and risk-reward. "
                    "Output ONLY valid JSON: {\"lean\": \"BUY\"|\"SELL\"|\"HOLD\", \"confidence\": int(0-100), \"reason\": \"risk assessment\"}"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                content = response.json()["choices"][0]["message"]["content"]
                result = _extract_json(content)
                if _validate_council_response(result):
                    return result
            except (KeyError, IndexError, TypeError):
                return None
        
        elif response.status_code in (429, 500, 503):
            _set_cooldown("openrouter", 90)
        
        elif response.status_code >= 500:
            _set_cooldown("openrouter", 120)
    
    except requests.Timeout:
        logger.warning("OpenRouter: Request timeout")
    except requests.RequestException as e:
        logger.warning(f"OpenRouter request error: {e}")
    except Exception as e:
        logger.error(f"OpenRouter unexpected error: {e}")
    
    return None

def _call_mistral(prompt: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Call Mistral for algorithmic market structure analysis.
    Excellent for identifying institutional order flow patterns.
    """
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not api_key or _is_cooling("mistral"):
        return None
    
    if retry_count >= MAX_RETRIES:
        return None
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an algorithmic market structure analyst specializing in order flow dynamics. "
                    "Output ONLY valid JSON: {\"lean\": \"BUY\"|\"SELL\"|\"HOLD\", \"confidence\": int(0-100), \"reason\": \"order flow insight\"}"
                )
            },
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                content = response.json()["choices"][0]["message"]["content"]
                result = _extract_json(content)
                if _validate_council_response(result):
                    return result
            except (KeyError, IndexError, TypeError):
                return None
        
        elif response.status_code in (429, 500, 503):
            _set_cooldown("mistral", 90)
        
        elif response.status_code >= 500:
            _set_cooldown("mistral", 120)
    
    except requests.Timeout:
        logger.warning("Mistral: Request timeout")
    except requests.RequestException as e:
        logger.warning(f"Mistral request error: {e}")
    except Exception as e:
        logger.error(f"Mistral unexpected error: {e}")
    
    return None

def _call_huggingface(prompt: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
    """
    Call HuggingFace Inference API with Qwen or DeepSeek for pattern recognition.
    Open-weights alternative provides diverse perspective.
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY", "").strip()
    if not api_key or _is_cooling("huggingface"):
        return None
    
    if retry_count >= MAX_RETRIES:
        return None
    
    url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": (
            f"You are a deep market pattern analyst. Output ONLY JSON: "
            f"{{\"lean\": \"BUY\"|\"SELL\"|\"HOLD\", \"confidence\": 0-100, \"reason\": \"brief\"}}\n\n{prompt}"
        ),
        "parameters": {
            "temperature": 0.2,
            "max_new_tokens": 300
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                result_data = response.json()
                if isinstance(result_data, list) and len(result_data) > 0:
                    generated_text = result_data[0].get("generated_text", "")
                    result = _extract_json(generated_text)
                    if _validate_council_response(result):
                        return result
            except (KeyError, IndexError, TypeError):
                return None
        
        elif response.status_code in (429, 500, 503):
            _set_cooldown("huggingface", 90)
        
        elif response.status_code >= 500:
            _set_cooldown("huggingface", 120)
    
    except requests.Timeout:
        logger.warning("HuggingFace: Request timeout")
    except requests.RequestException as e:
        logger.warning(f"HuggingFace request error: {e}")
    except Exception as e:
        logger.error(f"HuggingFace unexpected error: {e}")
    
    return None

# ==============================================================================
# SUPREME JUDGE - GEMINI-2.0-FLASH VERDICT
# ==============================================================================

def _call_gemini_judge(
    market_dossier: str,
    council_opinions: List[Dict[str, Any]]
) -> Tuple[str, int, str]:
    """
    Call Google Gemini-2.0-Flash as the Supreme Judge.
    
    Synthesizes council opinions using:
    - Weighted Bayesian credibility (from BRAIN historical accuracy)
    - Conflicting signal resolution
    - Risk-reward validation
    - Confidence threshold enforcement
    
    Returns: (decision: str, confidence: int, note: str)
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("Gemini API key missing - cannot obtain final verdict")
        return "HOLD", 0, "Gemini API key not configured"
    
    # Gather Bayesian weights from adaptive brain if available
    brain_weights = {}
    if BRAIN:
        try:
            snapshot = BRAIN.snapshot()
            # Extract provider weights from brain snapshot
            for provider, stats in snapshot.items():
                if isinstance(stats, dict) and "accuracy" in stats:
                    brain_weights[provider] = stats["accuracy"]
        except Exception as e:
            logger.debug(f"Brain snapshot error: {e}")
    
    # Build judge prompt with context and weighted opinions
    judge_prompt = f"""You are the Supreme Chief Trading Judge for an elite crypto quantitative fund.
Your role: Synthesize 4 expert opinions, resolve contradictions, and render final verdict.

=== LIVE MARKET DOSSIER ===
{market_dossier}

=== ADVISOR CREDIBILITY WEIGHTS (Historical Accuracy) ===
{json.dumps(brain_weights or {}, indent=2)}

=== 4-AI COUNCIL OPINIONS ===
{json.dumps(council_opinions, indent=2)}

DECISION RULES:
1. Weight opinions by advisor historical accuracy (Bayesian)
2. If conflicting signals (>1 lean opposite): default to HOLD
3. If sideways/choppy regime: bias toward HOLD
4. Require >=75% confidence to authorize entry
5. Favor proven setup patterns over single strong opinion

OUTPUT FORMAT (ONLY valid JSON):
{{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": <int 0-100>,
  "note": "<one sentence with reasoning>"
}}"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": judge_prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "maxOutputTokens": 500
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                raw_response = response.json()
                if "candidates" in raw_response and len(raw_response["candidates"]) > 0:
                    content_parts = raw_response["candidates"][0].get("content", {}).get("parts", [])
                    if content_parts:
                        raw_text = content_parts[0].get("text", "")
                        parsed = _extract_json(raw_text)
                        
                        if parsed:
                            decision = str(parsed.get("decision", "HOLD")).upper()
                            confidence = int(parsed.get("confidence", 0))
                            note = str(parsed.get("note", "Judge synthesis completed"))
                            
                            # Validate decision
                            if decision in ("BUY", "SELL", "HOLD"):
                                logger.info(f"Judge verdict: {decision} ({confidence}%) - {note}")
                                return decision, confidence, note
            
            except (KeyError, IndexError, TypeError, ValueError) as e:
                logger.debug(f"Gemini response parsing error: {e}")
        
        elif response.status_code >= 500:
            logger.warning(f"Gemini server error: {response.status_code}")
    
    except requests.Timeout:
        logger.warning("Gemini Judge: Request timeout")
    except requests.RequestException as e:
        logger.warning(f"Gemini Judge request error: {e}")
    except Exception as e:
        logger.error(f"Gemini Judge unexpected error: {e}")
    
    return "HOLD", 0, "Judge unavailable or error occurred"

# ==============================================================================
# PUBLIC CONSENSUS INTERFACE
# ==============================================================================

def get_ai_consensus(symbol: str, market_dossier: str) -> Tuple[str, int, str]:
    """
    Execute full 5-AI Expert Council evaluation with Gemini Judge.
    
    Process:
    1. Query 4 council providers in parallel (Groq, OpenRouter, Mistral, HF)
    2. Collect valid opinions with confidence scores
    3. Pass to Gemini Judge with Bayesian weighting
    4. Return final decision enforcing 75% confidence threshold
    
    Args:
        symbol: Trading pair (e.g., "ETH/USDT")
        market_dossier: Structured market context from strategy.py
    
    Returns:
        (decision: "BUY"|"SELL"|"HOLD", confidence: 0-100, reasoning: str)
    """
    logger.info(f"Initiating AI consensus for {symbol}")
    
    # Parallel execution of 4 council providers
    council_opinions = []
    providers = [
        ("groq", _call_groq),
        ("openrouter", _call_openrouter),
        ("mistral", _call_mistral),
        ("huggingface", _call_huggingface),
    ]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all calls
        future_to_provider = {
            executor.submit(fn, market_dossier): name 
            for name, fn in providers
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_provider, timeout=11):
            provider_name = future_to_provider[future]
            try:
                result = future.result()
                if result and isinstance(result, dict) and _validate_council_response(result):
                    council_opinions.append({
                        "provider": provider_name,
                        "lean": result.get("lean", "HOLD").upper(),
                        "confidence": int(result.get("confidence", 50)),
                        "reason": result.get("reason", "")
                    })
                    logger.debug(f"{provider_name}: {result['lean']} ({result['confidence']}%)")
            except concurrent.futures.TimeoutError:
                logger.warning(f"{provider_name}: Timeout exceeded")
            except Exception as e:
                logger.warning(f"{provider_name}: Exception - {e}")
    
    # If no council responses, still query judge with fallback
    if not council_opinions:
        logger.warning("No council opinions gathered - querying Judge with fallback")
        council_opinions = [{"provider": "fallback", "lean": "NEUTRAL", "confidence": 50}]
    
    # Obtain Supreme Judge verdict
    decision, confidence, note = _call_gemini_judge(market_dossier, council_opinions)
    
    # Enforce confidence threshold
    if confidence < CONFIDENCE_THRESHOLD:
        logger.info(f"Confidence {confidence}% < {CONFIDENCE_THRESHOLD}% - defaulting to HOLD")
        return "HOLD", confidence, f"Confidence below {CONFIDENCE_THRESHOLD}% threshold. {note}"
    
    return decision, confidence, note

# ==============================================================================
# HEALTH CHECK & DIAGNOSTIC FUNCTIONS
# ==============================================================================

def ai_healthcheck() -> Dict[str, Any]:
    """
    Check all AI provider connectivity and health.
    
    Returns dict with status for each provider.
    """
    health_status = {
        "timestamp": time.time(),
        "providers": {}
    }
    
    test_prompt = "Test: Is BTC trading? Respond with {\"lean\": \"HOLD\", \"confidence\": 50}"
    
    providers_check = [
        ("groq", _call_groq),
        ("openrouter", _call_openrouter),
        ("mistral", _call_mistral),
        ("huggingface", _call_huggingface),
    ]
    
    for name, func in providers_check:
        try:
            result = func(test_prompt)
            health_status["providers"][name] = {
                "status": "OK" if result else "NO_RESPONSE",
                "result": result
            }
        except Exception as e:
            health_status["providers"][name] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    # Check Gemini Judge
    try:
        decision, confidence, note = _call_gemini_judge(
            "Market test dossier",
            [{"provider": "test", "lean": "HOLD", "confidence": 50}]
        )
        health_status["judge"] = {
            "status": "OK",
            "decision": decision,
            "confidence": confidence
        }
    except Exception as e:
        health_status["judge"] = {
            "status": "ERROR",
            "error": str(e)
        }
    
    return health_status

def groq_probe() -> Tuple[bool, str]:
    """Quick connectivity check for Groq."""
    result = _call_groq("Test signal: Respond {\"lean\": \"HOLD\", \"confidence\": 50}")
    if result:
        return True, f"✓ Groq responsive: {result.get('lean')} ({result.get('confidence')}%)"
    return False, "✗ Groq unresponsive or rate-limited"

# ==============================================================================
# END OF multi_ai.py
# ==============================================================================
