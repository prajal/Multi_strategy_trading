# trading/position_sizer.py - FIXED VERSION WITH PROPER ATR SCALING

import pandas as pd
import numpy as np
from typing import Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedPositionSizer:
    """
    Advanced position sizing with proper ATR scaling and improved risk management
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_risk = config.get('max_risk_per_trade', 1.5) / 100  # Updated default
        self.base_size = config.get('base_position_size', 0.6)
        self.confidence_mult = config.get('confidence_multiplier', True)
        self.volatility_adj = config.get('volatility_adjustment', True)
        
        logger.info("✅ Enhanced position sizer initialized with ATR scaling")
        logger.info(f"   Max risk per trade: {self.max_risk:.1%}")
        logger.info(f"   Base position size: {self.base_size:.1%}")
    
    def scale_nifty_atr_to_instrument(self, nifty_atr: float, current_price: float, symbol: str) -> float:
        """
        CRITICAL FIX: Properly scale NIFTY ATR to trading instrument
        """
        try:
            # Define typical price ratios and scaling factors
            scaling_factors = {
                'NIFTYBEES': {
                    'typical_nifty_price': 25000,
                    'typical_instrument_price': 280,
                    'atr_ratio': 0.8  # NIFTYBEES typically has lower volatility than NIFTY
                },
                'JUNIORBEES': {
                    'typical_nifty_price': 25000,
                    'typical_instrument_price': 420,
                    'atr_ratio': 0.9
                },
                'BANKBEES': {
                    'typical_nifty_price': 25000,
                    'typical_instrument_price': 470,
                    'atr_ratio': 1.1  # Bank index can be more volatile
                }
            }
            
            if symbol in scaling_factors:
                scale_info = scaling_factors[symbol]
                
                # Calculate scaling ratio
                price_ratio = current_price / scale_info['typical_nifty_price']
                atr_ratio = scale_info['atr_ratio']
                
                # Scale the ATR
                scaled_atr = nifty_atr * price_ratio * atr_ratio
                
                # Apply reasonable bounds (1% to 8% of current price)
                min_atr = current_price * 0.01
                max_atr = current_price * 0.08
                final_atr = max(min_atr, min(scaled_atr, max_atr))
                
                logger.info(f"🔧 ATR Scaling for {symbol}:")
                logger.info(f"   NIFTY ATR: ₹{nifty_atr:.2f}")
                logger.info(f"   Price Ratio: {price_ratio:.4f}")
                logger.info(f"   ATR Ratio: {atr_ratio:.2f}")
                logger.info(f"   Scaled ATR: ₹{scaled_atr:.2f} → ₹{final_atr:.2f}")
                
                return final_atr
            else:
                # Default scaling for unknown instruments
                estimated_ratio = current_price / 25000
                scaled_atr = nifty_atr * estimated_ratio
                min_atr = current_price * 0.015
                max_atr = current_price * 0.06
                return max(min_atr, min(scaled_atr, max_atr))
                
        except Exception as e:
            logger.error(f"Error in ATR scaling: {e}")
            # Fallback: use percentage of current price
            return current_price * 0.02  # 2% fallback
    
    def calculate_position_size(self, 
                              account_balance: float,
                              current_price: float, 
                              atr_value: float,
                              signal_confidence: float,
                              symbol: str = "NIFTYBEES") -> Dict[str, Any]:
        """
        Calculate optimal position size with proper ATR scaling - FIXED VERSION
        """
        
        # Ensure minimum values
        account_balance = max(account_balance, 1000)  # Minimum ₹1000
        current_price = max(current_price, 1)  # Minimum ₹1
        signal_confidence = max(signal_confidence, 0.3)  # Minimum 30% confidence
        
        logger.info(f"💰 Position Sizing for {symbol}:")
        logger.info(f"   Account: ₹{account_balance:,.2f}")
        logger.info(f"   Price: ₹{current_price:.2f}")
        logger.info(f"   Raw ATR: ₹{atr_value:.2f}")
        logger.info(f"   Confidence: {signal_confidence:.1%}")
        
        # CRITICAL FIX: Scale ATR properly for the trading instrument
        scaled_atr = self.scale_nifty_atr_to_instrument(atr_value, current_price, symbol)
        
        # Base capital allocation with confidence adjustment
        base_capital = account_balance * self.base_size
        
        # Apply confidence multiplier
        if self.confidence_mult:
            # More conservative confidence scaling
            confidence_factor = 0.5 + (signal_confidence * 0.5)  # 50% to 100%
            adjusted_capital = base_capital * confidence_factor
        else:
            adjusted_capital = base_capital
        
        # Apply volatility adjustment
        if self.volatility_adj and scaled_atr > 0:
            # Higher volatility = smaller position
            normal_atr = current_price * 0.02  # 2% as normal volatility
            volatility_factor = min(1.0, normal_atr / scaled_atr)
            volatility_factor = max(0.3, volatility_factor)  # Don't reduce below 30%
            adjusted_capital = adjusted_capital * volatility_factor
        else:
            volatility_factor = 1.0
        
        # Get MIS leverage for the symbol
        mis_leverage = self.get_mis_leverage(symbol)
        effective_capital = adjusted_capital * mis_leverage
        
        # Risk-based position sizing using scaled ATR
        stop_distance = scaled_atr * self.config.get('stop_loss_atr_multiple', 2.5)
        
        # Calculate maximum shares based on risk limit
        max_risk_amount = account_balance * self.max_risk
        max_shares_by_risk = int(max_risk_amount / stop_distance) if stop_distance > 0 else 1
        
        # Calculate shares based on capital
        max_shares_by_capital = int(effective_capital / current_price)
        
        # Take the minimum of both constraints
        base_quantity = min(max_shares_by_capital, max_shares_by_risk)
        
        # CRITICAL: Ensure minimum viable quantity
        min_quantity = self.calculate_minimum_quantity(account_balance, current_price, mis_leverage)
        final_quantity = max(min_quantity, base_quantity)
        
        # Calculate actual margin required
        margin_required = final_quantity * (current_price / mis_leverage)
        
        # Final safety check: Ensure we don't exceed available capital
        max_affordable_quantity = int((account_balance * 0.9) / (current_price / mis_leverage))
        if final_quantity > max_affordable_quantity:
            final_quantity = max_affordable_quantity
            margin_required = final_quantity * (current_price / mis_leverage)
        
        # Ensure we still have at least 1 share
        if final_quantity < 1:
            final_quantity = 1
            margin_required = current_price / mis_leverage
        
        # Calculate risk metrics
        actual_risk_amount = final_quantity * stop_distance
        risk_percentage = (actual_risk_amount / account_balance) * 100 if account_balance > 0 else 0
        
        # Position sizing details
        sizing_details = {
            'quantity': final_quantity,
            'margin_required': margin_required,
            'trade_value': final_quantity * current_price,
            'capital_utilization': margin_required / account_balance if account_balance > 0 else 0,
            'confidence_factor': signal_confidence,
            'volatility_factor': volatility_factor,
            'risk_per_trade': actual_risk_amount,
            'risk_percentage': risk_percentage,
            'leverage_used': mis_leverage,
            'stop_loss_distance': stop_distance,
            'scaled_atr': scaled_atr,
            'original_atr': atr_value,
            'max_risk_constraint': max_shares_by_risk,
            'capital_constraint': max_shares_by_capital
        }
        
        logger.info(f"📊 Calculated Position:")
        logger.info(f"   Quantity: {final_quantity} shares")
        logger.info(f"   Margin: ₹{margin_required:,.2f}")
        logger.info(f"   Trade Value: ₹{sizing_details['trade_value']:,.2f}")
        logger.info(f"   Risk: {risk_percentage:.1f}%")
        logger.info(f"   Leverage: {mis_leverage}x")
        logger.info(f"   Stop Distance: ₹{stop_distance:.2f}")
        logger.info(f"   Constraints: Risk={max_shares_by_risk}, Capital={max_shares_by_capital}")
        
        # Warning if risk is too high
        if risk_percentage > self.max_risk * 100:
            logger.warning(f"⚠️ Risk {risk_percentage:.1f}% exceeds limit {self.max_risk*100:.1f}%")
        
        return sizing_details
    
    def calculate_minimum_quantity(self, account_balance: float, current_price: float, leverage: float) -> int:
        """Calculate minimum viable quantity based on account size"""
        # Minimum trade should be at least 0.3% of account balance or ₹500
        min_trade_value = max(account_balance * 0.003, 500)
        
        # Calculate minimum quantity needed
        min_quantity = max(1, int(min_trade_value / current_price))
        
        # Ensure we can afford the margin
        margin_per_share = current_price / leverage
        max_affordable = int((account_balance * 0.85) / margin_per_share)  # Use 85% of balance max
        
        return min(min_quantity, max_affordable, 1)  # At least 1 share
    
    def get_mis_leverage(self, symbol: str) -> float:
        """Get MIS leverage for different instruments with conservative values"""
        # More conservative leverage values
        leverage_map = {
            'NIFTYBEES': 4.0,      # Reduced from 5.0
            'JUNIORBEES': 4.0,     # Reduced from 5.0
            'BANKBEES': 3.5,       # Reduced from 4.0
            'LIQUIDBEES': 3.0,
            'RELIANCE': 3.5,       # Reduced from 4.0
            'TCS': 3.5,
            'HDFCBANK': 3.5,
            'ICICIBANK': 3.5,
            'INFY': 3.5,
            'HINDUNILVR': 3.5,
            'ITC': 3.5,
            'KOTAKBANK': 3.5,
            'LT': 3.5,
            'SBIN': 3.5,
            'BAJFINANCE': 3.0      # Reduced from 3.5
        }
        return leverage_map.get(symbol.upper(), 3.0)  # Default 3x leverage
    
    def validate_position_size(self, sizing_details: Dict[str, Any], account_balance: float) -> Dict[str, Any]:
        """Validate and adjust position size if needed"""
        
        # Check if margin requirement is reasonable
        margin_ratio = sizing_details['margin_required'] / account_balance
        if margin_ratio > 0.8:  # Don't use more than 80% of capital
            adjustment_factor = 0.8 / margin_ratio
            sizing_details['quantity'] = max(1, int(sizing_details['quantity'] * adjustment_factor))
            sizing_details['margin_required'] = sizing_details['quantity'] * (sizing_details['trade_value'] / sizing_details['quantity']) / sizing_details['leverage_used']
            
            logger.warning(f"⚠️ Position size adjusted down due to high margin usage: {margin_ratio:.1%}")
        
        # Check if risk is within acceptable limits
        if sizing_details['risk_percentage'] > self.max_risk * 100 * 1.1:  # 10% tolerance
            risk_adjustment = (self.max_risk * 100) / sizing_details['risk_percentage']
            sizing_details['quantity'] = max(1, int(sizing_details['quantity'] * risk_adjustment))
            
            logger.warning(f"⚠️ Position size adjusted down due to high risk: {sizing_details['risk_percentage']:.1f}%")
        
        return sizing_details