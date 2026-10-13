# ZORA v1.2.1+ MIGRATION & ROLLBACK GUIDE

## Upgrading from Old ZORA to New ZORA v1.2.1+

**Time Required:** 10 minutes (5 min upgrade + 5 min rollback if needed)  
**Risk Level:** Low (fully reversible)  
**Downtime:** <1 minute

---

## 📋 PRE-UPGRADE CHECKLIST

Before starting the upgrade:

- [ ] Stop the running bot: `killall python3`
- [ ] Verify backups exist: `ls -la *.bak`
- [ ] All 5 API keys ready in notes
- [ ] Disk space available (>100 MB)
- [ ] No active trades (close all positions first)
- [ ] Database backed up: `cp zora.db zora.db.backup.$(date +%Y%m%d)`

---

## 🚀 UPGRADE PROCESS (5 MINUTES)

### Step 1: Stop Current Bot

```bash
cd ~/zora_advanced_bot/master_quant_original

# Stop gracefully
killall python3
sleep 2

# Verify stopped
pgrep -l python3  # Should be empty
```

### Step 2: Create Backup Set

```bash
# Create dated backup directory
mkdir -p backups/$(date +%Y%m%d)
cd backups/$(date +%Y%m%d)

# Backup ALL current files
cp ../multi_ai.py .
cp ../strategy.py .
cp ../risk.py .
cp ../config.py .
cp ../.env .
cp ../../zora.db .

echo "✓ Backups created at: backups/$(date +%Y%m%d)/"
```

### Step 3: Install Upgraded Files

```bash
cd ~/zora_advanced_bot/master_quant_original

# Copy upgraded files (rename by removing _UPGRADED)
cp ~/Downloads/multi_ai_UPGRADED.py ./multi_ai.py
cp ~/Downloads/strategy_UPGRADED.py ./strategy.py
cp ~/Downloads/risk_UPGRADED.py ./risk.py
cp ~/Downloads/config_UPGRADED.py ./config.py

echo "✓ Upgraded files installed"
```

### Step 4: Update Configuration

```bash
# If .env.example exists, back it up
cp .env .env.old

# Merge new variables from upgraded example
# (Keep your old keys and settings)
nano .env

# ADD THESE NEW LINES (keep your old ones):
# New variables in v1.2.1:
# TP1_RR=1.5
# TP2_RR=3.0
# RUNNER_TRAIL_ATR_MULT=2.0
# INTRA_CANDLE_DETECTION_ENABLED=true
# VOLUME_SPIKE_THRESHOLD=2.5
# etc.

# Or use the provided .env.example_UPGRADED as template:
cp ~/Downloads/.env.example_UPGRADED .env.example
# Manually merge your keys into the new .env
```

### Step 5: Verify Syntax

```bash
# Compile to check for syntax errors
python3 -m py_compile multi_ai.py strategy.py risk.py config.py

# If no output = all OK!
echo "✓ All files syntax OK"
```

### Step 6: Verify Imports

```bash
python3 << 'EOF'
try:
    import multi_ai
    import strategy
    import risk
    import config
    print("✓ All modules import successfully")
    print(f"✓ Config: {config.CFG.symbols}")
    print(f"✓ Risk: {config.CFG.max_risk_per_trade_pct*100:.1f}% per trade")
except Exception as e:
    print(f"✗ Import error: {e}")
    exit(1)
EOF
```

### Step 7: Test AI Providers

```bash
python3 << 'EOF'
import multi_ai
print("Testing AI providers...")
health = multi_ai.ai_healthcheck()

ok_count = 0
for p, s in health.get("providers", {}).items():
    st = "✓" if s.get("status") == "OK" else "✗"
    print(f"  {st} {p}: {s.get('status')}")
    if s.get("status") == "OK":
        ok_count += 1

judge = health.get("judge", {}).get("status")
j_st = "✓" if judge == "OK" else "✗"
print(f"  {j_st} Judge: {judge}")

if ok_count >= 2 and judge == "OK":
    print("\n✓ AI system ready to deploy")
else:
    print("\n⚠ Some providers down, but will retry at runtime")
EOF
```

### Step 8: Start in Paper Mode

```bash
# Always start in paper mode first!
python3 bot.py paper &

sleep 3

# Verify running
curl http://127.0.0.1:5000/health

# Should see JSON response with status
```

### Step 9: Monitor First 15 Minutes

```bash
# Watch logs for errors
tail -f ~/zora_advanced_bot/logs/zora.log

# Look for:
# ✓ "Configuration loaded successfully"
# ✓ "AI consensus for ETH/USDT"
# ✓ "Judge verdict: BUY" (or SELL/HOLD)
# ✗ Any ERROR or CRITICAL messages

# Press Ctrl+C to stop watching
```

---

## ✅ UPGRADE COMPLETE!

If you see:
- ✓ Configuration loaded
- ✓ AI provider responses
- ✓ Judge verdicts
- ✓ Dashboard working

**Then upgrade was successful!**

---

## ⚙️ CONFIGURATION MIGRATION

### New Variables in v1.2.1+

Your old `.env` needs these NEW variables:

```bash
# Take-Profit Scaling (NEW)
TP1_RR=1.5                          # Close 50% at 1.5R
TP2_RR=3.0                          # Close 25% at 3.0R
RUNNER_TRAIL_ATR_MULT=2.0           # Trail runner at 2x ATR

# Intra-Candle Triggering (NEW)
INTRA_CANDLE_DETECTION_ENABLED=true # Enable breakout triggers
VOLUME_SPIKE_THRESHOLD=2.5          # Volume > 2.5x average

# AI Provider Tuning (NEW, optional)
AI_PROVIDER_TIMEOUT_SEC=12          # Timeout for API calls
AI_RESPONSE_CACHE_TTL_SEC=300       # Cache responses 5 min
AI_PROVIDER_MAX_RETRIES=2           # Retry failed calls
RATE_LIMIT_COOLDOWN_SEC=90          # Cooldown after 429

# Extended Monitoring (NEW, optional)
INTRA_CANDLE_COOLDOWN_SEC=60        # Min seconds between triggers
```

### How to Migrate Your .env

**Option A: Merge Manually** (Safest)

```bash
# Keep your old .env, just add new lines
nano .env

# Add the new variables above
# Keep your old API keys and settings unchanged
```

**Option B: Use Template** (Fastest)

```bash
# Backup old .env
cp .env .env.old.$(date +%Y%m%d)

# Copy new template
cp .env.example_UPGRADED .env

# Edit new .env to add your API keys
nano .env
# Paste your GROQ_API_KEY, OPENROUTER_API_KEY, etc.
```

---

## 🔄 ROLLBACK PROCESS (5 MINUTES)

If something goes wrong and you need to revert:

### Quick Rollback (Same Day)

```bash
cd ~/zora_advanced_bot/master_quant_original

# Stop new version
killall python3
sleep 2

# Restore backups
cp backups/$(date +%Y%m%d)/multi_ai.py ./multi_ai.py
cp backups/$(date +%Y%m%d)/strategy.py ./strategy.py
cp backups/$(date +%Y%m%d)/risk.py ./risk.py
cp backups/$(date +%Y%m%d)/config.py ./config.py
cp backups/$(date +%Y%m%d)/.env ./.env

# Restart old version
python3 bot.py paper &

# Verify
curl http://127.0.0.1:5000/health

echo "✓ Rolled back to previous version"
```

### Full Rollback (If Database Corrupted)

```bash
cd ~/zora_advanced_bot/master_quant_original

# Stop bot
killall python3

# Restore files AND database
cp backups/$(date +%Y%m%d)/multi_ai.py ./multi_ai.py
cp backups/$(date +%Y%m%d)/strategy.py ./strategy.py
cp backups/$(date +%Y%m%d)/risk.py ./risk.py
cp backups/$(date +%Y%m%d)/config.py ./config.py
cp backups/$(date +%Y%m%d)/.env ./.env
cp backups/$(date +%Y%m%d)/zora.db ./zora.db

# Restart
python3 bot.py paper &

echo "✓ Full rollback complete"
```

---

## ⚠️ COMMON ISSUES DURING UPGRADE

### Issue: "ModuleNotFoundError: No module named 'multi_ai'"

**Cause:** File copy failed or incomplete

**Solution:**
```bash
# Verify file exists and is readable
ls -la multi_ai.py
file multi_ai.py  # Should show Python script

# If not, recopy:
cp ~/Downloads/multi_ai_UPGRADED.py ./multi_ai.py

# Verify syntax:
python3 -m py_compile multi_ai.py
```

### Issue: "GEMINI_API_KEY not configured"

**Cause:** Missing API key in .env

**Solution:**
1. Get key from: aistudio.google.com/app/apikeys
2. Add to .env: `GEMINI_API_KEY=AIzaSy...`
3. Reload: `export $(cat .env | xargs)`
4. Test: `echo $GEMINI_API_KEY`

### Issue: "Configuration loaded successfully" but no trades

**Cause:** AI confidence below 75% or conflicting signals

**Solution:**
1. Check logs: `tail -f zora.log | grep confidence`
2. This is normal! Takes time to accumulate signal strength
3. Run in paper mode for observation

### Issue: "AI provider timeout"

**Cause:** Network slow or provider down

**Solution:**
```bash
# Increase timeout in .env
AI_PROVIDER_TIMEOUT_SEC=15  # was 12

# Test specific provider:
python3 << 'EOF'
import multi_ai
result = multi_ai._call_groq("test: {\"lean\": \"HOLD\", \"confidence\": 50}")
print(f"Groq result: {result}")
EOF
```

### Issue: "Circuit breaker triggered immediately"

**Cause:** Risk parameters too aggressive or unexpected loss

**Solution:**
1. Check logs: `grep CIRCUIT zora.log`
2. Reduce risk: `MAX_RISK_PER_TRADE_PCT=0.01` (1% instead of 2%)
3. Wait 24 hours or rollback to previous version

---

## 📊 MIGRATION DATA RETENTION

### What Gets Preserved

✅ Trading history (in database)  
✅ Equity curve  
✅ Closed trades & P&L  
✅ All settings in .env  
✅ API key configuration

### What Gets Reset

✅ Open positions (new version has different risk model)  
✅ Stop losses (recalculated in new version)  
✅ Risk cache (cleared on startup)

**Recommendation:** Close all positions before upgrade

---

## 🔐 SAFETY CHECKLIST

Before Upgrading:

- [ ] Backed up all .py files
- [ ] Backed up .env file
- [ ] Backed up zora.db (database)
- [ ] All positions closed
- [ ] API keys saved separately
- [ ] Read this entire guide

After Upgrading:

- [ ] Files syntax validated (py_compile)
- [ ] Imports successful
- [ ] AI providers tested
- [ ] Running in paper mode
- [ ] Logs checked for errors
- [ ] Dashboard responding
- [ ] Can reach rollback backups

---

## 📈 TESTING SEQUENCE

After upgrade, test in this order:

### Hour 1: System Check
```bash
# All systems online?
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/metrics
```

### Hour 2: AI Evaluation
```bash
# Monitor logs for decisions
tail -f zora.log | grep "Judge verdict"

# Expect to see entries like:
# "Judge verdict: BUY (85%) - Strong uptrend with support"
# "Judge verdict: HOLD (45%) - Conflicting signals"
```

### Day 1-3: Paper Trading
- Monitor equity curve (should trend positive)
- Check win rate (should be >50% after noise)
- Verify partial TP execution (1.5R/3.0R)
- Test intra-candle triggers (check logs)

### Week 1-2: Paper Validation
- Consistent positive equity growth
- AI confidence accuracy verified
- All features working correctly
- Circuit breaker tested
- Ready for live deployment

---

## 🆘 GETTING HELP

### If Something Goes Wrong

1. **Stop the bot:** `killall python3`
2. **Check logs:** `tail -n 100 zora.log | grep ERROR`
3. **Rollback:** Follow rollback steps above
4. **Get help:**
   - Check IMPLEMENTATION_GUIDE_v1.2.1_UPGRADES.md
   - Review API_KEYS_SETUP_GUIDE.md
   - Check code docstrings

### Emergency Contacts

- Groq support: https://console.groq.com/docs
- Gemini support: https://support.google.com/generativeai
- OpenRouter: https://openrouter.ai/docs
- Mistral: https://docs.mistral.ai
- HuggingFace: https://huggingface.co/support

---

## ✅ SUCCESSFUL UPGRADE INDICATORS

You'll see these in logs:

```
✓ Configuration loaded successfully
✓ Symbols: ['ETH/USDT']
✓ AI providers: 4/4 council + Judge
✓ Intra-candle detection: ENABLED
✓ Judge verdict: BUY (87%) - Strong momentum setup
✓ TP1 triggered at 1.5R - closing 50%
✓ TP2 triggered at 3.0R - closing 25%
✓ Circuit breaker active for 24 hours (4% daily loss)
```

---

## 📋 UPGRADE VERIFICATION SCRIPT

Save as `verify_upgrade.py`:

```python
#!/usr/bin/env python3
"""Verify upgrade successful"""
import os
import requests
import json

def verify():
    print("\n" + "="*70)
    print("ZORA v1.2.1+ UPGRADE VERIFICATION")
    print("="*70 + "\n")
    
    checks = {
        "Files": [],
        "Configuration": [],
        "API": [],
        "System": []
    }
    
    # File checks
    for f in ["multi_ai.py", "strategy.py", "risk.py", "config.py", ".env"]:
        if os.path.exists(f):
            checks["Files"].append((f"✓ {f} exists", True))
        else:
            checks["Files"].append((f"✗ {f} missing", False))
    
    # Config checks
    from config import CFG
    checks["Configuration"].append((f"✓ Symbols: {CFG.symbols}", True))
    checks["Configuration"].append((f"✓ Risk: {CFG.max_risk_per_trade_pct*100:.1f}%", True))
    checks["Configuration"].append((f"✓ AI providers: {CFG.ai_providers_available}/4", True))
    checks["Configuration"].append((f"✓ TP1: {CFG.tp1_rr}R, TP2: {CFG.tp2_rr}R", True))
    
    # AI checks
    try:
        import multi_ai
        h = multi_ai.ai_healthcheck()
        ok = sum(1 for s in h["providers"].values() if s.get("status") == "OK")
        checks["API"].append((f"✓ {ok}/4 providers online", ok >= 2))
        checks["API"].append((f"✓ Judge: {h.get('judge', {}).get('status')}", 
                            h.get('judge', {}).get('status') == 'OK'))
    except Exception as e:
        checks["API"].append((f"✗ AI check failed: {e}", False))
    
    # Dashboard check
    try:
        r = requests.get("http://127.0.0.1:5000/health", timeout=2)
        checks["System"].append((f"✓ Dashboard: {r.status_code}", r.status_code == 200))
    except:
        checks["System"].append((f"⚠ Dashboard not responding (will start later)", True))
    
    # Print results
    all_ok = True
    for section, items in checks.items():
        print(f"\n{section}:")
        for msg, ok in items:
            print(f"  {msg}")
            if not ok:
                all_ok = False
    
    print("\n" + "="*70)
    if all_ok:
        print("✓ UPGRADE VERIFICATION PASSED - Ready to deploy!")
    else:
        print("✗ Some checks failed - review above")
    print("="*70 + "\n")
    
    return all_ok

if __name__ == "__main__":
    verify()
```

Run: `python3 verify_upgrade.py`

---

## 📞 POST-UPGRADE MONITORING

Monitor these metrics daily:

- **Equity curve:** Should trend +
- **Win rate:** Should be >50%
- **Profit factor:** Should be >1.2
- **Sharpe ratio:** Should be >1.0
- **Max drawdown:** Should stay <4% daily
- **AI provider uptime:** Should be 95%+

---

## 🎉 UPGRADE COMPLETE!

After successful verification:

1. ✅ New ZORA v1.2.1+ running
2. ✅ All 5-AI providers active
3. ✅ Advanced risk management enabled
4. ✅ Paper mode validation running
5. ✅ Ready for live deployment (after 2 weeks)

**Next Step:** Run paper mode for 2+ weeks, then refer to DEPLOYMENT_QUICKSTART.txt for going live.

---

**Version:** ZORA v1.2.1+ Migration Guide  
**Date:** October 2026  
**Last Updated:** v1.2.1+
