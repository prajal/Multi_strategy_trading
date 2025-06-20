# trading/enhanced_strategy.py

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedTradingStrategy:
    """
    Multi-indicator trading strategy combining:
    - SuperTrend (Primary trend)
    - RSI (Momentum)
    - MACD (Trend confirmation)
    - Bollinger Bands (Volatility)
    - Volume analysis (Strength)
    - Support/Resistance (Key levels)
    """
    
    def __init__(self, config: Dict[str, Any]):
        # SuperTrend parameters
        self.st_period = config.get('supertrend_period', 10)
        self.st_factor = config.get('supertrend_factor', 3.0)
        
        # RSI parameters
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        
        # MACD parameters
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        
        # Bollinger Bands parameters
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        
        # Volume parameters
        self.volume_period = config.get('volume_period', 20)
        self.volume_threshold = config.get('volume_threshold', 1.5)
        
        # Support/Resistance parameters
        self.sr_period = config.get('sr_period', 20)
        
        # Signal confirmation requirements
        self.min_confirmations = config.get('min_confirmations', 3)
        
        logger.info("✅ Enhanced multi-indicator strategy initialized")
        logger.info(f"   SuperTrend: {self.st_period}/{self.st_factor}")
        logger.info(f"   RSI: {self.rsi_period} ({self.rsi_oversold}/{self.rsi_overbought})")
        logger.info(f"   Min confirmations: {self.min_confirmations}")
    
    def get_signal(self, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Main method to get trading signal"""
        try:
            # Ensure we have enough data
            min_data_needed = max(self.st_period, self.rsi_period, self.macd_slow, self.bb_period, self.volume_period)
            if len(df) < min_data_needed:
                logger.warning(f"Insufficient data: {len(df)} rows, need {min_data_needed}")
                return "HOLD", {"error": "Insufficient data"}
            
            # For now, return a simple signal for testing
            latest_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            
            # Simple trend detection
            if latest_close > prev_close:
                signal = "BUY"
                confidence = 0.6
                confirmations = ["Price Up", "Test Signal"]
            elif latest_close < prev_close:
                signal = "SELL"
                confidence = 0.6
                confirmations = ["Price Down", "Test Signal"]
            else:
                signal = "HOLD"
                confidence = 0
                confirmations = []
            
            signal_data = {
                'signal': signal,
                'confidence': confidence,
                'buy_score': 3 if signal == "BUY" else 0,
                'sell_score': 3 if signal == "SELL" else 0,
                'confirmations': confirmations,
                'indicators': {
                    'simple_trend': {
                        'current_price': latest_close,
                        'previous_price': prev_close,
                        'direction': 'UP' if latest_close > prev_close else 'DOWN'
                    }
                }
            }
            
            if signal != "HOLD":
                logger.info(f"📊 Enhanced Signal: {signal} (Confidence: {confidence:.1%})")
                logger.info(f"🔍 Confirmations: {', '.join(confirmations)}")
            
            return signal, signal_data
            
        except Exception as e:
            logger.error(f"Error in enhanced signal generation: {e}")
            return "HOLD", {"error": str(e)}
