# =============================================================================
# FILE 2: trading/position_sizer.py
# =============================================================================

import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedPositionSizer:
    """
    Advanced position sizing based on:
    - Signal confidence
    - Market volatility (ATR)
    - Risk management rules
    - Account balance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_risk = config.get('max_risk_per_trade', 2.0) / 100
        self.base_size = config.get('base_position_size', 0.8)
        self.confidence_mult = config.get('confidence_multiplier', True)
        self.volatility_adj = config.get('volatility_adjustment', True)
        
        logger.info("✅ Enhanced position sizer initialized")
        logger.info(f"   Max risk per trade: {self.max_risk:.1%}")
        logger.info(f"   Base position size: {self.base_size:.1%}")
    
    def calculate_position_size(self, 
                              account_balance: float,
                              current_price: float, 
                              atr_value: float,
                              signal_confidence: float,
                              symbol: str = "NIFTYBEES") -> Dict[str, Any]:
        """
        Calculate optimal position size based on multiple factors
        """
        
        # Base capital allocation
        base_capital = account_balance * self.base_size
        
        # Apply confidence multiplier
        if self.confidence_mult:
            confidence_factor = 0.5 + (signal_confidence * 0.5)  # 50% to 100%
            adjusted_capital = base_capital * confidence_factor
        else:
            adjusted_capital = base_capital
        
        # Apply volatility adjustment
        if self.volatility_adj and atr_value > 0:
            # Higher volatility = smaller position
            normal_atr = current_price * 0.02  # 2% as normal volatility
            volatility_factor = min(1.0, normal_atr / atr_value)
            adjusted_capital = adjusted_capital * volatility_factor
        else:
            volatility_factor = 1.0
        
        # Get MIS leverage for the symbol
        mis_leverage = self.get_mis_leverage(symbol)
        effective_capital = adjusted_capital * mis_leverage
        
        # Base quantity calculation
        base_quantity = int(effective_capital / current_price)
        
        # Risk-based position sizing using ATR
        if atr_value > 0:
            # Calculate stop loss distance (2x ATR)
            stop_distance = atr_value * self.config.get('stop_loss_atr_multiple', 2.0)
            
            # Risk per share
            risk_per_share = stop_distance
            
            # Maximum shares based on risk limit
            max_risk_amount = account_balance * self.max_risk
            max_shares_by_risk = int(max_risk_amount / risk_per_share)
            
            # Take minimum of capital-based and risk-based sizing
            final_quantity = min(base_quantity, max_shares_by_risk)
        else:
            final_quantity = base_quantity
        
        # Ensure minimum viable quantity
        final_quantity = max(1, final_quantity)
        
        # Calculate actual margin required
        margin_required = final_quantity * (current_price / mis_leverage)
        
        # Ensure we don't exceed available capital
        if margin_required > account_balance:
            final_quantity = int(account_balance / (current_price / mis_leverage))
            margin_required = final_quantity * (current_price / mis_leverage)
        
        # Position sizing details
        sizing_details = {
            'quantity': final_quantity,
            'margin_required': margin_required,
            'trade_value': final_quantity * current_price,
            'capital_utilization': margin_required / account_balance,
            'confidence_factor': signal_confidence,
            'volatility_factor': volatility_factor,
            'risk_per_trade': final_quantity * (atr_value * 2) if atr_value > 0 else 0,
            'risk_percentage': (final_quantity * atr_value * 2) / account_balance * 100 if atr_value > 0 else 0,
            'leverage_used': mis_leverage,
            'stop_loss_distance': atr_value * 2 if atr_value > 0 else current_price * 0.02
        }
        
        return sizing_details
    
    def get_mis_leverage(self, symbol: str) -> float:
        """Get MIS leverage for different instruments"""
        leverage_map = {
            'NIFTYBEES': 5.0,
            'JUNIORBEES': 5.0,
            'BANKBEES': 4.0,
            'LIQUIDBEES': 3.0,
            'RELIANCE': 4.0,
            'TCS': 4.0,
            'HDFCBANK': 4.0,
            'ICICIBANK': 4.0,
            'INFY': 4.0,
            'HINDUNILVR': 4.0,
            'ITC': 4.0,
            'KOTAKBANK': 4.0,
            'LT': 4.0,
            'SBIN': 4.0,
            'BAJFINANCE': 3.5
        }
        return leverage_map.get(symbol.upper(), 3.0)  # Default 3x leverage