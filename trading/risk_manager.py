# =============================================================================
# FILE 3: trading/risk_manager.py
# =============================================================================

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedRiskManager:
    """
    Comprehensive risk management system:
    - Position-level risk
    - Portfolio-level risk
    - Drawdown protection
    - Dynamic position sizing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.max_risk_per_trade = config.get('max_risk_per_trade', 2.0) / 100
        self.max_daily_loss = config.get('max_daily_loss', 5.0) / 100
        self.max_drawdown = config.get('max_drawdown_limit', 10.0) / 100
        self.max_position_value = config.get('max_position_value', 20.0) / 100
        
        # Risk tracking
        self.daily_pnl = 0
        self.max_portfolio_value = config.get('account_balance', 10000)
        self.current_drawdown = 0
        self.risk_events = []
        self.trade_count_today = 0
        self.max_trades_per_day = config.get('max_trades_per_day', 5)
        
        logger.info("✅ Enhanced risk manager initialized")
        logger.info(f"   Max risk per trade: {self.max_risk_per_trade:.1%}")
        logger.info(f"   Max daily loss: {self.max_daily_loss:.1%}")
        logger.info(f"   Max drawdown: {self.max_drawdown:.1%}")
        
    def assess_trade_risk(self, 
                         entry_price: float,
                         quantity: int,
                         stop_loss: float,
                         account_balance: float,
                         current_positions: int = 0) -> Dict[str, Any]:
        """Assess risk for a proposed trade"""
        
        # Calculate trade risk
        risk_per_share = abs(entry_price - stop_loss)
        total_risk = risk_per_share * quantity
        risk_percentage = total_risk / account_balance if account_balance > 0 else 0
        
        # Position size validation
        max_position_size = account_balance * self.max_position_value
        position_value = entry_price * quantity
        
        # Risk assessment
        risk_score = 0
        warnings = []
        
        # Check risk percentage
        if risk_percentage > self.max_risk_per_trade:
            risk_score += 3
            warnings.append(f"Risk {risk_percentage:.1%} exceeds limit {self.max_risk_per_trade:.1%}")
        
        # Check position size
        if position_value > max_position_size:
            risk_score += 2
            warnings.append(f"Position size too large: {position_value/account_balance:.1%}")
        
        # Check daily loss limit
        potential_daily_loss = abs(self.daily_pnl - total_risk) / account_balance if account_balance > 0 else 0
        if potential_daily_loss > self.max_daily_loss:
            risk_score += 3
            warnings.append(f"Would exceed daily loss limit")
        
        # Check drawdown
        if self.current_drawdown > self.max_drawdown * 0.8:  # 80% of max
            risk_score += 2
            warnings.append(f"Approaching max drawdown limit")
        
        # Check trade frequency
        if self.trade_count_today >= self.max_trades_per_day:
            risk_score += 2
            warnings.append(f"Max trades per day reached: {self.trade_count_today}")
        
        # Risk level determination
        if risk_score >= 5:
            risk_level = "HIGH"
            recommendation = "REJECT"
        elif risk_score >= 3:
            risk_level = "MEDIUM" 
            recommendation = "REDUCE_SIZE"
        elif risk_score >= 1:
            risk_level = "LOW"
            recommendation = "PROCEED_CAUTION"
        else:
            risk_level = "MINIMAL"
            recommendation = "PROCEED"
        
        # Calculate suggested safe quantity
        safe_quantity = quantity
        if recommendation == "REDUCE_SIZE":
            # Reduce to meet risk limits
            max_safe_risk = account_balance * self.max_risk_per_trade
            safe_quantity = int(max_safe_risk / risk_per_share) if risk_per_share > 0 else 1
            safe_quantity = max(1, min(safe_quantity, int(quantity * 0.5)))
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_percentage': risk_percentage,
            'warnings': warnings,
            'recommendation': recommendation,
            'suggested_quantity': safe_quantity,
            'max_safe_quantity': int(account_balance * self.max_risk_per_trade / risk_per_share) if risk_per_share > 0 else quantity,
            'position_value_pct': position_value / account_balance if account_balance > 0 else 0
        }
    
    def update_daily_pnl(self, pnl_change: float):
        """Update daily P&L tracking"""
        self.daily_pnl += pnl_change
        logger.info(f"📊 Daily P&L updated: ₹{self.daily_pnl:.2f}")
        
    def update_drawdown(self, current_portfolio_value: float):
        """Update drawdown tracking"""
        if current_portfolio_value > self.max_portfolio_value:
            self.max_portfolio_value = current_portfolio_value
            self.current_drawdown = 0
        else:
            self.current_drawdown = (self.max_portfolio_value - current_portfolio_value) / self.max_portfolio_value
        
        if self.current_drawdown > 0.05:  # Log significant drawdowns
            logger.warning(f"📉 Current drawdown: {self.current_drawdown:.1%}")
    
    def increment_trade_count(self):
        """Increment daily trade count"""
        self.trade_count_today += 1
        logger.info(f"📈 Trade count today: {self.trade_count_today}/{self.max_trades_per_day}")
    
    def reset_daily_counters(self):
        """Reset daily counters (call at start of each trading day)"""
        self.daily_pnl = 0
        self.trade_count_today = 0
        logger.info("🔄 Daily risk counters reset")
    
    def should_stop_trading(self) -> Tuple[bool, str]:
        """Check if trading should be stopped due to risk limits"""
        
        # Daily loss limit check
        if abs(self.daily_pnl) > self.max_daily_loss * self.max_portfolio_value:
            return True, f"Daily loss limit exceeded: ₹{abs(self.daily_pnl):.2f}"
        
        # Max drawdown check
        if self.current_drawdown > self.max_drawdown:
            return True, f"Maximum drawdown exceeded: {self.current_drawdown:.1%}"
        
        # Max trades per day check
        if self.trade_count_today >= self.max_trades_per_day:
            return True, f"Maximum trades per day reached: {self.trade_count_today}"
        
        return False, ""
    
    def log_risk_event(self, event_type: str, details: str):
        """Log significant risk events"""
        risk_event = {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'details': details,
            'daily_pnl': self.daily_pnl,
            'drawdown': self.current_drawdown
        }
        self.risk_events.append(risk_event)
        logger.warning(f"🚨 Risk Event: {event_type} - {details}")