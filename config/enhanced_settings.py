# config/enhanced_settings.py - FIXED VERSION WITH IMPROVED SIGNAL QUALITY

# Enhanced Strategy Configuration Settings

ENHANCED_STRATEGY_CONFIG = {
    # SuperTrend settings - More conservative
    'supertrend_period': 10,
    'supertrend_factor': 3.5,  # Increased from 3.0
    
    # RSI settings - More extreme levels
    'rsi_period': 14,
    'rsi_oversold': 25,        # More extreme from 30
    'rsi_overbought': 75,      # More extreme from 70
    
    # MACD settings
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # Bollinger Bands settings
    'bb_period': 20,
    'bb_std': 2,
    
    # Volume settings - Higher threshold
    'volume_period': 20,
    'volume_threshold': 2.0,   # Increased from 1.5
    
    # Support/Resistance settings
    'sr_period': 20,
    
    # Signal confirmation - Higher threshold
    'min_confirmations': 4,    # Increased from 3
    
    # Risk management - More conservative
    'max_risk_per_trade': 1.5,     # Reduced from 2.0
    'max_daily_loss': 4.0,         # Reduced from 5.0
    'stop_loss_atr_multiple': 2.5, # Increased from 2.0
    'take_profit_risk_ratio': 2.5, # Increased from 2.0
    'max_drawdown_limit': 8.0,     # Reduced from 10.0
    'max_position_value': 15.0,    # Reduced from 20.0
    'max_trades_per_day': 3,       # Reduced from 5
    
    # Position sizing - More conservative
    'base_position_size': 0.6,     # Reduced from 0.8
    'confidence_multiplier': True,
    'volatility_adjustment': True,
    
    # Account settings
    'account_balance': 20000.0,
    'check_interval': 45,          # Increased from 30
    
    # NEW: Market regime settings
    'regime_filter_enabled': True,
    'min_hold_time_hours': 2,      # Minimum hold time
    'signal_reversal_threshold': 0.65,  # Require 65% confidence for reversal
}

# Updated strategy profiles with better risk management
STRATEGY_PROFILES = {
    'conservative': {
        **ENHANCED_STRATEGY_CONFIG,
        'min_confirmations': 5,        # Very high threshold
        'supertrend_factor': 4.0,      # Very conservative
        'rsi_oversold': 20,            # Extreme levels
        'rsi_overbought': 80,
        'volume_threshold': 2.5,       # High volume requirement
        'base_position_size': 0.4,     # Small positions
        'max_risk_per_trade': 1.0,     # Low risk
        'max_daily_loss': 3.0,
        'max_trades_per_day': 2,       # Very selective
        'check_interval': 60,          # Slow checking
        'signal_reversal_threshold': 0.75,  # Very high reversal threshold
    },
    
    'balanced': {
        **ENHANCED_STRATEGY_CONFIG,
        'min_confirmations': 4,        # High threshold
        'supertrend_factor': 3.5,      # Conservative
        'rsi_oversold': 25,            # More extreme
        'rsi_overbought': 75,
        'volume_threshold': 2.0,       # Higher volume
        'base_position_size': 0.6,     # Moderate positions
        'max_risk_per_trade': 1.5,     # Moderate risk
        'max_daily_loss': 4.0,
        'max_trades_per_day': 3,       # Selective
        'check_interval': 45,          # Moderate checking
        'signal_reversal_threshold': 0.65,  # High reversal threshold
    },
    
    'aggressive': {
        **ENHANCED_STRATEGY_CONFIG,
        'min_confirmations': 3,        # Still require 3+ but improve other filters
        'supertrend_factor': 3.0,      # Less conservative than before
        'rsi_oversold': 30,            # Standard levels
        'rsi_overbought': 70,
        'volume_threshold': 1.8,       # Higher than original
        'base_position_size': 0.8,     # Larger positions
        'max_risk_per_trade': 2.0,     # Higher risk
        'max_daily_loss': 5.0,
        'max_trades_per_day': 5,       # More trades
        'check_interval': 30,          # Standard checking
        'signal_reversal_threshold': 0.55,  # Lower reversal threshold
    },
    
    'scalping': {
        **ENHANCED_STRATEGY_CONFIG,
        'supertrend_period': 7,
        'supertrend_factor': 2.5,      # More sensitive but with other filters
        'rsi_period': 9,
        'min_confirmations': 3,        # Keep low but add quality filters
        'bb_period': 15,
        'volume_threshold': 2.2,       # High volume for scalping
        'base_position_size': 0.4,     # Small positions for frequent trading
        'max_risk_per_trade': 1.0,     # Low risk per trade
        'max_trades_per_day': 8,       # Allow more trades
        'check_interval': 20,          # Faster checking
        'signal_reversal_threshold': 0.60,  # Moderate reversal threshold
    }
}

# Market hours configuration (unchanged)
MARKET_CONFIG = {
    'market_open_time': '09:15',
    'market_close_time': '15:30',
    'auto_square_off_time': '15:15',
    'pre_market_start': '09:00',
    'trading_days': [0, 1, 2, 3, 4],
}

# Instruments configuration (unchanged)
INSTRUMENTS = {
    'NIFTY_50': {
        'token': '256265',
        'symbol': 'NIFTY 50'
    },
    'NIFTYBEES': {
        'token': '2707457',
        'symbol': 'NIFTYBEES',
        'exchange': 'NSE',
        'lot_size': 1
    },
    'JUNIORBEES': {
        'token': '2769665',
        'symbol': 'JUNIORBEES',
        'exchange': 'NSE',
        'lot_size': 1
    },
    'BANKBEES': {
        'token': '273665',
        'symbol': 'BANKBEES',
        'exchange': 'NSE',
        'lot_size': 1
    }
}