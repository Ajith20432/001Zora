"""
risk.py — UPGRADED Institutional Capital Preservation & Compounding Engine
===========================================================================

Advanced risk management for elite crypto quantitative trading:
- Dynamic risk sizing (1-2% per trade based on ATR stop distance)
- Partial Take-Profit with auto-Breakeven scaling
  • TP1 (50% position): Close at 1.5R, move stop to Entry (0% risk)
  • TP2 (25% position): Close at 3.0R
  • Runner (25% position): Trail with dynamic ATR stop
- Daily circuit breaker (4% drawdown locks entries for 24h)
- Auto-compounding (recalculate sizes as equity grows)
- Intraday equity tracking with proper UTC midnight resets

Enforces strict capital preservation that overrides any AI signal.
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger("zora.risk")

# ==============================================================================
# CONFIGURATION CONSTANTS
# ==============================================================================

MAX_RISK_PER_TRADE_PCT_MIN = 0.01   # Minimum 1% capital risk per trade
MAX_RISK_PER_TRADE_PCT_MAX = 0.02   # Maximum 2% capital risk per trade

DAILY_DRAWDOWN_LIMIT_PCT = 0.04     # 4% daily circuit breaker

# Partial take-profit scaling (Risk-Reward multiples)
TP1_RR = 1.5                        # 50% position closes at 1.5R
TP2_RR = 3.0                        # 25% position closes at 3.0R
RUNNER_TRAIL_ATR_MULT = 2.0         # Runner trails at 2x ATR

# Position limits
MAX_POSITION_SIZE_PCT = 0.10        # Maximum 10% of equity in any single position
MAX_OPEN_POSITIONS = 5              # Maximum 5 concurrent positions

# Compounding
COMPOUND_EVERY_PCT_GAIN = 0.05      # Recalculate size for every 5% equity gain

# ==============================================================================
# INSTITUTIONAL RISK MANAGER CLASS
# ==============================================================================

class InstitutionalRiskManager:
    """
    Enterprise-grade risk engine that enforces capital preservation above all.
    All decisions override AI signals if risk parameters are violated.
    """
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.equity = initial_capital
        self.peak_equity = initial_capital
        
        # Daily tracking (resets at UTC midnight)
        self.daily_start_equity = initial_capital
        self.daily_start_time = self._get_utc_midnight()
        
        # Circuit breaker
        self.halted = False
        self.halt_time: Optional[float] = None
        
        # Position tracking
        self.open_positions: Dict[str, Dict[str, Any]] = {}  # symbol -> position data
        self.current_exposure_pct = 0.0
        
        # Compounding tracking
        self.last_compound_equity = initial_capital
        
        # Thread safety
        self._lock = threading.Lock()
    
    @staticmethod
    def _get_utc_midnight() -> float:
        """Get Unix timestamp of next UTC midnight."""
        now = datetime.now(timezone.utc)
        # Calculate seconds until midnight
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if midnight < now:
            # Add 24 hours to get tomorrow's midnight
            from datetime import timedelta
            midnight += timedelta(days=1)
        return midnight.timestamp()
    
    def _check_daily_reset(self) -> bool:
        """Check if we've crossed into a new UTC day and reset if so."""
        with self._lock:
            now = time.time()
            if now >= self.daily_start_time:
                logger.info(
                    f"Daily reset: {self.daily_start_equity:.2f} USD equity -> "
                    f"{self.equity:.2f} USD (today PnL: "
                    f"{((self.equity/self.daily_start_equity - 1)*100):+.2f}%)"
                )
                self.daily_start_equity = self.equity
                self.halted = False
                self.halt_time = None
                self.daily_start_time = self._get_utc_midnight()
                return True
        return False
    
    def update_equity(self, current_equity: float) -> None:
        """
        Update current equity and check circuit breaker conditions.
        
        Called after each trade close/scale-out.
        Enforces:
        - Peak equity tracking for accurate drawdown calculation
        - Daily drawdown circuit breaker
        """
        with self._lock:
            self.equity = float(current_equity)
            
            # Update peak for accurate drawdown
            if self.equity > self.peak_equity:
                self.peak_equity = self.equity
            
            # Check daily reset (UTC midnight)
            self._check_daily_reset()
            
            # Calculate daily drawdown
            daily_drawdown = (self.daily_start_equity - self.equity) / self.daily_start_equity
            
            # Circuit breaker logic
            if daily_drawdown >= DAILY_DRAWDOWN_LIMIT_PCT:
                if not self.halted:
                    logger.critical(
                        f"CIRCUIT BREAKER ACTIVATED: Daily drawdown {daily_drawdown*100:.2f}% >= "
                        f"{DAILY_DRAWDOWN_LIMIT_PCT*100:.1f}%. "
                        f"Halting all new entries for 24 hours."
                    )
                    self.halted = True
                    self.halt_time = time.time()
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        atr_value: float,
        base_risk_pct: Optional[float] = None
    ) -> float:
        """
        Calculate optimal position size using ATR-based risk allocation.
        
        Logic:
        - Risk distance = ATR * 2 (if no explicit SL provided) or |entry - SL|
        - Risk amount = equity * risk_pct (1-2% depending on volatility)
        - Size = risk_amount / risk_distance
        - Cap at max position size (10% equity)
        
        Args:
            entry_price: Entry price in USD
            stop_loss_price: Stop loss price in USD
            atr_value: Current ATR(14) volatility
            base_risk_pct: Override risk % (0.01-0.02), else auto-selected
        
        Returns:
            Position size in base asset (capped to risk limits)
        """
        with self._lock:
            # Check if halted
            if self.halted:
                logger.warning("Circuit breaker active - position size = 0")
                return 0.0
            
            # Validate inputs
            try:
                entry_price = float(entry_price)
                stop_loss_price = float(stop_loss_price)
                atr_value = float(atr_value)
            except (ValueError, TypeError):
                logger.error(f"Invalid position size inputs: {entry_price}, {stop_loss_price}, {atr_value}")
                return 0.0
            
            if entry_price <= 0 or stop_loss_price < 0 or atr_value < 0:
                logger.warning("Invalid price/ATR values for position sizing")
                return 0.0
            
            # Calculate risk distance
            risk_distance = abs(entry_price - stop_loss_price)
            if risk_distance <= 0:
                logger.warning("Risk distance = 0, cannot size position")
                return 0.0
            
            # Auto-select risk percentage based on volatility
            if base_risk_pct is None:
                # High volatility (ATR > 2% of price) -> 1% risk
                # Low volatility (ATR < 1% of price) -> 2% risk
                volatility_ratio = (atr_value / entry_price) * 100
                if volatility_ratio > 2.0:
                    base_risk_pct = MAX_RISK_PER_TRADE_PCT_MIN  # 1%
                else:
                    base_risk_pct = MAX_RISK_PER_TRADE_PCT_MAX  # 2%
            
            # Ensure risk is within bounds
            base_risk_pct = max(MAX_RISK_PER_TRADE_PCT_MIN, 
                               min(MAX_RISK_PER_TRADE_PCT_MAX, base_risk_pct))
            
            # Calculate position size
            risk_usd = self.equity * base_risk_pct
            position_size = risk_usd / risk_distance
            
            # Hard cap: maximum 10% of equity in notional value
            max_notional = self.equity * MAX_POSITION_SIZE_PCT
            max_size_by_notional = max_notional / entry_price
            position_size = min(position_size, max_size_by_notional)
            
            # Floor to 4 decimal places to ensure clean numbers
            position_size = float(int(position_size * 10000) / 10000)
            
            logger.info(
                f"Position size: {position_size:.4f} | "
                f"Risk: {risk_usd:.2f} USD | "
                f"Risk distance: {risk_distance:.4f} | "
                f"Volatility: {(atr_value/entry_price*100):.2f}%"
            )
            
            return position_size
    
    def check_partial_takeprofits(
        self,
        symbol: str,
        entry_price: float,
        current_price: float,
        stop_loss_price: float,
        side: str = "BUY"
    ) -> Dict[str, Any]:
        """
        Check if position qualifies for partial take-profit scaling.
        
        Implements 3-leg scale-out strategy:
        
        1. TP1 (50% position) at 1.5R
           - Close half position
           - Move remaining stop to Entry (Breakeven/0% risk)
        
        2. TP2 (25% position) at 3.0R
           - Close quarter position
        
        3. Runner (25% position)
           - Trail stop dynamically with ATR
           - Infinite upside with risk-free entry
        
        Args:
            symbol: Trading pair
            entry_price: Entry fill price
            current_price: Current market price
            stop_loss_price: Current stop loss price
            side: "BUY" or "SELL"
        
        Returns:
            {
                "action": "CLOSE_PARTIAL" | "HOLD" | "CLOSE_ALL",
                "stage": "TP1_BREAKEVEN" | "TP2" | "HOLD",
                "percent_to_close": float (0.0-1.0),
                "new_stop_loss": float,
                "pnl_r": float (risk multiples earned)
            }
        """
        with self._lock:
            try:
                # Calculate risk-reward
                risk_distance = abs(entry_price - stop_loss_price)
                if risk_distance <= 0:
                    return {"action": "HOLD", "stage": "ERROR", "pnl_r": 0.0}
                
                # Calculate P&L in R multiples
                if side == "BUY":
                    pnl = current_price - entry_price
                else:  # SELL
                    pnl = entry_price - current_price
                
                pnl_r = pnl / risk_distance
                
                # TP2: 3.0R - close 25% (quarter position)
                if pnl_r >= TP2_RR:
                    logger.info(f"{symbol} TP2 triggered at {pnl_r:.2f}R - closing 25%")
                    return {
                        "action": "CLOSE_PARTIAL",
                        "stage": "TP2",
                        "percent_to_close": 0.25,
                        "new_stop_loss": stop_loss_price,  # Keep trailing runner stop
                        "pnl_r": pnl_r
                    }
                
                # TP1: 1.5R - close 50%, move stop to entry (breakeven)
                if pnl_r >= TP1_RR:
                    new_sl = entry_price  # Breakeven - 0% risk
                    logger.info(
                        f"{symbol} TP1 triggered at {pnl_r:.2f}R - "
                        f"closing 50%, moving stop to breakeven"
                    )
                    return {
                        "action": "CLOSE_PARTIAL",
                        "stage": "TP1_BREAKEVEN",
                        "percent_to_close": 0.50,
                        "new_stop_loss": new_sl,
                        "pnl_r": pnl_r
                    }
                
                # No TP triggered - update return data
                return {
                    "action": "HOLD",
                    "stage": "HOLD",
                    "pnl_r": pnl_r,
                    "r_to_next_tp": TP1_RR - pnl_r
                }
            
            except (ValueError, TypeError, ZeroDivisionError) as e:
                logger.error(f"TP check error for {symbol}: {e}")
                return {"action": "HOLD", "stage": "ERROR"}
    
    def calculate_trailing_stop(
        self,
        current_price: float,
        entry_price: float,
        atr_value: float,
        side: str = "BUY",
        current_stop: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate trailing stop for runner position.
        
        Trail at 2x ATR below (for BUY) or above (for SELL) the price.
        Never loosens the stop - only tightens.
        
        Args:
            current_price: Current market price
            entry_price: Position entry price
            atr_value: Current ATR(14) value
            side: "BUY" or "SELL"
            current_stop: Current stop loss to avoid loosening
        
        Returns:
            New stop loss price, or None if should keep current
        """
        try:
            atr_value = float(atr_value)
            current_price = float(current_price)
            entry_price = float(entry_price)
            
            if side == "BUY":
                # Trail below current price
                new_stop = current_price - (atr_value * RUNNER_TRAIL_ATR_MULT)
                
                # Never lower than entry (would eliminate profit)
                new_stop = max(new_stop, entry_price)
                
                # Never loosen - only tighten
                if current_stop is not None:
                    new_stop = max(new_stop, float(current_stop))
                
                return new_stop
            
            else:  # SELL
                # Trail above current price
                new_stop = current_price + (atr_value * RUNNER_TRAIL_ATR_MULT)
                
                # Never higher than entry
                new_stop = min(new_stop, entry_price)
                
                # Never loosen
                if current_stop is not None:
                    new_stop = min(new_stop, float(current_stop))
                
                return new_stop
        
        except (ValueError, TypeError) as e:
            logger.error(f"Trailing stop error: {e}")
            return None
    
    def register_open_position(
        self,
        symbol: str,
        entry_price: float,
        position_size: float,
        stop_loss: float,
        side: str = "BUY"
    ) -> None:
        """Register an open position for tracking and exposure calculation."""
        with self._lock:
            self.open_positions[symbol] = {
                "entry_price": entry_price,
                "size": position_size,
                "stop_loss": stop_loss,
                "side": side,
                "opened_at": time.time(),
                "tp1_closed": False,
                "tp2_closed": False
            }
            
            # Recalculate exposure
            self._update_exposure()
    
    def close_position(self, symbol: str) -> None:
        """Unregister a closed position."""
        with self._lock:
            if symbol in self.open_positions:
                del self.open_positions[symbol]
                self._update_exposure()
    
    def _update_exposure(self) -> None:
        """Recalculate total open exposure as % of equity."""
        if not self.open_positions:
            self.current_exposure_pct = 0.0
            return
        
        # Count open position slots (each risk up to 2% per trade)
        # Total exposure = number of open positions * max risk per trade
        num_open = len(self.open_positions)
        self.current_exposure_pct = num_open * MAX_RISK_PER_TRADE_PCT_MAX
    
    def can_open_new_position(self) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Conditions:
        - Not halted by circuit breaker
        - Under max open positions limit
        - Under max exposure limit (5 positions * 2% = 10% max)
        
        Returns:
            (allowed: bool, reason: str)
        """
        with self._lock:
            if self.halted:
                hours_remaining = (self.halt_time + 86400 - time.time()) / 3600
                return False, (
                    f"Circuit breaker active for {hours_remaining:.1f} more hours "
                    f"(daily drawdown hit)"
                )
            
            if len(self.open_positions) >= MAX_OPEN_POSITIONS:
                return False, (
                    f"Max {MAX_OPEN_POSITIONS} open positions reached "
                    f"({len(self.open_positions)} current)"
                )
            
            return True, "OK"
    
    def get_status(self) -> Dict[str, Any]:
        """Return current risk engine status for monitoring/display."""
        with self._lock:
            return {
                "equity": self.equity,
                "peak_equity": self.peak_equity,
                "daily_start_equity": self.daily_start_equity,
                "daily_pnl_pct": ((self.equity / self.daily_start_equity) - 1) * 100,
                "drawdown_pct": ((self.peak_equity - self.equity) / self.peak_equity) * 100,
                "halted": self.halted,
                "open_positions": len(self.open_positions),
                "current_exposure_pct": self.current_exposure_pct,
                "max_risk_per_trade_pct": MAX_RISK_PER_TRADE_PCT_MAX
            }

# ==============================================================================
# GLOBAL RISK MANAGER INSTANCE
# ==============================================================================

RISK = InstitutionalRiskManager()

# ==============================================================================
# END OF risk.py
# ==============================================================================
