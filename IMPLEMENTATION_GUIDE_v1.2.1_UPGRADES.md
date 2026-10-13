# ZORA v1.2.1+ UPGRADES - IMPLEMENTATION GUIDE

## 📋 EXECUTIVE SUMMARY

This guide walks you through integrating the upgraded ZORA system with:
- **5-AI Expert Council** (Groq, OpenRouter, Mistral, HuggingFace) + **Google Gemini Supreme Judge**
- **Autonomous Market Dossier Packager** (replaces rigid indicator rules)
- **Hybrid Triggering** (candle close + intra-candle volume/breakout)
- **Advanced Risk Management** (1.5R partial TP, auto-breakeven, trailing runner)
- **Dynamic Position Sizing** (1-2% risk based on volatility)

**Target Platform:** Android Termux (Python 3.11+, `requests` only, no C-extensions)

---

## 🎯 FILES TO REPLACE/UPGRADE

| File | Status | Description |
|------|--------|-------------|
| `multi_ai.py` | **REPLACE** | Enhanced 5-AI council with improved error handling |
| `strategy.py` | **REPLACE** | AI-centric dossier packager + intra-candle detection |
| `risk.py` | **REPLACE** | Advanced risk engine with partial TP scaling |
| `config.py` | **REPLACE** | Extended configuration with all new parameters |
| `.env` | **UPDATE** | Add new API keys and settings |

---

## 📦 STEP 1: DOWNLOAD UPGRADED FILES

All 5 upgraded files are provided:
1. `multi_ai_UPGRADED.py`
2. `strategy_UPGRADED.py`
3. `risk_UPGRADED.py`
4. `config_UPGRADED.py`
5. `.env.example_UPGRADED`

### Backup Current Files

```bash
# On your Termux/Android device:
cd ~/zora_advanced_bot/master_quant_original

# Backup originals
cp multi_ai.py multi_ai.py.backup
cp strategy.py strategy.py.backup
cp risk.py risk.py.backup
cp config.py config.py.backup
```

---

## 🚀 STEP 2: INSTALL UPGRADED FILES

### Copy New Files

```bash
# Copy each upgraded file (rename to remove _UPGRADED suffix)
cp ~/Downloads/multi_ai_UPGRADED.py ./multi_ai.py
cp ~/Downloads/strategy_UPGRADED.py ./strategy.py
cp ~/Downloads/risk_UPGRADED.py ./risk.py
cp ~/Downloads/config_UPGRADED.py ./config.py
```

### Update .env Configuration

```bash
# Copy example with all new variables
cp ~/Downloads/.env.example_UPGRADED .env.example

# Edit your .env file with ALL required values
nano .env
```

**Critical Variables to Set:**

```bash
# AI Provider Keys (ALL REQUIRED for 5-AI consensus)
GROQ_API_KEY=<your_groq_key>
OPENROUTER_API_KEY=<your_openrouter_key>
MISTRAL_API_KEY=<your_mistral_key>
HUGGINGFACE_API_KEY=<your_huggingface_key>
GEMINI_API_KEY=<your_gemini_key>  # SUPREME JUDGE - critical!

# Risk Parameters
MAX_RISK_PER_TRADE_PCT=0.02         # 2% per trade
DAILY_DRAWDOWN_LIMIT_PCT=0.04       # 4% circuit breaker
MAX_OPEN_POSITIONS=5

# Take-Profit Scaling
TP1_RR=1.5                          # 50% close at 1.5R, move SL to BE
TP2_RR=3.0                          # 25% close at 3.0R
RUNNER_TRAIL_ATR_MULT=2.0           # Trail runner at 2x ATR

# Intra-Candle Triggering
INTRA_CANDLE_DETECTION_ENABLED=true
VOLUME_SPIKE_THRESHOLD=2.5          # Trigger on 2.5x volume
```

---

## ✅ STEP 3: VERIFY INSTALLATION

### Check Syntax

```bash
# Verify Python syntax (no compilation errors)
python3 -m py_compile multi_ai.py strategy.py risk.py config.py
# Should output nothing if OK

# Or more verbose:
python3 << 'EOF'
import multi_ai
import strategy
import risk
import config
print("✓ All modules imported successfully")
print(f"✓ Configuration loaded: {config.CFG.symbols}")
EOF
```

### Test Configuration Loading

```bash
python3 << 'EOF'
from config import CFG

print("=== CONFIGURATION VERIFICATION ===")
print(f"Exchange: {CFG.exchange_id}")
print(f"Symbols: {CFG.symbols}")
print(f"Mode: {CFG.trading_mode}")
print(f"Risk per trade: {CFG.max_risk_per_trade_pct*100:.1f}%")
print(f"Daily DD limit: {CFG.daily_drawdown_limit_pct*100:.1f}%")
print(f"AI providers: {CFG.ai_providers_available}/4 council + Judge")
print(f"Min confidence: {CFG.ai_min_confidence}%")
print(f"Intra-candle triggers: {'ENABLED' if CFG.intra_candle_detection_enabled else 'DISABLED'}")
print(f"TP1 @ {CFG.tp1_rr}R | TP2 @ {CFG.tp2_rr}R")
EOF
```

### Test AI Provider Health

```bash
python3 << 'EOF'
import multi_ai

print("Testing AI provider connectivity...")
health = multi_ai.ai_healthcheck()

for provider, status in health.get("providers", {}).items():
    result = "✓" if status.get("status") == "OK" else "✗"
    print(f"  {result} {provider}: {status.get('status')}")

judge_status = health.get("judge", {}).get("status")
judge_result = "✓" if judge_status == "OK" else "✗"
print(f"  {judge_result} Gemini Judge: {judge_status}")
EOF
```

---

## 🧠 STEP 4: UNDERSTAND THE NEW ARCHITECTURE

### 5-AI Expert Council Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Market Data (OHLCV)                                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ strategy.py: Build Market Dossier                               │
│ ├─ Technical Indicators (RSI, MACD, ATR, EMAs)                 │
│ ├─ Market Regime Detection (BULLISH/BEARISH/RANGING/BREAKOUT)  │
│ ├─ Smart Money Concepts (FVG, Liquidity Sweeps)                │
│ ├─ Sentiment (News, Fear & Greed)                              │
│ └─ Intra-Candle Trigger Check                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ multi_ai.py: 5-AI Parallel Council                             │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Concurrent Evaluation (ThreadPoolExecutor)                  ││
│ │  • Groq: Momentum & Price Action                           ││
│ │  • OpenRouter: Risk Validation & Deep Reasoning            ││
│ │  • Mistral: Algorithmic Market Structure                   ││
│ │  • HuggingFace: Deep Market Pattern Recognition            ││
│ └─────────────────────────────────────────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ multi_ai.py: Gemini-2.0-Flash Supreme Judge                    │
│ ├─ Bayesian Weighting (provider historical accuracy)          │
│ ├─ Resolve Conflicting Signals                                │
│ ├─ Risk-Reward Validation                                      │
│ └─ OUTPUT: {"decision": BUY|SELL|HOLD, "confidence": 0-100}   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ risk.py: Risk Guard (Overrides AI if needed)                   │
│ ├─ Enforce Confidence Threshold (>=75%)                        │
│ ├─ Check Circuit Breaker (4% daily DD)                         │
│ ├─ Verify Max Positions (5 open limit)                         │
│ ├─ Calculate Dynamic Position Size                             │
│ └─ OUTPUT: Approved or Rejected                                │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ execution.py: Place Order (if approved)                        │
│ └─ Monitor for Partial TP Scaling                             │
└─────────────────────────────────────────────────────────────────┘
```

### Market Dossier Example

The `strategy.py` builds this AI-friendly dossier (instead of rigid if-then rules):

```
MARKET ANALYSIS: ETH/USDT | 2026-10-12 14:30:00
======================================================================

PRICE ACTION:
  Current Price: $2345.67
  24h High: $2380.00 | 24h Low: $2100.00 | Range: $280.00
  Price Position in 24h Range: 87.4%
  Latest Candle: +1.25%

TECHNICAL INDICATORS:
  RSI(14): 68.5
  MACD=245.32, Signal=238.50, Hist=6.82
  ATR(14): 45.20 (1.93% of price)
  EMA20=2340.50 vs EMA50=2320.00 vs EMA200=2180.00

MARKET REGIME: TRENDING_BULLISH

SMART MONEY STRUCTURE:
  Liquidity Sweep: BEARISH_WICK
  Fair Value Gaps: 3 active FVG zones

MARKET SENTIMENT: GREEDY (FGI: 78)
```

The 5 AI providers read this dossier and form opinions. Gemini Judge synthesizes them with Bayesian weighting.

---

## 🔧 STEP 5: INTEGRATE WITH EXISTING BOT

### Update bot.py to Use New Modules

```python
# In bot.py, update imports
from strategy import evaluate  # New dossier-based evaluator
from risk import RISK  # New advanced risk manager
from config import CFG  # New config with extended vars
import multi_ai  # Enhanced multi-AI

# When evaluating strategy (candle close):
decision, confidence, note = evaluate(
    symbol="ETH/USDT",
    df=df_15m,
    current_price=current_price,
    current_volume=current_volume,
    is_intra_candle=False  # Routine 15m evaluation
)

# When intra-candle trigger detected:
decision, confidence, note = evaluate(
    symbol="ETH/USDT",
    df=df_15m,
    current_price=current_price,
    current_volume=current_volume,
    is_intra_candle=True  # Fast-track evaluation
)

# Check position sizing and risk
if decision in ("BUY", "SELL"):
    can_open, reason = RISK.can_open_new_position()
    if not can_open:
        logger.warning(f"Cannot open position: {reason}")
        decision = "HOLD"
    else:
        # Calculate size
        position_size = RISK.calculate_position_size(
            entry_price=current_price,
            stop_loss_price=calculated_sl,
            atr_value=atr_val
        )
        
        # Register position
        RISK.register_open_position(
            symbol="ETH/USDT",
            entry_price=current_price,
            position_size=position_size,
            stop_loss=calculated_sl,
            side=decision
        )

# Monitor for partial take-profits (every price tick)
tp_action = RISK.check_partial_takeprofits(
    symbol="ETH/USDT",
    entry_price=position.entry,
    current_price=current_price,
    stop_loss_price=position.stop,
    side=position.side
)

if tp_action["action"] == "CLOSE_PARTIAL":
    # Close specified % at TP price
    pct_to_close = tp_action["percent_to_close"]
    # Update stop loss to new_stop (may be breakeven)
    # Continue runner with trailing stop
```

### Update Data Polling (Intra-Candle Monitoring)

```python
# Background thread monitoring intra-candle events (every 10s)
def intra_candle_monitor_loop():
    while True:
        time.sleep(10)  # Poll every 10 seconds
        
        for symbol in CFG.symbols:
            try:
                # Get latest tick price and volume
                ticker = exchange.fetch_ticker(symbol)
                current_price = ticker["last"]
                current_volume = ticker.get("quoteVolume", 0)
                
                # This automatically triggers fast-track evaluation
                # if volume/breakout detected
                from strategy import _intra_candle_monitor
                if _intra_candle_monitor.check_intra_candle_trigger(
                    current_price, current_volume
                ):
                    logger.warning(
                        f"INTRA-CANDLE TRIGGER for {symbol} - "
                        f"initiating fast-track AI evaluation"
                    )
                    # Trigger immediate consensus evaluation
                    evaluate(symbol, df, current_price, current_volume, 
                            is_intra_candle=True)
            
            except Exception as e:
                logger.debug(f"Intra-candle monitor error: {e}")

# Start background thread
import threading
thread = threading.Thread(target=intra_candle_monitor_loop, daemon=True)
thread.start()
```

---

## 🛡️ STEP 6: VERIFY SAFETY GUARDRAILS

### Daily Circuit Breaker Test

```python
from risk import RISK

# Simulate hitting 4% daily loss
RISK.daily_start_equity = 1000.0
RISK.equity = 960.0  # 4% loss

RISK.update_equity(960.0)

if RISK.halted:
    print("✓ Circuit breaker activated correctly")
    can_open, reason = RISK.can_open_new_position()
    print(f"  Can open new position: {can_open}")
    print(f"  Reason: {reason}")
```

### Risk Sizing Verification

```python
from risk import RISK

size = RISK.calculate_position_size(
    entry_price=2350.0,
    stop_loss_price=2300.0,  # 50pt stop
    atr_value=45.0           # ATR = 1.9% of price
)

print(f"Position size: {size:.4f} ETH")
print(f"Risk amount: {(size * 50):.2f} USD")
print(f"Risk %: {((size * 50) / 1000 * 100):.2f}%")
```

### Partial TP Test

```python
from risk import RISK

# Simulate position up 1.5R
tp_action = RISK.check_partial_takeprofits(
    symbol="ETH/USDT",
    entry_price=2350.0,
    current_price=2425.0,     # $75 profit = 1.5R
    stop_loss_price=2300.0,   # $50 stop
    side="BUY"
)

print(f"Action: {tp_action['action']}")
print(f"Stage: {tp_action['stage']}")
print(f"Close: {tp_action['percent_to_close']*100:.0f}%")
print(f"New SL: {tp_action['new_stop_loss']:.2f}")  # Should be 2350.0 (breakeven)
```

---

## 📊 STEP 7: MONITOR OPERATION

### Key Metrics to Track

```
Daily Dashboard Checks:
  ✓ Equity growth (should compound)
  ✓ Win rate (% of profitable trades)
  ✓ Average R multiple
  ✓ Sharpe ratio
  ✓ Max drawdown vs limit (4%)
  ✓ AI provider availability (4/4 council + judge)
  ✓ Number of intra-candle triggers
  ✓ TP1/TP2/Runner execution rates
```

### Log Monitoring

```bash
# Monitor logs in real-time
tail -f ~/zora_advanced_bot/logs/zora.log | grep -E "(TRIGGER|Judge|TP[12]|CIRCUIT|ERROR)"

# Look for key signals
grep "Judge verdict" ~/zora_advanced_bot/logs/zora.log
grep "TP1 triggered" ~/zora_advanced_bot/logs/zora.log
grep "CIRCUIT BREAKER" ~/zora_advanced_bot/logs/zora.log
```

---

## 🚨 TROUBLESHOOTING

### AI Provider Timeout

**Symptom:** `Groq: Request timeout`

**Solution:**
```bash
# Increase timeout in config
AI_PROVIDER_TIMEOUT_SEC=15  # Default 12, increase to 15
```

### Gemini Judge Unavailable

**Symptom:** All trades default to HOLD, judge unreachable

**Solution:**
```bash
# Verify Gemini API key
echo $GEMINI_API_KEY  # Should be non-empty

# Test Gemini directly
python3 << 'EOF'
import requests, os
key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
r = requests.post(url, json={"contents": [{"parts": [{"text": "test"}]}]})
print(f"Status: {r.status_code}")
EOF
```

### Intra-Candle Not Triggering

**Symptom:** Volume spikes not triggering fast-track evaluation

**Solution:**
```bash
# Check threshold setting
VOLUME_SPIKE_THRESHOLD=2.5  # Increase sensitivity (2.0 = more triggers)

# Verify 20-period average volume is being calculated
# Check logs for: "Baseline update"
```

### Circuit Breaker Too Sensitive

**Symptom:** Trading halts too often

**Solution:**
```bash
# Increase daily drawdown limit (use with caution!)
DAILY_DRAWDOWN_LIMIT_PCT=0.06  # 6% instead of 4%

# Or reduce risk per trade
MAX_RISK_PER_TRADE_PCT=0.01  # 1% instead of 2%
```

---

## 🎯 BEST PRACTICES

### 1. Start in Paper Mode

```bash
TRADING_MODE=paper
INITIAL_CAPITAL=10000  # Paper trading capital
```

Run for **at least 2 weeks** before going live. Verify:
- AI consensus quality (check advisor accuracy logs)
- Risk management effectiveness
- Intra-candle trigger rate
- Partial TP execution (should hit 50-70%)

### 2. Monitor Daily Equity

```python
# Log daily equity at market open
Daily PnL = (Current Equity / Start Equity) - 1
Cumulative PnL = (Current Equity / Initial Capital) - 1
```

### 3. Verify Each AI Provider Weekly

```bash
python3 << 'EOF'
import multi_ai
health = multi_ai.ai_healthcheck()
for p, s in health["providers"].items():
    print(f"{p}: {s['status']}")
EOF
```

### 4. Keep Backups

```bash
# Weekly backup of .env and db
cp .env .env.backup.$(date +%Y%m%d)
cp zora.db zora.db.backup.$(date +%Y%m%d)
```

---

## 📞 SUPPORT

### Files Provided

- ✅ `multi_ai_UPGRADED.py` - Full 5-AI with Gemini Judge
- ✅ `strategy_UPGRADED.py` - Dossier packager + intra-candle
- ✅ `risk_UPGRADED.py` - Advanced risk with partial TP
- ✅ `config_UPGRADED.py` - Full config parser
- ✅ `.env.example_UPGRADED` - All variables documented

### Quick Checklist

- [ ] Backup existing files
- [ ] Copy upgraded files
- [ ] Update .env with all API keys
- [ ] Verify syntax with `py_compile`
- [ ] Test configuration loading
- [ ] Run AI healthcheck
- [ ] Test in paper mode for 2 weeks
- [ ] Monitor equity curve
- [ ] Verify partial TP execution
- [ ] Check intra-candle triggers
- [ ] Go live with caution

---

## 🎉 YOU'RE READY!

Your ZORA bot is now running:
✅ 5-AI Expert Council consensus (not single black-box AI)  
✅ Autonomous market dossier (no more rigid indicator rules)  
✅ Hybrid triggering (candle close + intra-candle breaks)  
✅ Advanced risk management (1.5R partial TP, auto-BE, trailing runner)  
✅ Dynamic position sizing (1-2% based on volatility)  
✅ Daily circuit breaker (4% protection)  
✅ Production-grade error handling (Termux-compatible)

**Deploy with confidence!** 🚀

---

**Version:** ZORA v1.2.1+  
**Date:** October 2026  
**Platform:** Android Termux, Python 3.11+  
**Status:** Production-Ready
