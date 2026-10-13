"""
strategy.py — UPGRADED Autonomous Institutional Market Dossier Packager
=========================================================================

Transforms raw OHLCV data into a comprehensive AI-friendly market context:
- Multi-timeframe technical analysis (15m, 1h, 4h)
- Market regime classification (Trending/Ranging/Breakout/High-Volatility)
- Smart Money Concepts (Liquidity sweeps, FVG detection, Support/Resistance)
- Sentiment aggregation (News, Fear & Greed Index)
- Intra-candle volume/price breakout triggers

Feeds structured dossier to 5-AI consensus engine, bypassing rigid indicator thresholds.
"""
from __future__ import annotations

import logging
import json
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

# Import dependencies - these must be available in the environment
try:
    import indicators
    import patterns
    import news_feed
    import multi_ai
except ImportError as e:
    raise ImportError(f"Required module missing: {e}. Check installation.") from e

logger = logging.getLogger("zora.strategy")

# ==============================================================================
# MARKET REGIME DETECTION
# ==============================================================================

def detect_market_regime(df) -> str:
    """
    Classify current market regime into 4 categories:
    - TRENDING_BULLISH: Strong uptrend with ADX > 20, EMA20 > EMA50
    - TRENDING_BEARISH: Strong downtrend with ADX > 20, EMA20 < EMA50
    - RANGING_SIDEWAYS: Choppy/mean-reverting consolidation (ADX < 20)
    - HIGH_VOLATILITY_BREAKOUT: High volatility with undefined direction
    
    This informs AI council on regime-specific strategy bias.
    """
    if len(df) < 50:
        return "INSUFFICIENT_DATA"
    
    try:
        # Calculate technical indicators
        ema_20 = float(indicators.ema(df["close"], 20).iloc[-1])
        ema_50 = float(indicators.ema(df["close"], 50).iloc[-1])
        adx_val = float(indicators.adx(df, 14).iloc[-1])
        atr_val = float(indicators.atr(df, 14).iloc[-1])
        close_price = float(df["close"].iloc[-1])
        
        # Calculate volatility ratio (ATR % of price)
        volatility_ratio = (atr_val / close_price) * 100 if close_price > 0 else 0
        
        # Regime classification logic
        if adx_val < 20:
            # Low directional strength = ranging/choppy
            return "RANGING_SIDEWAYS"
        
        # ADX >= 20 indicates trending
        if volatility_ratio > 3.0:  # Unusually high volatility during trend
            return "HIGH_VOLATILITY_BREAKOUT"
        
        if ema_20 > ema_50:
            return "TRENDING_BULLISH"
        else:
            return "TRENDING_BEARISH"
    
    except (ValueError, IndexError, TypeError) as e:
        logger.error(f"Market regime detection error: {e}")
        return "UNKNOWN"

# ==============================================================================
# INTRA-CANDLE TRIGGER DETECTION
# ==============================================================================

class IntraCandleMonitor:
    """
    Tracks intra-candle price and volume events for immediate trigger evaluation.
    Prevents missing fast-moving opportunities while avoiding false wicks.
    """
    def __init__(self):
        self.last_close_price: float = 0
        self.last_volume_20_avg: float = 0
        self.h24_high: float = 0
        self.h24_low: float = 0
        self.triggered_at: float = 0
        self.last_trigger_time: float = 0
    
    def update_baseline(self, df) -> None:
        """Update 24h levels and volume baseline from OHLCV data."""
        if len(df) >= 96:  # 96 15m candles = 24h
            try:
                h24_data = df.tail(96)
                self.h24_high = float(h24_data["high"].max())
                self.h24_low = float(h24_data["low"].min())
                self.last_volume_20_avg = float(h24_data["volume"].tail(20).mean())
                self.last_close_price = float(df["close"].iloc[-1])
            except (ValueError, KeyError, TypeError) as e:
                logger.debug(f"Baseline update error: {e}")
    
    def check_intra_candle_trigger(
        self,
        current_price: float,
        current_volume: float,
        min_seconds_between_triggers: int = 60
    ) -> bool:
        """
        Check if an abnormal intra-candle event should trigger immediate AI evaluation.
        
        Triggers on:
        - Volume spike > 2.5x 20-period average
        - Price breakout beyond 24h high/low
        
        Cooldown prevents repeated triggers within min_seconds_between_triggers.
        """
        import time
        
        now = time.time()
        
        # Cooldown check
        if now - self.last_trigger_time < min_seconds_between_triggers:
            return False
        
        # Check volume spike (> 2.5x average)
        if self.last_volume_20_avg > 0:
            volume_ratio = current_volume / self.last_volume_20_avg
            if volume_ratio > 2.5:
                logger.warning(
                    f"INTRA-CANDLE TRIGGER: Volume spike {volume_ratio:.2f}x "
                    f"({current_volume:.0f} vs {self.last_volume_20_avg:.0f})"
                )
                self.triggered_at = now
                self.last_trigger_time = now
                return True
        
        # Check 24h breakout (with 0.1% tolerance for noise)
        tolerance = self.last_close_price * 0.001
        
        if current_price > (self.h24_high + tolerance):
            logger.warning(
                f"INTRA-CANDLE TRIGGER: 24h high breakout "
                f"{current_price:.2f} > {self.h24_high:.2f}"
            )
            self.triggered_at = now
            self.last_trigger_time = now
            return True
        
        if current_price < (self.h24_low - tolerance):
            logger.warning(
                f"INTRA-CANDLE TRIGGER: 24h low breakout "
                f"{current_price:.2f} < {self.h24_low:.2f}"
            )
            self.triggered_at = now
            self.last_trigger_time = now
            return True
        
        return False

# Global monitor instance
_intra_candle_monitor = IntraCandleMonitor()

# ==============================================================================
# MARKET DOSSIER PACKAGING
# ==============================================================================

def build_market_dossier(symbol: str, df, is_intra_candle: bool = False) -> str:
    """
    Package comprehensive market context into AI-friendly structured dossier.
    
    Includes:
    - Current price and recent price action
    - Technical indicators (RSI, MACD, ATR, EMA trends)
    - Market regime classification
    - 24h key price levels
    - Smart Money Concepts (liquidity sweeps, FVGs)
    - Market sentiment (news, fear/greed)
    - Intra-candle trigger flag (if applicable)
    
    This dossier replaces rigid indicator rules - AI council makes the decision.
    """
    if len(df) < 30:
        return f"Insufficient data for {symbol} analysis (need 30+ candles)"
    
    try:
        # Extract latest candle data
        last_candle = df.iloc[-1]
        curr_price = float(last_candle["close"])
        curr_open = float(last_candle["open"])
        
        # Calculate percentage move in latest candle
        candle_move_pct = ((curr_price - curr_open) / curr_open * 100) if curr_open > 0 else 0
        
        # Technical indicators
        rsi_val = float(indicators.rsi(df["close"], 14).iloc[-1])
        
        # MACD
        macd_result = indicators.macd(df["close"])
        if macd_result is not None and len(macd_result) >= 3:
            macd_line = float(macd_result[0].iloc[-1])
            macd_signal = float(macd_result[1].iloc[-1])
            macd_histogram = float(macd_result[2].iloc[-1])
            macd_summary = f"MACD={macd_line:.2f}, Signal={macd_signal:.2f}, Hist={macd_histogram:.4f}"
        else:
            macd_summary = "MACD unavailable"
        
        # ATR for volatility assessment
        atr_val = float(indicators.atr(df, 14).iloc[-1])
        atr_pct = (atr_val / curr_price * 100) if curr_price > 0 else 0
        
        # EMA trends for momentum confirmation
        ema_20 = float(indicators.ema(df["close"], 20).iloc[-1])
        ema_50 = float(indicators.ema(df["close"], 50).iloc[-1])
        ema_200 = float(indicators.ema(df["close"], 200).iloc[-1]) if len(df) >= 200 else None
        
        ema_summary = f"EMA20={ema_20:.2f} vs EMA50={ema_50:.2f}"
        if ema_200:
            ema_summary += f" vs EMA200={ema_200:.2f}"
        
        # Market regime
        regime = detect_market_regime(df)
        
        # 24h key levels
        if len(df) >= 96:  # 24h of 15m candles
            h24_data = df.tail(96)
            h24_high = float(h24_data["high"].max())
            h24_low = float(h24_data["low"].min())
            h24_range = h24_high - h24_low
        else:
            h24_high = float(df["high"].max())
            h24_low = float(df["low"].min())
            h24_range = h24_high - h24_low
        
        # Price position within 24h range
        if h24_range > 0:
            price_position = ((curr_price - h24_low) / h24_range) * 100
        else:
            price_position = 50
        
        # Smart Money Concepts
        try:
            sweep = patterns.detect_liquidity_sweep(df)
            sweep_summary = f"{sweep.get('type', 'None').upper()}" if sweep else "None detected"
        except Exception:
            sweep_summary = "N/A"
        
        try:
            fvgs = patterns.detect_fvg(df)
            fvg_summary = f"{len(fvgs)} active FVG zones" if fvgs else "No active FVGs"
        except Exception:
            fvg_summary = "N/A"
        
        # Market sentiment
        try:
            sentiment = news_feed.fetch_market_sentiment()
            sentiment_summary = f"{sentiment.get('sentiment', 'NEUTRAL')} (FGI: {sentiment.get('score', 50)})"
        except Exception:
            sentiment_summary = "N/A"
        
        # Build comprehensive dossier
        dossier = f"""
MARKET ANALYSIS: {symbol} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{"="*70}

PRICE ACTION:
  Current Price: ${curr_price:.4f}
  24h High: ${h24_high:.4f} | 24h Low: ${h24_low:.4f} | Range: ${h24_range:.4f}
  Price Position in 24h Range: {price_position:.1f}%
  Latest Candle: {'+' if candle_move_pct >= 0 else ''}{candle_move_pct:.2f}%

TECHNICAL INDICATORS:
  RSI(14): {rsi_val:.1f}
  {macd_summary}
  ATR(14): {atr_val:.4f} ({atr_pct:.2f}% of price)
  {ema_summary}

MARKET REGIME: {regime}

SMART MONEY STRUCTURE:
  Liquidity Sweep: {sweep_summary}
  Fair Value Gaps: {fvg_summary}

MARKET SENTIMENT: {sentiment_summary}

TRADING CONTEXT:
  - {regime} indicates regime-specific entry bias
  - RSI={'OVERBOUGHT (>70)' if rsi_val > 70 else 'OVERSOLD (<30)' if rsi_val < 30 else 'NEUTRAL (30-70)'}
  - EMA trend {'bullish (20>50)' if ema_20 > ema_50 else 'bearish (20<50)'}
"""
        
        # Add intra-candle context if triggered
        if is_intra_candle:
            dossier += "\nUROENT: Intra-candle volume/price breakout detected - evaluate immediately for fast-track entry"
        
        return dossier.strip()
    
    except Exception as e:
        logger.error(f"Dossier build error: {e}")
        return f"Error building dossier for {symbol}: {str(e)}"

# ==============================================================================
# STRATEGY EVALUATION INTERFACE
# ==============================================================================

def evaluate(
    symbol: str,
    df,
    current_price: Optional[float] = None,
    current_volume: Optional[float] = None,
    is_intra_candle: bool = False
) -> Tuple[str, int, str]:
    """
    Main strategy evaluation function.
    
    Called on two occasions:
    1. Regular candle close (is_intra_candle=False) - once per 15m candle
    2. Intra-candle breakout (is_intra_candle=True) - when volume/price triggers
    
    Process:
    1. Build comprehensive market dossier
    2. Query 5-AI consensus (Groq, OpenRouter, Mistral, HF + Gemini Judge)
    3. Enforce confidence threshold (>=75%)
    4. Return decision to execution layer
    
    Args:
        symbol: Trading pair (e.g., "ETH/USDT")
        df: OHLCV DataFrame with at least 30 candles
        current_price: Latest tick price (for intra-candle monitoring)
        current_volume: Latest tick volume
        is_intra_candle: True if triggered by intra-candle event
    
    Returns:
        (decision: "BUY"|"SELL"|"HOLD", confidence: 0-100, reasoning: str)
    """
    logger.info(f"Evaluating {symbol} | Intra-candle: {is_intra_candle}")
    
    # Validate data availability
    if len(df) < 30:
        logger.warning(f"Insufficient data for {symbol}: {len(df)} candles (need 30+)")
        return "HOLD", 0, f"Insufficient data: only {len(df)} candles available"
    
    # Update intra-candle monitor baseline
    _intra_candle_monitor.update_baseline(df)
    
    # Check for intra-candle trigger if not already triggered
    if not is_intra_candle and current_price and current_volume:
        if _intra_candle_monitor.check_intra_candle_trigger(current_price, current_volume):
            # Recursive call with is_intra_candle=True
            logger.info(f"Intra-candle trigger activated for {symbol} - fast-tracking evaluation")
            return evaluate(symbol, df, current_price, current_volume, is_intra_candle=True)
    
    # Build market dossier
    dossier = build_market_dossier(symbol, df, is_intra_candle=is_intra_candle)
    
    # Query AI consensus
    try:
        decision, confidence, note = multi_ai.get_ai_consensus(symbol, dossier)
    except Exception as e:
        logger.error(f"AI consensus error: {e}")
        return "HOLD", 0, f"AI consensus unavailable: {str(e)}"
    
    # Log decision
    logger.info(
        f"{symbol} decision: {decision} ({confidence}%) | "
        f"Intra: {is_intra_candle} | {note}"
    )
    
    # Enforce confidence threshold
    confidence_threshold = 75
    if confidence < confidence_threshold:
        logger.debug(
            f"Confidence {confidence}% < {confidence_threshold}% threshold - "
            f"defaulting to HOLD"
        )
        return "HOLD", confidence, (
            f"Confidence {confidence}% below {confidence_threshold}% threshold. "
            f"AI note: {note}"
        )
    
    return decision, confidence, note

# ==============================================================================
# END OF strategy.py
# ==============================================================================
