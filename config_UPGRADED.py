"""
config.py — UPGRADED Master Configuration Parser
================================================

Loads and validates all environment variables for ZORA v1.2.1+
Handles defaults, type conversion, validation, and provides
clean configuration interface for all modules.

Termux-compatible: No special dependencies, pure Python.
"""
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("zora.config")

class Config:
    """
    Master configuration class. Loads from environment variables.
    All defaults are conservative (safe) values.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        
        # ==============================================================================
        # EXCHANGE & TRADING
        # ==============================================================================
        
        self.exchange_id = os.getenv("EXCHANGE_ID", "htx").lower()
        valid_exchanges = ["htx", "binance", "bybit", "okx"]
        if self.exchange_id not in valid_exchanges:
            logger.warning(f"Unknown exchange '{self.exchange_id}', defaulting to 'htx'")
            self.exchange_id = "htx"
        
        # Parse trading symbols (comma-separated)
        symbols_str = os.getenv("SYMBOLS", "ETH/USDT")
        self.symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
        if not self.symbols:
            self.symbols = ["ETH/USDT"]
        
        self.trading_mode = os.getenv("TRADING_MODE", "paper").lower()
        if self.trading_mode not in ("paper", "live"):
            logger.warning(f"Unknown trading mode '{self.trading_mode}', defaulting to 'paper'")
            self.trading_mode = "paper"
        
        # Initial capital (USD)
        try:
            self.initial_capital = float(os.getenv("INITIAL_CAPITAL", "1000"))
        except ValueError:
            logger.warning("Invalid INITIAL_CAPITAL, defaulting to 1000")
            self.initial_capital = 1000.0
        
        # ==============================================================================
        # AI PROVIDERS - 5-AI EXPERT COUNCIL
        # ==============================================================================
        
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY", "").strip()
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        
        # Warn if critical provider (Gemini) is missing
        if not self.gemini_api_key:
            logger.warning(
                "Gemini API key not configured! "
                "The AI Judge will be unavailable - consensus will default to HOLD."
            )
        
        # Count available AI providers
        self.ai_providers_available = sum([
            bool(self.groq_api_key),
            bool(self.openrouter_api_key),
            bool(self.mistral_api_key),
            bool(self.huggingface_api_key)
        ])
        
        logger.info(f"AI providers configured: {self.ai_providers_available}/4 council members + Judge")
        
        # AI confidence threshold for trade execution
        try:
            self.ai_min_confidence = int(os.getenv("AI_MIN_CONFIDENCE", "75"))
            self.ai_min_confidence = max(0, min(100, self.ai_min_confidence))
        except ValueError:
            logger.warning("Invalid AI_MIN_CONFIDENCE, defaulting to 75")
            self.ai_min_confidence = 75
        
        # ==============================================================================
        # RISK MANAGEMENT
        # ==============================================================================
        
        # Risk per trade (1-2% recommended)
        try:
            risk_pct = float(os.getenv("MAX_RISK_PER_TRADE_PCT", "0.02"))
            # Clamp between 0.5% and 3% as safety bounds
            self.max_risk_per_trade_pct = max(0.005, min(0.03, risk_pct))
        except ValueError:
            logger.warning("Invalid MAX_RISK_PER_TRADE_PCT, defaulting to 0.02")
            self.max_risk_per_trade_pct = 0.02
        
        # Daily drawdown circuit breaker
        try:
            dd_pct = float(os.getenv("DAILY_DRAWDOWN_LIMIT_PCT", "0.04"))
            self.daily_drawdown_limit_pct = max(0.01, min(0.10, dd_pct))
        except ValueError:
            logger.warning("Invalid DAILY_DRAWDOWN_LIMIT_PCT, defaulting to 0.04")
            self.daily_drawdown_limit_pct = 0.04
        
        # Maximum open positions
        try:
            self.max_open_positions = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
            self.max_open_positions = max(1, min(10, self.max_open_positions))
        except ValueError:
            logger.warning("Invalid MAX_OPEN_POSITIONS, defaulting to 5")
            self.max_open_positions = 5
        
        # Maximum position size
        try:
            pos_pct = float(os.getenv("MAX_POSITION_SIZE_PCT", "0.10"))
            self.max_position_size_pct = max(0.05, min(0.25, pos_pct))
        except ValueError:
            logger.warning("Invalid MAX_POSITION_SIZE_PCT, defaulting to 0.10")
            self.max_position_size_pct = 0.10
        
        # ==============================================================================
        # TAKE-PROFIT SCALING
        # ==============================================================================
        
        try:
            self.tp1_rr = float(os.getenv("TP1_RR", "1.5"))
            self.tp1_rr = max(0.5, min(5.0, self.tp1_rr))
        except ValueError:
            logger.warning("Invalid TP1_RR, defaulting to 1.5")
            self.tp1_rr = 1.5
        
        try:
            self.tp2_rr = float(os.getenv("TP2_RR", "3.0"))
            self.tp2_rr = max(1.0, min(10.0, self.tp2_rr))
        except ValueError:
            logger.warning("Invalid TP2_RR, defaulting to 3.0")
            self.tp2_rr = 3.0
        
        try:
            self.runner_trail_atr_mult = float(os.getenv("RUNNER_TRAIL_ATR_MULT", "2.0"))
            self.runner_trail_atr_mult = max(1.0, min(5.0, self.runner_trail_atr_mult))
        except ValueError:
            logger.warning("Invalid RUNNER_TRAIL_ATR_MULT, defaulting to 2.0")
            self.runner_trail_atr_mult = 2.0
        
        # ==============================================================================
        # INTRA-CANDLE TRIGGERING
        # ==============================================================================
        
        try:
            self.intra_candle_cooldown_sec = int(os.getenv("INTRA_CANDLE_COOLDOWN_SEC", "60"))
            self.intra_candle_cooldown_sec = max(30, min(300, self.intra_candle_cooldown_sec))
        except ValueError:
            logger.warning("Invalid INTRA_CANDLE_COOLDOWN_SEC, defaulting to 60")
            self.intra_candle_cooldown_sec = 60
        
        try:
            self.volume_spike_threshold = float(os.getenv("VOLUME_SPIKE_THRESHOLD", "2.5"))
            self.volume_spike_threshold = max(1.5, min(5.0, self.volume_spike_threshold))
        except ValueError:
            logger.warning("Invalid VOLUME_SPIKE_THRESHOLD, defaulting to 2.5")
            self.volume_spike_threshold = 2.5
        
        intra_enabled_str = os.getenv("INTRA_CANDLE_DETECTION_ENABLED", "true").lower()
        self.intra_candle_detection_enabled = intra_enabled_str in ("true", "1", "yes", "on")
        
        # ==============================================================================
        # MONITORING & DASHBOARD
        # ==============================================================================
        
        try:
            self.dashboard_port = int(os.getenv("DASHBOARD_PORT", "5000"))
            # Ensure port is in valid range
            self.dashboard_port = max(1024, min(65535, self.dashboard_port))
        except ValueError:
            logger.warning("Invalid DASHBOARD_PORT, defaulting to 5000")
            self.dashboard_port = 5000
        
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            logger.warning(f"Invalid LOG_LEVEL '{self.log_level}', defaulting to 'INFO'")
            self.log_level = "INFO"
        
        # Optional Telegram notifications
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        self.telegram_enabled = bool(self.telegram_bot_token and self.telegram_chat_id)
        
        # ==============================================================================
        # DATABASE
        # ==============================================================================
        
        self.db_path = os.getenv("DB_PATH", "./zora.db")
        
        # ==============================================================================
        # ADVANCED SETTINGS
        # ==============================================================================
        
        try:
            self.ai_provider_timeout_sec = int(os.getenv("AI_PROVIDER_TIMEOUT_SEC", "12"))
            self.ai_provider_timeout_sec = max(5, min(30, self.ai_provider_timeout_sec))
        except ValueError:
            logger.warning("Invalid AI_PROVIDER_TIMEOUT_SEC, defaulting to 12")
            self.ai_provider_timeout_sec = 12
        
        try:
            self.ai_response_cache_ttl_sec = int(os.getenv("AI_RESPONSE_CACHE_TTL_SEC", "300"))
            self.ai_response_cache_ttl_sec = max(0, min(3600, self.ai_response_cache_ttl_sec))
        except ValueError:
            logger.warning("Invalid AI_RESPONSE_CACHE_TTL_SEC, defaulting to 300")
            self.ai_response_cache_ttl_sec = 300
        
        try:
            self.ai_provider_max_retries = int(os.getenv("AI_PROVIDER_MAX_RETRIES", "2"))
            self.ai_provider_max_retries = max(0, min(5, self.ai_provider_max_retries))
        except ValueError:
            logger.warning("Invalid AI_PROVIDER_MAX_RETRIES, defaulting to 2")
            self.ai_provider_max_retries = 2
        
        try:
            self.rate_limit_cooldown_sec = int(os.getenv("RATE_LIMIT_COOLDOWN_SEC", "90"))
            self.rate_limit_cooldown_sec = max(30, min(600, self.rate_limit_cooldown_sec))
        except ValueError:
            logger.warning("Invalid RATE_LIMIT_COOLDOWN_SEC, defaulting to 90")
            self.rate_limit_cooldown_sec = 90
        
        # ==============================================================================
        # MARKET DATA
        # ==============================================================================
        
        self.candle_timeframe = os.getenv("CANDLE_TIMEFRAME", "15m")
        valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        if self.candle_timeframe not in valid_timeframes:
            logger.warning(f"Unknown timeframe '{self.candle_timeframe}', defaulting to '15m'")
            self.candle_timeframe = "15m"
        
        try:
            self.history_lookback = int(os.getenv("HISTORY_LOOKBACK", "96"))
            self.history_lookback = max(30, min(500, self.history_lookback))
        except ValueError:
            logger.warning("Invalid HISTORY_LOOKBACK, defaulting to 96")
            self.history_lookback = 96
        
        # ==============================================================================
        # TECHNICAL INDICATORS
        # ==============================================================================
        
        try:
            self.atr_period = int(os.getenv("ATR_PERIOD", "14"))
            self.atr_period = max(5, min(50, self.atr_period))
        except ValueError:
            logger.warning("Invalid ATR_PERIOD, defaulting to 14")
            self.atr_period = 14
        
        try:
            self.ema_fast = int(os.getenv("EMA_FAST", "20"))
            self.ema_mid = int(os.getenv("EMA_MID", "50"))
            self.ema_slow = int(os.getenv("EMA_SLOW", "200"))
        except ValueError:
            logger.warning("Invalid EMA periods, using defaults")
            self.ema_fast = 20
            self.ema_mid = 50
            self.ema_slow = 200
        
        # ==============================================================================
        # PAPER TRADING
        # ==============================================================================
        
        try:
            self.paper_initial_balance = float(os.getenv("PAPER_TRADING_INITIAL_BALANCE", "10000"))
        except ValueError:
            logger.warning("Invalid PAPER_TRADING_INITIAL_BALANCE, defaulting to 10000")
            self.paper_initial_balance = 10000.0
        
        try:
            self.slippage_pct = float(os.getenv("SLIPPAGE_PCT", "0.001"))
            self.slippage_pct = max(0, min(1.0, self.slippage_pct))
        except ValueError:
            logger.warning("Invalid SLIPPAGE_PCT, defaulting to 0.001")
            self.slippage_pct = 0.001
        
        try:
            self.commission_pct = float(os.getenv("COMMISSION_PCT", "0.001"))
            self.commission_pct = max(0, min(1.0, self.commission_pct))
        except ValueError:
            logger.warning("Invalid COMMISSION_PCT, defaulting to 0.001")
            self.commission_pct = 0.001
        
        # ==============================================================================
        # PERSISTENCE
        # ==============================================================================
        
        try:
            self.state_save_interval_sec = int(os.getenv("STATE_SAVE_INTERVAL_SEC", "300"))
            self.state_save_interval_sec = max(60, min(3600, self.state_save_interval_sec))
        except ValueError:
            logger.warning("Invalid STATE_SAVE_INTERVAL_SEC, defaulting to 300")
            self.state_save_interval_sec = 300
        
        auto_recover_str = os.getenv("AUTO_RECOVER_ON_STARTUP", "true").lower()
        self.auto_recover_on_startup = auto_recover_str in ("true", "1", "yes", "on")
        
        # ==============================================================================
        # LOG CONFIGURATION SUMMARY
        # ==============================================================================
        
        logger.info(
            f"Configuration loaded successfully:\n"
            f"  Exchange: {self.exchange_id}\n"
            f"  Symbols: {', '.join(self.symbols)}\n"
            f"  Mode: {self.trading_mode}\n"
            f"  Risk per trade: {self.max_risk_per_trade_pct*100:.1f}%\n"
            f"  Daily DD limit: {self.daily_drawdown_limit_pct*100:.1f}%\n"
            f"  Max open positions: {self.max_open_positions}\n"
            f"  AI providers: {self.ai_providers_available}/4 council + Judge\n"
            f"  Min confidence: {self.ai_min_confidence}%\n"
            f"  Dashboard: http://127.0.0.1:{self.dashboard_port}\n"
            f"  Intra-candle: {'ENABLED' if self.intra_candle_detection_enabled else 'DISABLED'}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "exchange": self.exchange_id,
            "symbols": self.symbols,
            "mode": self.trading_mode,
            "initial_capital": self.initial_capital,
            "risk_per_trade_pct": self.max_risk_per_trade_pct,
            "daily_dd_limit": self.daily_drawdown_limit_pct,
            "max_open_positions": self.max_open_positions,
            "tp1_rr": self.tp1_rr,
            "tp2_rr": self.tp2_rr,
            "ai_providers": self.ai_providers_available,
            "ai_min_confidence": self.ai_min_confidence,
            "intra_candle_enabled": self.intra_candle_detection_enabled
        }

# ==============================================================================
# GLOBAL CONFIG INSTANCE - USE THIS IN OTHER MODULES
# ==============================================================================

CFG = Config()

# ==============================================================================
# END OF config.py
# ==============================================================================
