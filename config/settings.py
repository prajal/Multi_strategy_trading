import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Complete settings class with all required attributes for compatibility"""
    
    # API Keys from environment or hardcoded values
    KITE_API_KEY = os.getenv('KITE_API_KEY', 't4otrxd7h438r47b')
    KITE_API_SECRET = os.getenv('KITE_API_SECRET', 'rm4zbprszz13h5dhuoo2mp1czl1wxn45')
    KITE_REDIRECT_URI = os.getenv('KITE_REDIRECT_URI', 'http://localhost:3000')
    
    # File paths - using Path objects to support .exists() method
    LOG_FILE = Path('logs/trading.log')
    TOKEN_FILE = Path('data/kite_tokens.json')
    TOKENS_FILE = Path('data/kite_tokens.json')  # Alternative naming
    CONFIG_FILE = Path('saved_trading_config.json')
    DATA_DIR = Path('data')
    LOGS_DIR = Path('logs')
    
    # API Configuration
    API_CONFIG = {
        'base_url': 'https://api.kite.trade',
        'login_url': 'https://kite.zerodha.com/connect/login',
        'redirect_uri': KITE_REDIRECT_URI,
        'api_key': KITE_API_KEY,
        'api_secret': KITE_API_SECRET
    }
    
    # Strategy Parameters
    STRATEGY_PARAMS = {
        'atr_period': 10,
        'factor': 3.0,
        'historical_days': 5,
        'min_candles_required': 50,
        'check_interval': 30,
        'account_balance': 5000.0,
        'capital_allocation_percent': 80.0,
        'fixed_stop_loss': 200.0,
        'max_trade_amount': 4000
    }
    
    # Safety Configuration
    SAFETY_CONFIG = {
        'dry_run_mode': os.getenv('DRY_RUN_MODE', 'false').lower() == 'true',
        'live_trading_enabled': os.getenv('LIVE_TRADING_ENABLED', 'true').lower() == 'true',
        'max_daily_trades': 5,
        'position_size_limit': 0.2,
        'emergency_stop': False
    }
    
    # Logging Configuration
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '[%(asctime)s] %(levelname)s: %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
        'filename': str(LOG_FILE)  # Convert to string for logging
    }
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        Path('config').mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_log_file_path(cls):
        """Get the log file path"""
        cls.ensure_directories()
        return str(cls.LOG_FILE)
    
    @classmethod
    def get_tokens_file_path(cls):
        """Get the tokens file path"""
        cls.ensure_directories()
        return str(cls.TOKEN_FILE)
    
    @classmethod
    def load_config(cls):
        """Load configuration (placeholder for future use)"""
        cls.ensure_directories()
        return True
    
    @classmethod
    def save_config(cls):
        """Save configuration (placeholder for future use)"""
        cls.ensure_directories()
        return True
