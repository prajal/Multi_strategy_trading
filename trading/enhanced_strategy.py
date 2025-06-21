# trading/enhanced_strategy.py - FIXED VERSION WITH MARKET REGIME FILTER

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedTradingStrategy:
    """
    Enhanced multi-indicator trading strategy with market regime filtering
    """
    
    def __init__(self, config: Dict[str, Any]):
        # SuperTrend parameters
        self.st_period = config.get('supertrend_period', 10)
        self.st_factor = config.get('supertrend_factor', 3.5)
        
        # RSI parameters
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_oversold = config.get('rsi_oversold', 25)
        self.rsi_overbought = config.get('rsi_overbought', 75)
        
        # MACD parameters
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        
        # Bollinger Bands parameters
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2)
        
        # Volume parameters
        self.volume_period = config.get('volume_period', 20)
        self.volume_threshold = config.get('volume_threshold', 2.0)
        
        # Support/Resistance parameters
        self.sr_period = config.get('sr_period', 20)
        
        # Signal confirmation requirements
        self.min_confirmations = config.get('min_confirmations', 4)
        
        # NEW: Market regime filter settings
        self.regime_filter_enabled = config.get('regime_filter_enabled', True)
        
        logger.info("✅ Enhanced multi-indicator strategy initialized with regime filter")
        logger.info(f"   SuperTrend: {self.st_period}/{self.st_factor}")
        logger.info(f"   RSI: {self.rsi_period} ({self.rsi_oversold}/{self.rsi_overbought})")
        logger.info(f"   Min confirmations: {self.min_confirmations}")
        logger.info(f"   Volume threshold: {self.volume_threshold}")
        logger.info(f"   Regime filter: {'ENABLED' if self.regime_filter_enabled else 'DISABLED'}")
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect market regime to filter poor trading conditions"""
        try:
            if len(df) < 50:
                return {'skip_trading': False, 'regime': 'INSUFFICIENT_DATA'}
            
            # Calculate volatility regime
            returns = df['close'].pct_change().dropna()
            if len(returns) < 20:
                return {'skip_trading': False, 'regime': 'INSUFFICIENT_DATA'}
            
            vol_20 = returns.rolling(20).std() * np.sqrt(252)  # Annualized volatility
            vol_current = vol_20.iloc[-1] if not vol_20.empty else 0.15
            vol_median = vol_20.median() if not vol_20.empty else 0.15
            
            # Calculate trend strength
            highs = df['high'].rolling(14).max()
            lows = df['low'].rolling(14).min()
            range_size = highs - lows
            
            # Avoid division by zero
            range_size = range_size.replace(0, df['close'].iloc[-1] * 0.01)
            
            trend_position = (df['close'] - lows) / range_size
            trend_current = trend_position.iloc[-1] if not trend_position.empty else 0.5
            
            # Calculate price momentum
            price_change_5 = df['close'].pct_change(5).iloc[-1] if len(df) >= 5 else 0
            price_momentum = abs(price_change_5)
            
            # Determine regime
            regime = {
                'volatility': 'HIGH' if vol_current > vol_median * 1.8 else 'NORMAL',
                'trend_strength': 'STRONG' if trend_current > 0.75 or trend_current < 0.25 else 'WEAK',
                'momentum': 'HIGH' if price_momentum > 0.02 else 'LOW',
                'vol_current': vol_current,
                'vol_median': vol_median,
                'trend_position': trend_current,
                'skip_trading': False
            }
            
            # Skip trading in poor conditions
            skip_conditions = [
                regime['volatility'] == 'HIGH' and regime['trend_strength'] == 'WEAK',
                regime['volatility'] == 'HIGH' and regime['momentum'] == 'LOW',
                vol_current > vol_median * 2.5  # Extremely high volatility
            ]
            
            if any(skip_conditions):
                regime['skip_trading'] = True
                regime['skip_reason'] = 'Poor market conditions detected'
                logger.info(f"🚫 Skipping trading: {regime['volatility']} volatility, {regime['trend_strength']} trend")
            
            return regime
            
        except Exception as e:
            logger.error(f"Error in market regime detection: {e}")
            return {'skip_trading': False, 'regime': 'ERROR'}
    
    def calculate_signal_quality(self, signal_data: Dict) -> float:
        """Calculate overall signal quality score (0-1)"""
        try:
            indicators = signal_data.get('indicators', {})
            confirmations = signal_data.get('confirmations', [])
            
            quality_score = 0
            max_score = 10
            
            # 1. RSI quality (2 points)
            rsi = indicators.get('rsi', 50)
            if rsi < 20 or rsi > 80:  # Extreme levels
                quality_score += 2
            elif rsi < 30 or rsi > 70:  # Strong levels
                quality_score += 1
            
            # 2. Volume confirmation (2 points)
            volume_data = indicators.get('volume', {})
            volume_ratio = volume_data.get('ratio', 1)
            if volume_ratio > 2.5:  # Very high volume
                quality_score += 2
            elif volume_ratio > 2.0:
                quality_score += 1.5
            elif volume_ratio > 1.5:
                quality_score += 1
            
            # 3. Trend alignment (3 points)
            supertrend_data = indicators.get('supertrend', {})
            price = supertrend_data.get('price', 0)
            supertrend_value = supertrend_data.get('value', 0)
            
            if price and supertrend_value:
                trend_strength = abs(price - supertrend_value) / price
                if trend_strength > 0.03:  # Very strong trend (>3%)
                    quality_score += 3
                elif trend_strength > 0.02:  # Strong trend (>2%)
                    quality_score += 2
                elif trend_strength > 0.01:  # Moderate trend (>1%)
                    quality_score += 1
            
            # 4. MACD confirmation (2 points)
            macd_data = indicators.get('macd', {})
            macd_line = macd_data.get('macd', 0)
            signal_line = macd_data.get('signal', 0)
            histogram = macd_data.get('histogram', 0)
            
            if abs(histogram) > 0:  # MACD has momentum
                quality_score += 1
                if (macd_line > signal_line and histogram > 0) or (macd_line < signal_line and histogram < 0):
                    quality_score += 1  # Aligned momentum
            
            # 5. Multiple confirmations bonus (1 point)
            if len(confirmations) >= 4:
                quality_score += 1
            
            return min(1.0, quality_score / max_score)  # Cap at 1.0
            
        except Exception as e:
            logger.error(f"Error calculating signal quality: {e}")
            return 0.5  # Default moderate quality
    
    def calculate_supertrend(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Calculate SuperTrend indicator - same as before"""
        try:
            # Calculate True Range
            df = df.copy()
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['close'].shift(1))
            df['tr3'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # Calculate ATR
            df['atr'] = df['tr'].rolling(window=self.st_period).mean()
            
            # Calculate basic bands
            df['basic_ub'] = (df['high'] + df['low']) / 2 + (self.st_factor * df['atr'])
            df['basic_lb'] = (df['high'] + df['low']) / 2 - (self.st_factor * df['atr'])
            
            # Calculate final bands
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
            return pd.Series([np.nan] * len(df), index=df.index), pd.Series([0] * len(df), index=df.index)
    
    def calculate_rsi(self, df: pd.DataFrame) -> pd.Series:
        """Calculate RSI indicator - same as before"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(df), index=df.index)
    
    def calculate_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD indicator - same as before"""
        try:
            exp1 = df['close'].ewm(span=self.macd_fast).mean()
            exp2 = df['close'].ewm(span=self.macd_slow).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=self.macd_signal).mean()
            histogram = macd - signal
            return macd, signal, histogram
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return (pd.Series([0] * len(df), index=df.index), 
                   pd.Series([0] * len(df), index=df.index), 
                   pd.Series([0] * len(df), index=df.index))
    
    def get_signal(self, df: pd.DataFrame) -> Tuple[str, Dict[str, Any]]:
        """Enhanced signal generation with regime filter and quality scoring"""
        try:
            # Ensure we have enough data
            min_data_needed = max(self.st_period, self.rsi_period, self.macd_slow, self.bb_period, self.volume_period)
            if len(df) < min_data_needed:
                logger.warning(f"Insufficient data: {len(df)} rows, need {min_data_needed}")
                return "HOLD", {"error": "Insufficient data"}
            
            # Check market regime first
            if self.regime_filter_enabled:
                regime = self.detect_market_regime(df)
                if regime.get('skip_trading', False):
                    return "HOLD", {
                        "regime": regime,
                        "reason": "Poor market conditions - skipping trade"
                    }
            else:
                regime = {'regime': 'FILTER_DISABLED'}
            
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
            
            # 2. RSI Analysis (Weight: 2) - More selective with adjusted thresholds
            if not pd.isna(latest_rsi):
                if latest_rsi < self.rsi_oversold:
                    buy_score += 2
                    confirmations.append("RSI Oversold")
                elif latest_rsi > self.rsi_overbought:
                    sell_score += 2
                    confirmations.append("RSI Overbought")
                elif self.rsi_oversold < latest_rsi < (self.rsi_oversold + 10):
                    buy_score += 1
                    confirmations.append("RSI Bullish Zone")
                elif (self.rsi_overbought - 10) < latest_rsi < self.rsi_overbought:
                    sell_score += 1
                    confirmations.append("RSI Bearish Zone")
            
            # 3. MACD Analysis (Weight: 2) - More stringent
            if not pd.isna(latest_macd) and not pd.isna(latest_macd_signal):
                macd_histogram = latest_macd - latest_macd_signal
                if latest_macd > latest_macd_signal and macd_histogram > 0:
                    buy_score += 2
                    confirmations.append("MACD Bullish")
                elif latest_macd < latest_macd_signal and macd_histogram < 0:
                    sell_score += 2
                    confirmations.append("MACD Bearish")
            
            # 4. Volume Analysis (Weight: 2) - Higher threshold
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
            
            # Prepare initial signal data
            signal_data = {
                'signal': 'HOLD',
                'confidence': 0,
                'buy_score': buy_score,
                'sell_score': sell_score,
                'confirmations': confirmations,
                'regime': regime,
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
            
            # Calculate signal quality
            quality_score = self.calculate_signal_quality(signal_data)
            signal_data['quality_score'] = quality_score
            
            # Adjust minimum confirmations based on quality and regime
            adjusted_min_confirmations = self.min_confirmations
            
            # Quality-based adjustment
            if quality_score < 0.5:  # Low quality
                adjusted_min_confirmations += 1
            elif quality_score > 0.8:  # High quality
                adjusted_min_confirmations = max(2, adjusted_min_confirmations - 1)
            
            # Regime-based adjustment
            if self.regime_filter_enabled and regime.get('volatility') == 'HIGH':
                adjusted_min_confirmations += 1
            
            # Determine signal based on adjusted scores
            max_score = max(buy_score, sell_score)
            
            if buy_score >= adjusted_min_confirmations and buy_score > sell_score:
                signal = "BUY"
                confidence = min(0.95, (buy_score / 12) * (1 + quality_score * 0.5))
            elif sell_score >= adjusted_min_confirmations and sell_score > buy_score:
                signal = "SELL"
                confidence = min(0.95, (sell_score / 12) * (1 + quality_score * 0.5))
            else:
                signal = "HOLD"
                confidence = 0
            
            # Update signal data
            signal_data['signal'] = signal
            signal_data['confidence'] = confidence
            signal_data['adjusted_min_confirmations'] = adjusted_min_confirmations
            signal_data['quality_score'] = quality_score
            
            if signal != "HOLD":
                logger.info(f"📊 Enhanced Signal: {signal} (Confidence: {confidence:.1%})")
                logger.info(f"📈 Buy Score: {buy_score}, Sell Score: {sell_score} (Required: {adjusted_min_confirmations})")
                logger.info(f"🔍 Confirmations: {', '.join(confirmations)}")
                logger.info(f"⭐ Quality Score: {quality_score:.1%}")
                logger.info(f"💰 Price: ₹{latest_close:.2f} | SuperTrend: ₹{latest_supertrend:.2f}")
                logger.info(f"📊 RSI: {latest_rsi:.1f} | ATR: ₹{atr:.2f}")
                if self.regime_filter_enabled:
                    logger.info(f"🌐 Market Regime: {regime.get('volatility', 'N/A')} volatility, {regime.get('trend_strength', 'N/A')} trend")
            
            return signal, signal_data
            
        except Exception as e:
            logger.error(f"Error in enhanced signal generation: {e}")
            import traceback
            traceback.print_exc()
            return "HOLD", {"error": str(e)}