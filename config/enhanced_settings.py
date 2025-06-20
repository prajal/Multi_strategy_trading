# Create these files in the specified order to fix the import errors

# =============================================================================
# FILE 1: config/enhanced_settings.py
# =============================================================================

# Enhanced Strategy Configuration Settings

ENHANCED_STRATEGY_CONFIG = {
    # SuperTrend settings
    'supertrend_period': 10,
    'supertrend_factor': 3.0,
    
    # RSI settings
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    
    # MACD settings
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # Bollinger Bands settings
    'bb_period': 20,
    'bb_std': 2,
    
    # Volume settings
    'volume_period': 20,
    'volume_threshold': 1.5,  # 1.5x average volume
    
    # Support/Resistance settings
    'sr_period': 20,
    
    # Signal confirmation
    'min_confirmations': 3,  # Minimum score to generate signal
    
    # Risk management
    'max_risk_per_trade': 2.0,      # 2% of capital
    'max_daily_loss': 5.0,          # 5% daily loss limit
    'stop_loss_atr_multiple': 2.0,   # 2x ATR for stop loss
    'take_profit_risk_ratio': 2.0,   # 2:1 risk-reward ratio
    'max_drawdown_limit': 10.0,      # 10% max drawdown
    'max_position_value': 20.0,      # 20% max position size
    'max_trades_per_day': 5,         # Max 5 trades per day
    
    # Position sizing
    'base_position_size': 0.8,       # 80% of available capital
    'confidence_multiplier': True,   # Scale position by signal confidence
    'volatility_adjustment': True,   # Adjust for market volatility
    
    # Account settings (update these with your values)
    'account_balance': 5000.0,       # Your trading capital
    'check_interval': 30,            # Check every 30 seconds
}

# Different strategy profiles for different risk appetites
STRATEGY_PROFILES = {
    'conservative': {
        **ENHANCED_STRATEGY_CONFIG,
        'min_confirmations': 4,
        'supertrend_factor': 3.5,
        'rsi_oversold': 25,
        'rsi_overbought': 75,
        'volume_threshold': 2.0,
        'base_position_size': 0.6,
        'max_risk_per_trade': 1.5,
        'max_daily_loss': 3.0,
        'max_trades_per_day': 3,
    },
    
    'balanced': {
        **ENHANCED_STRATEGY_CONFIG,
        # Uses default settings - good balance of risk/reward
    },
    
    'aggressive': {
        **ENHANCED_STRATEGY_CONFIG,
        'min_confirmations': 2,
        'supertrend_factor': 2.5,
        'rsi_oversold': 35,
        'rsi_overbought': 65,
        'volume_threshold': 1.2,
        'base_position_size': 1.0,
        'max_risk_per_trade': 3.0,
        'max_daily_loss': 7.0,
        'max_trades_per_day': 8,
    },
    
    'scalping': {
        **ENHANCED_STRATEGY_CONFIG,
        'supertrend_period': 7,
        'supertrend_factor': 2.0,
        'rsi_period': 9,
        'min_confirmations': 2,
        'bb_period': 15,
        'volume_threshold': 1.8,
        'base_position_size': 0.5,
        'max_risk_per_trade': 1.0,
        'max_trades_per_day': 15,
        'check_interval': 15,  # Check every 15 seconds
    }
}

# Market hours configuration
MARKET_CONFIG = {
    'market_open_time': '09:15',
    'market_close_time': '15:30',
    'auto_square_off_time': '15:20',  # Close positions 10 min before market close
    'pre_market_start': '09:00',
    'trading_days': [0, 1, 2, 3, 4],  # Monday to Friday
}

# Instruments configuration with their tokens
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