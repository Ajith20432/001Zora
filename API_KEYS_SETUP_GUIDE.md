# ZORA v1.2.1+ API KEYS SETUP GUIDE

## Get Your 5 AI Provider Keys (15 minutes total)

This guide walks you through getting **FREE or affordable** API keys for all 5 AI providers.

**Time Required:** ~15 minutes  
**Cost:** Free for testing, paid for production (optional)  
**Difficulty:** Easy (copy-paste)

---

## 📋 WHAT YOU NEED

| Provider | Key Name | Cost | Speed | Use Case |
|----------|----------|------|-------|----------|
| **Groq** | GROQ_API_KEY | Free | ⚡⚡⚡ Fastest | Momentum & price action |
| **OpenRouter** | OPENROUTER_API_KEY | Free | ⚡⚡ Fast | Risk validation & reasoning |
| **Mistral** | MISTRAL_API_KEY | Free | ⚡⚡ Fast | Order flow analysis |
| **HuggingFace** | HUGGINGFACE_API_KEY | Free | ⚡ Moderate | Pattern recognition |
| **Google Gemini** | GEMINI_API_KEY | Free | ⚡⚡ Fast | **SUPREME JUDGE** (critical!) |

**Recommendation:** Get ALL 5 for consensus strength. But minimum: Groq + Gemini.

---

## ⚡ STEP 1: GROQ (5 minutes)

**Why:** Fastest AI (70B parameter Llama model), excellent for crypto analysis, completely free

### Get Your Key

1. Go to: https://console.groq.com/keys
2. Sign up (Google/email - instant)
3. Click "Create API Key"
4. Copy the key (looks like: `gsk_xxxxx...`)
5. Save to `.env`:
   ```
   GROQ_API_KEY=gsk_xxxxx...
   ```

### Test It Works

```bash
python3 << 'EOF'
import requests
import os

key = os.getenv("GROQ_API_KEY")
if not key:
    print("ERROR: GROQ_API_KEY not set")
    exit(1)

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
payload = {
    "model": "llama-3.3-70b-versatile",
    "messages": [
        {"role": "system", "content": "You are a crypto analyst. Respond with JSON: {\"test\": \"OK\"}"},
        {"role": "user", "content": "Test"}
    ],
    "response_format": {"type": "json_object"},
    "temperature": 0.2
}

r = requests.post(url, headers=headers, json=payload, timeout=10)
if r.status_code == 200:
    print("✓ Groq: WORKING")
else:
    print(f"✗ Groq: ERROR {r.status_code}")
EOF
```

**Expected Output:** `✓ Groq: WORKING`

---

## 🔄 STEP 2: OPENROUTER (3 minutes)

**Why:** Auto-selects best available model, deep reasoning, cross-validation

### Get Your Key

1. Go to: https://openrouter.ai/keys
2. Sign up (Google/GitHub - instant)
3. Click "Create Key"
4. Copy the key (looks like: `sk-or-xxxxx...`)
5. Save to `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-xxxxx...
   ```

### Test It Works

```bash
python3 << 'EOF'
import requests
import os

key = os.getenv("OPENROUTER_API_KEY")
if not key:
    print("ERROR: OPENROUTER_API_KEY not set")
    exit(1)

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "zora-bot"
}
payload = {
    "model": "openrouter/auto",
    "messages": [
        {"role": "system", "content": "Respond with: {\"test\": \"OK\"}"},
        {"role": "user", "content": "Test"}
    ],
    "temperature": 0.2
}

r = requests.post(url, headers=headers, json=payload, timeout=10)
if r.status_code == 200:
    print("✓ OpenRouter: WORKING")
else:
    print(f"✗ OpenRouter: ERROR {r.status_code}")
EOF
```

**Expected Output:** `✓ OpenRouter: WORKING`

---

## 🎯 STEP 3: MISTRAL (3 minutes)

**Why:** Algorithmic market structure analysis, excellent reasoning, 7B-80B models available

### Get Your Key

1. Go to: https://console.mistral.ai/api-keys
2. Sign up (email required)
3. Click "+ Create API Key"
4. Copy the key (looks like: `xxx_xxxxxxxxxxxxx`)
5. Save to `.env`:
   ```
   MISTRAL_API_KEY=xxx_xxxxxxxxxxxxx
   ```

### Test It Works

```bash
python3 << 'EOF'
import requests
import os

key = os.getenv("MISTRAL_API_KEY")
if not key:
    print("ERROR: MISTRAL_API_KEY not set")
    exit(1)

url = "https://api.mistral.ai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "mistral-small-latest",
    "messages": [
        {"role": "system", "content": "Respond with: {\"test\": \"OK\"}"},
        {"role": "user", "content": "Test"}
    ],
    "response_format": {"type": "json_object"},
    "temperature": 0.2
}

r = requests.post(url, headers=headers, json=payload, timeout=10)
if r.status_code == 200:
    print("✓ Mistral: WORKING")
else:
    print(f"✗ Mistral: ERROR {r.status_code}")
EOF
```

**Expected Output:** `✓ Mistral: WORKING`

---

## 🤗 STEP 4: HUGGINGFACE (2 minutes)

**Why:** Open-weights models (Qwen, DeepSeek), diverse perspective, free tier available

### Get Your Key

1. Go to: https://huggingface.co/settings/tokens
2. Sign up (GitHub/Google/email - instant)
3. Click "New token"
4. Choose "Read" permission
5. Copy the token (looks like: `hf_xxxxxxxxxxxxx`)
6. Save to `.env`:
   ```
   HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx
   ```

### Test It Works

```bash
python3 << 'EOF'
import requests
import os

key = os.getenv("HUGGINGFACE_API_KEY")
if not key:
    print("ERROR: HUGGINGFACE_API_KEY not set")
    exit(1)

url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-72B-Instruct"
headers = {"Authorization": f"Bearer {key}"}
payload = {
    "inputs": "Respond with: {\"test\": \"OK\"}",
    "parameters": {"max_new_tokens": 100}
}

r = requests.post(url, headers=headers, json=payload, timeout=10)
if r.status_code == 200:
    print("✓ HuggingFace: WORKING")
else:
    print(f"✗ HuggingFace: {r.status_code}")
    print(r.text[:200])
EOF
```

**Expected Output:** `✓ HuggingFace: WORKING`

---

## 🏆 STEP 5: GOOGLE GEMINI (3 minutes) — CRITICAL!

**Why:** Gemini-2.0-Flash is your **SUPREME JUDGE** - synthesizes all 4 opinions, completely free

### Get Your Key

1. Go to: https://aistudio.google.com/app/apikeys
2. Sign in with Google (required)
3. Click "Create API key in new project"
4. Copy the key (looks like: `AIzaSyxxxxxxxxxxxxxxxx`)
5. Save to `.env`:
   ```
   GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxx
   ```

### Test It Works

```bash
python3 << 'EOF'
import requests
import os

key = os.getenv("GEMINI_API_KEY")
if not key:
    print("ERROR: GEMINI_API_KEY not set")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
headers = {"Content-Type": "application/json"}
payload = {
    "contents": [
        {
            "parts": [
                {"text": "Respond with valid JSON only: {\"test\": \"OK\"}"}
            ]
        }
    ],
    "generationConfig": {"temperature": 0.1}
}

r = requests.post(url, headers=headers, json=payload, timeout=10)
if r.status_code == 200:
    print("✓ Gemini: WORKING")
else:
    print(f"✗ Gemini: ERROR {r.status_code}")
    print(r.text[:200])
EOF
```

**Expected Output:** `✓ Gemini: WORKING`

---

## 📝 EXAMPLE .ENV FILE (AFTER ALL KEYS)

```bash
# Exchange & Trading
EXCHANGE_ID=htx
SYMBOLS=ETH/USDT,BTC/USDT
TRADING_MODE=paper
INITIAL_CAPITAL=1000

# AI PROVIDERS (ALL 5 REQUIRED)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxxx
MISTRAL_API_KEY=xxx_xxxxxxxxxxxxxxxxxxxxx
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxx

# Risk Management
MAX_RISK_PER_TRADE_PCT=0.02
DAILY_DRAWDOWN_LIMIT_PCT=0.04
MAX_OPEN_POSITIONS=5
MAX_POSITION_SIZE_PCT=0.10

# Take-Profit Scaling
TP1_RR=1.5
TP2_RR=3.0
RUNNER_TRAIL_ATR_MULT=2.0

# Intra-Candle
INTRA_CANDLE_DETECTION_ENABLED=true
VOLUME_SPIKE_THRESHOLD=2.5

# Monitoring
DASHBOARD_PORT=5000
LOG_LEVEL=INFO

# Database
DB_PATH=./zora.db
```

---

## ✅ VERIFICATION SCRIPT

Run this after setting all keys:

```bash
python3 << 'EOF'
import os
import requests
import json

print("=" * 70)
print("ZORA API KEYS VERIFICATION")
print("=" * 70)

providers = {
    "GROQ": {
        "key_var": "GROQ_API_KEY",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
        "payload": {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": "test"}],
            "temperature": 0.2,
            "max_tokens": 10
        }
    },
    "OpenRouter": {
        "key_var": "OPENROUTER_API_KEY",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
        "payload": {
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": "test"}],
            "temperature": 0.2,
            "max_tokens": 10
        }
    },
    "Mistral": {
        "key_var": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "headers_fn": lambda k: {"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
        "payload": {
            "model": "mistral-small-latest",
            "messages": [{"role": "user", "content": "test"}],
            "temperature": 0.2,
            "max_tokens": 10
        }
    },
    "Gemini": {
        "key_var": "GEMINI_API_KEY",
        "url": lambda k: f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={k}",
        "headers_fn": lambda k: {"Content-Type": "application/json"},
        "payload": {
            "contents": [{"parts": [{"text": "test"}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 10}
        }
    }
}

results = {}
for name, config in providers.items():
    key = os.getenv(config["key_var"], "").strip()
    
    if not key:
        results[name] = "MISSING"
        print(f"  ✗ {name:15} MISSING (set {config['key_var']})")
        continue
    
    try:
        url = config["url"] if isinstance(config["url"], str) else config["url"](key)
        headers = config["headers_fn"](key)
        payload = config["payload"]
        
        r = requests.post(url, headers=headers, json=payload, timeout=8)
        
        if r.status_code == 200:
            results[name] = "OK"
            print(f"  ✓ {name:15} OK")
        elif r.status_code == 401:
            results[name] = "INVALID_KEY"
            print(f"  ✗ {name:15} INVALID KEY")
        elif r.status_code in (429, 500, 503):
            results[name] = "RATE_LIMITED"
            print(f"  ⚠ {name:15} Rate limited (will retry)")
        else:
            results[name] = f"ERROR_{r.status_code}"
            print(f"  ✗ {name:15} ERROR {r.status_code}")
    
    except requests.Timeout:
        results[name] = "TIMEOUT"
        print(f"  ⚠ {name:15} Timeout (network issue)")
    except Exception as e:
        results[name] = "ERROR"
        print(f"  ✗ {name:15} ERROR: {str(e)[:30]}")

print()
print("=" * 70)
ok_count = sum(1 for v in results.values() if v == "OK")
print(f"Result: {ok_count}/5 providers working")
print("=" * 70)

if ok_count >= 2:
    print("✓ Ready to deploy! (minimum Groq + Gemini working)")
else:
    print("✗ Need at least 2 providers working before deployment")
    print("  Required: GROQ_API_KEY and GEMINI_API_KEY")

EOF
```

---

## 🛠️ TROUBLESHOOTING API KEYS

### "Invalid API Key"

**Solution:**
1. Double-check you copied the entire key (including `gsk_`, `sk-or-`, etc.)
2. Make sure there are no extra spaces
3. Delete the key and create a new one
4. Paste into `.env` and retry

### "Rate Limited (429)"

**Normal behavior!** These are free tiers with rate limits.

**Solution:**
- Code has automatic 90-second cooldown
- Just wait and retry
- For production: upgrade to paid tier (usually $5-10/month)

### "Timeout"

**Usually network issue**

**Solution:**
- Check internet connection
- Try again in a few seconds
- Increase `AI_PROVIDER_TIMEOUT_SEC=15` in `.env`

### "No such file or directory: .env"

**Solution:**
```bash
cp .env.example .env
nano .env  # Add your keys
```

---

## 💰 COST BREAKDOWN (Monthly)

For a bot trading 5-10 times per day:

| Provider | Free Tier | Typical Cost |
|----------|-----------|--------------|
| **Groq** | 30,000 reqs/day | Free for most users |
| **OpenRouter** | Free credits | $0-5/month |
| **Mistral** | 100,000 tokens/month | Free for most users |
| **HuggingFace** | Free tier | Free for most users |
| **Gemini** | 60 requests/minute | Free for most users |
| **TOTAL** | All free | **$0-10/month** |

**Recommendation:** Start free. Upgrade if needed.

---

## 🔒 SECURITY BEST PRACTICES

### ✅ DO:
- Store keys in `.env` only
- Never commit `.env` to Git
- Use separate keys for paper vs live trading
- Rotate keys monthly
- Keep backups of working keys

### ❌ DON'T:
- Paste keys in code
- Share keys in Slack/email
- Commit `.env` to version control
- Log keys in console output
- Use same key for multiple bots

---

## ⚡ QUICK REFERENCE

```bash
# Set all keys at once (if in same terminal session)
export GROQ_API_KEY="gsk_xxxxx"
export OPENROUTER_API_KEY="sk-or-xxxxx"
export MISTRAL_API_KEY="xxx_xxxxx"
export HUGGINGFACE_API_KEY="hf_xxxxx"
export GEMINI_API_KEY="AIzaSy_xxxxx"

# Load from .env (Termux)
export $(cat .env | xargs)

# Verify one key
echo $GROQ_API_KEY

# Test all keys
python3 /path/to/verify_script.py
```

---

## ✅ YOU'RE DONE!

After getting all 5 keys:

1. ✅ Keys saved in `.env`
2. ✅ All 5 providers tested and working
3. ✅ Ready to deploy bot
4. ✅ Follow `DEPLOYMENT_QUICKSTART.txt` next

**Next Step:** Run the bot in paper mode for 2+ weeks

---

**Version:** ZORA v1.2.1+  
**Updated:** October 2026  
**Status:** Complete API Key Setup
