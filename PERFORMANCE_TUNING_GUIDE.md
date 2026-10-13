# ZORA v1.2.1+ PERFORMANCE TUNING GUIDE

## Optimize Your Bot for Maximum Profitability

**Topics:**
- AI provider configuration (response time vs cost)
- Risk parameters tuning
- Intra-candle sensitivity adjustment
- Database optimization
- Network optimization
- Memory management

---

## 📊 PERFORMANCE BASELINE

Default configuration targets:

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | <3s (4 providers parallel) | 2-3s |
| AI Consensus Quality | 75%+ confidence | Depends on market |
| Trade Frequency | 5-20/day (configurable) | Depends on volume |
| Win Rate | >50% | Historical dependent |
| Profit Factor | >1.5 | Market dependent |
| Memory Usage | <200 MB | ~150 MB |
| CPU Usage | <50% | Depends on load |
| Daily Downtime | <0.5% | 99.5%+ uptime |

---

## ⚙️ TIER 1: AI PROVIDER OPTIMIZATION

### Scenario A: Maximum Speed (Minimum Latency)

**Best for:** High-frequency scalping, intra-candle triggers

```bash
# In .env:
AI_PROVIDER_TIMEOUT_SEC=10           # Faster timeout
AI_RESPONSE_CACHE_TTL_SEC=600        # 10-min cache
GROQ_API_KEY=xxx                     # Fast + free
OPENROUTER_API_KEY=                  # Skip (slow)
MISTRAL_API_KEY=                     # Skip (slow)
HUGGINGFACE_API_KEY=                 # Skip (very slow)
GEMINI_API_KEY=xxx                   # Judge (required)
```

**Result:** ~2s consensus time, uses fast Groq + Gemini judge

**Tradeoff:** Less diverse opinions, slightly lower accuracy

---

### Scenario B: Balanced (Recommended Default)

**Best for:** Most traders, all market conditions

```bash
# In .env:
AI_PROVIDER_TIMEOUT_SEC=12           # Default
AI_RESPONSE_CACHE_TTL_SEC=300        # 5-min cache
GROQ_API_KEY=xxx                     # Fast momentum
OPENROUTER_API_KEY=xxx               # Reasoning
MISTRAL_API_KEY=xxx                  # Order flow
HUGGINGFACE_API_KEY=xxx              # Patterns
GEMINI_API_KEY=xxx                   # Judge
```

**Result:** ~3s consensus time, 4 opinions + judge

**Tradeoff:** Balanced speed/accuracy

---

### Scenario C: Maximum Accuracy (Highest Confidence)

**Best for:** Conservative trading, swing positions

```bash
# In .env:
AI_PROVIDER_TIMEOUT_SEC=15           # Longer timeout
AI_RESPONSE_CACHE_TTL_SEC=0          # No cache
GROQ_API_KEY=xxx                     # Include all
OPENROUTER_API_KEY=xxx               # providers
MISTRAL_API_KEY=xxx                  # for maximum
HUGGINGFACE_API_KEY=xxx              # consensus
GEMINI_API_KEY=xxx                   # Judge (required)
```

**Result:** ~5s consensus time, maximum diversity

**Tradeoff:** Slower, but higher confidence in decisions

---

## ⚡ TIER 2: INTRA-CANDLE TRIGGER TUNING

### Conservative (Fewer False Signals)

```bash
INTRA_CANDLE_DETECTION_ENABLED=true
VOLUME_SPIKE_THRESHOLD=3.5           # Only 3.5x+ spikes
INTRA_CANDLE_COOLDOWN_SEC=120        # 2-min wait between triggers
```

**Result:** 2-3 triggers/day, high quality

**Best for:** Risk-averse traders

---

### Balanced (Default)

```bash
INTRA_CANDLE_DETECTION_ENABLED=true
VOLUME_SPIKE_THRESHOLD=2.5           # 2.5x+ spikes
INTRA_CANDLE_COOLDOWN_SEC=60         # 1-min wait
```

**Result:** 5-10 triggers/day

**Best for:** Most traders

---

### Aggressive (More Opportunities)

```bash
INTRA_CANDLE_DETECTION_ENABLED=true
VOLUME_SPIKE_THRESHOLD=2.0           # 2.0x+ spikes
INTRA_CANDLE_COOLDOWN_SEC=30         # 30-sec wait
```

**Result:** 15-30 triggers/day, more noise

**Best for:** Experienced traders, high frequency

---

## 💰 TIER 3: RISK PARAMETER TUNING

### Conservative (Low Volatility Settings)

```bash
MAX_RISK_PER_TRADE_PCT=0.01          # 1% per trade
DAILY_DRAWDOWN_LIMIT_PCT=0.02        # 2% daily halt
MAX_OPEN_POSITIONS=3                 # Max 3 positions
MAX_POSITION_SIZE_PCT=0.05           # Max 5% per position
TP1_RR=2.0                           # Higher profit target
TP2_RR=4.0                           # Higher TP2
```

**Result:** ~1-2 trades/day, very low risk

**Best for:** Capital preservation, risk-averse

---

### Balanced (Default)

```bash
MAX_RISK_PER_TRADE_PCT=0.02          # 2% per trade
DAILY_DRAWDOWN_LIMIT_PCT=0.04        # 4% daily halt
MAX_OPEN_POSITIONS=5                 # Max 5 positions
MAX_POSITION_SIZE_PCT=0.10           # Max 10% per position
TP1_RR=1.5                           # Quick profits
TP2_RR=3.0                           # Extended runner
```

**Result:** 5-15 trades/day, balanced growth

**Best for:** Most traders

---

### Aggressive (Growth Focused)

```bash
MAX_RISK_PER_TRADE_PCT=0.03          # 3% per trade
DAILY_DRAWDOWN_LIMIT_PCT=0.06        # 6% daily halt
MAX_OPEN_POSITIONS=8                 # Max 8 positions
MAX_POSITION_SIZE_PCT=0.15           # Max 15% per position
TP1_RR=1.2                           # Aggressive scaling
TP2_RR=2.5                           # Faster TP2
```

**Result:** 20+ trades/day, high growth

**Best for:** Experienced traders, growth phase

⚠️ **WARNING:** Higher risk = higher drawdowns. Requires discipline!

---

## 🗄️ TIER 4: DATABASE OPTIMIZATION

### Monitor Database Size

```bash
# Check current size
du -h zora.db

# If >500 MB, optimize:
sqlite3 zora.db "VACUUM"
sqlite3 zora.db "ANALYZE"

# Archive old trades (keep last 100)
sqlite3 zora.db "DELETE FROM trades WHERE created_at < datetime('now', '-30 days') AND status = 'CLOSED';"
```

### Enable SQLite Performance

Add to `config.py`:

```python
# Enable performance optimizations
os.environ["SQLITE_TMPDIR"] = "/tmp"
os.environ["SQLITE_SORTERREF"] = "262144"  # 256KB
```

### Reduce Logging Verbosity

```bash
# In .env, use INFO instead of DEBUG:
LOG_LEVEL=INFO
```

**Result:** Faster disk writes, less I/O

---

## 🌐 TIER 5: NETWORK OPTIMIZATION

### Use Faster DNS

On Termux:

```bash
# Edit /system/etc/resolv.conf (may need root)
# Or set environment variables
export NAMESERVERS="8.8.8.8 1.1.1.1"
```

### Connection Pooling

The code uses `requests` which doesn't pool by default. To enable:

```bash
pip install requests[use_chardet_on_py3]
pip install urllib3
```

Add to bot.py:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

---

## 💾 TIER 6: MEMORY OPTIMIZATION

### Monitor Memory Usage

```bash
# On Termux:
top -b -n 1 | grep python3

# Should be <300 MB
```

### Reduce Memory Footprint

In `config.py`, disable unused features:

```python
# If you don't use Telegram:
self.telegram_enabled = False

# Limit history lookback (reduce OHLCV cache):
self.history_lookback = 50  # Instead of 96
```

### Optimize DataFrame Storage

In `strategy.py`:

```python
# Convert to more efficient dtypes
df['open'] = df['open'].astype('float32')
df['high'] = df['high'].astype('float32')
df['low'] = df['low'].astype('float32')
df['close'] = df['close'].astype('float32')
df['volume'] = df['volume'].astype('int32')
```

---

## 🎯 TIER 7: RESPONSE CACHING

### Aggressive Caching (For Choppy Markets)

```bash
AI_RESPONSE_CACHE_TTL_SEC=900       # 15-min cache
```

**Effect:** 
- 90% reduction in API calls
- Same opinions for 15 min
- Saves API quota
- May miss fast trend changes

### No Caching (For Trending Markets)

```bash
AI_RESPONSE_CACHE_TTL_SEC=0         # No cache
```

**Effect:**
- Fresh AI evaluation every time
- Catches all trend changes
- Uses more API quota
- May be over-reactive

---

## 📈 TIER 8: CONFIDENCE THRESHOLD TUNING

### Conservative (Only Best Setups)

```bash
AI_MIN_CONFIDENCE=85                 # Only 85%+ confidence
```

**Result:** 2-3 trades/week, very high quality

---

### Balanced (Default)

```bash
AI_MIN_CONFIDENCE=75                 # Standard threshold
```

**Result:** 5-15 trades/day

---

### Aggressive (More Opportunity)

```bash
AI_MIN_CONFIDENCE=65                 # Lower threshold
```

**Result:** 20+ trades/day, more noise

⚠️ **WARNING:** Increasing confidence threshold increases win rate!

---

## 🔍 MONITORING & ADJUSTMENTS

### Daily Metrics to Track

```bash
# Log daily equity change
echo "Daily PnL: $(tail -1 zora.log | grep -o 'Daily.*%')"

# Count trades
sqlite3 zora.db "SELECT COUNT(*) FROM trades WHERE DATE(created_at) = DATE('now');"

# Check win rate
sqlite3 zora.db "SELECT SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)*100.0/COUNT(*) as win_rate FROM trades WHERE status='CLOSED';"
```

### Weekly Optimization Review

1. **Win Rate:** Should be >50%
   - If <50%: confidence is too low, increase to 80%
   - If >65%: can lower confidence to catch more

2. **Average Trade Duration:** Should be 1-4 hours
   - If too long: tighten TP1_RR from 1.5 to 1.2
   - If too short: relax TP1_RR from 1.5 to 1.8

3. **Max Drawdown:** Should stay <4% daily
   - If >4%: reduce MAX_RISK_PER_TRADE_PCT
   - If always <1%: could increase slightly

4. **Sharpe Ratio:** Should be >1.0
   - Calculate: (Average daily return) / (Std Dev daily returns)

---

## 🚀 QUICK OPTIMIZATION RECIPES

### Recipe 1: "I Want Consistent Small Wins"

```bash
AI_MIN_CONFIDENCE=80               # High confidence
MAX_RISK_PER_TRADE_PCT=0.01        # 1% per trade
TP1_RR=1.2                         # Quick take-profit
DAILY_DRAWDOWN_LIMIT_PCT=0.03      # 3% daily halt
INTRA_CANDLE_DETECTION_ENABLED=false  # Fewer triggers
```

**Expected Result:**
- 2-5 trades/day
- >60% win rate
- Smooth equity curve
- ~1-3% monthly return

---

### Recipe 2: "I Want Maximum Growth"

```bash
AI_MIN_CONFIDENCE=70               # Accept more
MAX_RISK_PER_TRADE_PCT=0.03        # 3% per trade
TP1_RR=2.0                         # Let winners run
DAILY_DRAWDOWN_LIMIT_PCT=0.08      # 8% daily halt
INTRA_CANDLE_DETECTION_ENABLED=true   # Catch all
VOLUME_SPIKE_THRESHOLD=2.0
```

**Expected Result:**
- 15-30 trades/day
- 50-55% win rate (but bigger winners)
- Higher equity curve slope
- ~5-15% monthly return
- Higher volatility

⚠️ Requires monitoring!

---

### Recipe 3: "I Want Maximum Safety"

```bash
AI_MIN_CONFIDENCE=85               # Very selective
MAX_RISK_PER_TRADE_PCT=0.005       # 0.5% per trade
TP1_RR=3.0                         # Very high targets
DAILY_DRAWDOWN_LIMIT_PCT=0.02      # 2% daily halt
INTRA_CANDLE_DETECTION_ENABLED=false
MAX_OPEN_POSITIONS=2               # Max 2 trades
```

**Expected Result:**
- 1-2 trades/day
- >65% win rate
- Very smooth equity
- ~0.5-1% monthly return
- Minimal volatility

---

## 🔄 A/B TESTING CHANGES

Never change multiple parameters at once!

### Test Process

1. **Baseline:** Run current settings for 1 week, record metrics
2. **Change ONE parameter**
3. **Run for 1 week** with new setting
4. **Compare metrics** (win rate, Sharpe, drawdown)
5. **Keep if better**, revert if not
6. **Proceed to next parameter**

### Example: Testing TP1_RR

```
Week 1: TP1_RR=1.5 (baseline)
        Win rate: 52%, Avg PnL: $50, Sharpe: 1.1

Week 2: TP1_RR=1.3 (tighter)
        Win rate: 58%, Avg PnL: $42, Sharpe: 1.3 ✓ Better!

Week 3: TP1_RR=1.1 (even tighter)
        Win rate: 62%, Avg PnL: $28, Sharpe: 1.2 (profit per trade dropped)

Decision: Keep TP1_RR=1.3 (best balance)
```

---

## 📊 MONITORING DASHBOARD

Create a weekly summary:

```bash
# Save as check_performance.sh
#!/bin/bash

echo "=== WEEKLY PERFORMANCE SUMMARY ==="
echo ""
echo "Trades This Week:"
sqlite3 zora.db "SELECT COUNT(*) FROM trades WHERE DATE(created_at) > DATE('now', '-7 days');"

echo ""
echo "Win Rate:"
sqlite3 zora.db "SELECT ROUND(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END)*100.0/COUNT(*),1) FROM trades WHERE DATE(created_at) > DATE('now', '-7 days');"

echo ""
echo "Avg P&L per Trade:"
sqlite3 zora.db "SELECT ROUND(AVG(pnl),2) FROM trades WHERE DATE(created_at) > DATE('now', '-7 days');"

echo ""
echo "Max Equity:"
sqlite3 zora.db "SELECT ROUND(MAX(equity),2) FROM equity_log WHERE DATE(timestamp) > DATE('now', '-7 days');"

echo ""
echo "Min Equity:"
sqlite3 zora.db "SELECT ROUND(MIN(equity),2) FROM equity_log WHERE DATE(timestamp) > DATE('now', '-7 days');"
```

---

## ✅ OPTIMIZATION CHECKLIST

Start here:

- [ ] Use balanced default settings (Scenario B)
- [ ] Run paper mode for 1 week
- [ ] Review: win rate, trades/day, max drawdown
- [ ] Identify 1 problem area (too few trades? too much risk?)
- [ ] Test ONE change for 1 week
- [ ] If better, keep it; if not, revert
- [ ] Repeat for next problem area
- [ ] After 4 weeks, you'll have an optimized bot

---

## 🎯 FINAL TUNING GOALS

After 4 weeks of optimization:

| Metric | Conservative | Balanced | Aggressive |
|--------|--------------|----------|-----------|
| Trades/Day | 1-3 | 5-15 | 20-30 |
| Win Rate | >60% | >52% | >50% |
| Profit Factor | >2.0 | >1.5 | >1.2 |
| Sharpe Ratio | >1.5 | >1.0 | >0.8 |
| Monthly Return | 1-3% | 3-10% | 10-20% |
| Max Daily DD | <2% | <4% | <6% |

---

## 🚨 WARNING SIGNS

Stop trading if:

- Win rate drops below 45% (AI not working properly)
- Sharpe ratio < 0.5 (returns too volatile)
- Circuit breaker triggered 2+ days/week (risk too high)
- Equity drops >10% below peak (major issue)
- AI provider uptime <80% (connectivity problem)

**Action:** Roll back last change and investigate

---

**Version:** ZORA v1.2.1+ Performance Tuning  
**Date:** October 2026  
**Last Updated:** v1.2.1+
