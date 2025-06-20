# trading/position_sizer.py - FIXED VERSION

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
        Calculate optimal position size - FIXED to prevent zero quantities
        """
        
        # Ensure minimum values
        account_balance = max(account_balance, 1000)  # Minimum ₹1000
        current_price = max(current_price, 1)  # Minimum ₹1
        atr_value = max(atr_value, current_price * 0.01)  # Minimum 1% of price
        signal_confidence = max(signal_confidence, 0.3)  # Minimum 30% confidence
        
        logger.info(f"💰 Position Sizing for {symbol}:")
        logger.info(f"   Account: ₹{account_balance:,.2f}")
        logger.info(f"   Price: ₹{current_price:.2f}")
        logger.info(f"   ATR: ₹{atr_value:.2f}")
        logger.info(f"   Confidence: {signal_confidence:.1%}")
        
        # Base capital allocation
        base_capital = account_balance * self.base_size
        
        # Apply confidence multiplier
        if self.confidence_mult:
            confidence_factor = 0.6 + (signal_confidence * 0.4)  # 60% to 100%
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
            max_shares_by_risk = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else base_quantity
            
            # Take minimum of capital-based and risk-based sizing
            final_quantity = min(base_quantity, max_shares_by_risk)
        else:
            final_quantity = base_quantity
        
        # CRITICAL: Ensure minimum viable quantity
        min_quantity = self.calculate_minimum_quantity(account_balance, current_price, mis_leverage)
        final_quantity = max(min_quantity, final_quantity)
        
        # Calculate actual margin required
        margin_required = final_quantity * (current_price / mis_leverage)
        
        # Final safety check: Ensure we don't exceed available capital
        max_affordable_quantity = int(account_balance / (current_price / mis_leverage))
        if final_quantity > max_affordable_quantity:
            final_quantity = max_affordable_quantity
            margin_required = final_quantity * (current_price / mis_leverage)
        
        # Ensure we still have at least 1 share
        if final_quantity < 1:
            final_quantity = 1
            margin_required = current_price / mis_leverage
        
        # Position sizing details
        sizing_details = {
            'quantity': final_quantity,
            'margin_required': margin_required,
            'trade_value': final_quantity * current_price,
            'capital_utilization': margin_required / account_balance if account_balance > 0 else 0,
            'confidence_factor': signal_confidence,
            'volatility_factor': volatility_factor,
            'risk_per_trade': final_quantity * (atr_value * 2) if atr_value > 0 else 0,
            'risk_percentage': (final_quantity * atr_value * 2) / account_balance * 100 if atr_value > 0 and account_balance > 0 else 0,
            'leverage_used': mis_leverage,
            'stop_loss_distance': atr_value * 2 if atr_value > 0 else current_price * 0.02
        }
        
        logger.info(f"📊 Calculated Position:")
        logger.info(f"   Quantity: {final_quantity} shares")
        logger.info(f"   Margin: ₹{margin_required:,.2f}")
        logger.info(f"   Trade Value: ₹{sizing_details['trade_value']:,.2f}")
        logger.info(f"   Risk: {sizing_details['risk_percentage']:.1f}%")
        logger.info(f"   Leverage: {mis_leverage}x")
        
        return sizing_details
    
    def calculate_minimum_quantity(self, account_balance: float, current_price: float, leverage: float) -> int:
        """Calculate minimum viable quantity based on account size"""
        # Minimum trade should be at least 0.5% of account balance
        min_trade_value = max(account_balance * 0.005, 500)  # Minimum ₹500 or 0.5% of balance
        
        # Calculate minimum quantity needed
        min_quantity = max(1, int(min_trade_value / current_price))
        
        # Ensure we can afford the margin
        margin_per_share = current_price / leverage
        max_affordable = int(account_balance * 0.9 / margin_per_share)  # Use 90% of balance max
        
        return min(min_quantity, max_affordable, 1)  # At least 1 share
    
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