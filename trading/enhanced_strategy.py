# trading/enhanced_strategy.py - FIXED VERSION

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
    
    def calculate_supertrend(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate SuperTrend indicator"""
        try:
            # Calculate True Range
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR
            df['atr'] = df['tr'].rolling(window=self.st_period).mean()
            
            # Calculate basic bands
            df['basic_ub'] = (df['high'] + df['low']) / 2 + (self.st_factor * df['atr'])
            df['basic_lb'] = (df['high'] + df['low']) / 2 - (self.st_factor * df['atr'])
            
            # Calculate final upper and lower bands
            df['final_ub'] = df['basic_ub']
            df['final_lb'] = df['basic_lb']
            
            for i in range(1, len(df)):
                if pd.isna(df['basic_ub'].iloc[i-1]):
                    continue
                    
                # Final Upper Band
                if df['basic_ub'].iloc[i] < df['final_ub'].iloc[i-1] or df['close'].iloc[i-1] > df['final_ub'].iloc[i-1]:
                    df.at[df.index[i], 'final_ub'] = df['basic_ub'].iloc[i]
                else:
                    df.at[df.index[i], 'final_ub'] = df['final_ub'].iloc[i-1]
                
                # Final Lower Band
                if df['basic_lb'].iloc[i] > df['final_lb'].iloc[i-1] or df['close'].iloc[i-1] < df['final_lb'].iloc[i-1]:
                    df.at[df.index[i], 'final_lb'] = df['basic_lb'].iloc[i]
                else:
                    df.at[df.index[i], 'final_lb'] = df['final_lb'].iloc[i-1]
            
            # Calculate SuperTrend
            df['supertrend'] = np.nan
            df['trend'] = np.nan
            
            for i in range(len(df)):
                if pd.isna(df['final_ub'].iloc[i]) or pd.isna(df['final_lb'].iloc[i]):
                    continue
                    
                if i == 0:
                    df.at[df.index[i], 'supertrend'] = df['final_ub'].iloc[i]
                    df.at[df.index[i], 'trend'] = 1
                else:
                    prev_supertrend = df['supertrend'].iloc[i-1]
                    prev_trend = df['trend'].iloc[i-1]
                    
                    if prev_trend == 1:
                        if df['close'].iloc[i] <= df['final_lb'].iloc[i]:
                            df.at[df.index[i], 'supertrend'] = df['final_lb'].iloc[i]
                            df.at[df.index[i], 'trend'] = -1
                        else:
                            df.at[df.index[i], 'supertrend'] = df['final_lb'].iloc[i]
                            df.at[df.index[i], 'trend'] = 1
                    else:
                        if df['close'].iloc[i] >= df['final_ub'].iloc[i]:
                            df.at[df.index[i], 'supertrend'] = df['final_ub'].iloc[i]
                            df.at[df.index[i], 'trend'] = 1
                        else:
                            df.at[df.index[i], 'supertrend'] = df['final_ub'].iloc[i]
                            df.at[df.index[i], 'trend'] = -1
            
            return df['supertrend'], df['trend']
            
        except Exception as e:
            logger.error(f"Error calculating SuperTrend: {e}")
            return pd.Series([np.nan] * len(df)), pd.Series([0] * len(df))
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(df))
    
    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        try:
            exp1 = df['close'].ewm(span=self.macd_fast).mean()
            exp2 = df['close'].ewm(span=self.macd_slow).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=self.macd_signal).mean()
            histogram = macd - signal
            return macd, signal, histogram
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return pd.Series([0] * len(df)), pd.Series([0] * len(df)), pd.Series([0] * len(df))
    
    def get_signal(self, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Main method to get trading signal with PROPER indicator analysis"""
        try:
            # Ensure we have enough data
            min_data_needed = max(self.st_period, self.rsi_period, self.macd_slow, self.bb_period, self.volume_period)
            if len(df) < min_data_needed:
                logger.warning(f"Insufficient data: {len(df)} rows, need {min_data_needed}")
                return "HOLD", {"error": "Insufficient data"}
            
            # Calculate all indicators
            supertrend, trend = self.calculate_supertrend(df.copy())
            rsi = self.calculate_rsi(df)
            macd, macd_signal, macd_hist = self.calculate_macd(df)
            
            # Get latest values
            latest_close = df['close'].iloc[-1]
            latest_supertrend = supertrend.iloc[-1]
            latest_trend = trend.iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_macd = macd.iloc[-1]
            latest_macd_signal = macd_signal.iloc[-1]
            latest_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].rolling(window=self.volume_period).mean().iloc[-1]
            
            # Calculate ATR for risk management
            df_temp = df.copy()
            df_temp['tr1'] = df_temp['high'] - df_temp['low']
            df_temp['tr2'] = abs(df_temp['high'] - df_temp['close'].shift(1))
            df_temp['tr3'] = abs(df_temp['low'] - df_temp['close'].shift(1))
            df_temp['tr'] = df_temp[['tr1', 'tr2', 'tr3']].max(axis=1)
            atr = df_temp['tr'].rolling(window=14).mean().iloc[-1]
            
            # Initialize scoring system
            buy_score = 0
            sell_score = 0
            confirmations = []
            
            # 1. SuperTrend Analysis (Weight: 3)
            if not pd.isna(latest_trend):
                if latest_trend == 1 and latest_close > latest_supertrend:
                    buy_score += 3
                    confirmations.append("SuperTrend Bullish")
                elif latest_trend == -1 and latest_close < latest_supertrend:
                    sell_score += 3
                    confirmations.append("SuperTrend Bearish")
            
            # 2. RSI Analysis (Weight: 2)
            if not pd.isna(latest_rsi):
                if latest_rsi < self.rsi_oversold:
                    buy_score += 2
                    confirmations.append("RSI Oversold")
                elif latest_rsi > self.rsi_overbought:
                    sell_score += 2
                    confirmations.append("RSI Overbought")
                elif 30 < latest_rsi < 50:
                    buy_score += 1
                    confirmations.append("RSI Bullish Zone")
                elif 50 < latest_rsi < 70:
                    sell_score += 1
                    confirmations.append("RSI Bearish Zone")
            
            # 3. MACD Analysis (Weight: 2)
            if not pd.isna(latest_macd) and not pd.isna(latest_macd_signal):
                if latest_macd > latest_macd_signal and latest_macd > 0:
                    buy_score += 2
                    confirmations.append("MACD Bullish")
                elif latest_macd < latest_macd_signal and latest_macd < 0:
                    sell_score += 2
                    confirmations.append("MACD Bearish")
            
            # 4. Volume Analysis (Weight: 2)
            if not pd.isna(latest_volume) and not pd.isna(avg_volume):
                volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 1
                if volume_ratio > self.volume_threshold:
                    # High volume supports the trend
                    if buy_score > sell_score:
                        buy_score += 2
                        confirmations.append("High Volume Support")
                    elif sell_score > buy_score:
                        sell_score += 2
                        confirmations.append("High Volume Support")
            
            # 5. Price Action (Weight: 1)
            if len(df) >= 3:
                recent_highs = df['high'].iloc[-3:].max()
                recent_lows = df['low'].iloc[-3:].min()
                if latest_close > recent_highs * 0.999:  # Near recent high
                    buy_score += 1
                    confirmations.append("Breaking High")
                elif latest_close < recent_lows * 1.001:  # Near recent low
                    sell_score += 1
                    confirmations.append("Breaking Low")
            
            # Determine signal based on scores
            max_score = max(buy_score, sell_score)
            
            if buy_score >= self.min_confirmations and buy_score > sell_score:
                signal = "BUY"
                confidence = min(0.95, buy_score / 12)  # Max possible score is 12
            elif sell_score >= self.min_confirmations and sell_score > buy_score:
                signal = "SELL"
                confidence = min(0.95, sell_score / 12)
            else:
                signal = "HOLD"
                confidence = 0
            
            # Prepare signal data
            signal_data = {
                'signal': signal,
                'confidence': confidence,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'confirmations': confirmations,
                'indicators': {
                    'supertrend': {
                        'value': latest_supertrend,
                        'trend': latest_trend,
                        'price': latest_close
                    },
                    'rsi': latest_rsi,
                    'macd': {
                        'macd': latest_macd,
                        'signal': latest_macd_signal,
                        'histogram': latest_macd - latest_macd_signal
                    },
                    'volume': {
                        'current': latest_volume,
                        'average': avg_volume,
                        'ratio': latest_volume / avg_volume if avg_volume > 0 else 1
                    },
                    'atr': atr,
                    'price': latest_close
                }
            }
            
            if signal != "HOLD":
                logger.info(f"📊 Enhanced Signal: {signal} (Confidence: {confidence:.1%})")
                logger.info(f"📈 Buy Score: {buy_score}, Sell Score: {sell_score}")
                logger.info(f"🔍 Confirmations: {', '.join(confirmations)}")
                logger.info(f"💰 Price: ₹{latest_close:.2f} | SuperTrend: ₹{latest_supertrend:.2f}")
                logger.info(f"📊 RSI: {latest_rsi:.1f} | ATR: ₹{atr:.2f}")
            
            return signal, signal_data
            
        except Exception as e:
            logger.error(f"Error in enhanced signal generation: {e}")
            import traceback
            traceback.print_exc()
            return "HOLD", {"error": str(e)}