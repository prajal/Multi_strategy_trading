# backtesting/data_fetcher.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from auth.kite_auth import KiteAuth
from utils.logger import get_logger

logger = get_logger(__name__)

class HistoricalDataFetcher:
    """Fetch and prepare historical data for backtesting"""
    
    def __init__(self):
        self.auth = KiteAuth()
        self.kite = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup Kite connection"""
        self.kite = self.auth.get_kite_instance()
        if not self.kite:
            logger.error("❌ Failed to setup Kite connection for data fetching")
    
    def fetch_historical_data(self, 
                            instrument_token: str, 
                            start_date: str, 
                            end_date: str, 
                            interval: str = "30minute") -> pd.DataFrame:
        """
        Fetch historical data from Kite
        
        Args:
            instrument_token: Token for instrument (e.g., "256265" for NIFTY 50)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Data interval (minute, 3minute, 5minute, 15minute, 30minute, 60minute, day)
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.kite:
            logger.error("❌ Kite connection not available")
            return pd.DataFrame()
        
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            logger.info(f"📊 Fetching data for {instrument_token}")
            logger.info(f"📅 Period: {start_date} to {end_date}")
            logger.info(f"⏱️ Interval: {interval}")
            
            # Fetch data from Kite
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=start_dt,
                to_date=end_dt,
                interval=interval
            )
            
            if not historical_data:
                logger.warning(f"⚠️ No data received for {instrument_token}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Set timestamp as index
            df['timestamp'] = pd.to_datetime(df['date'])
            df.set_index('timestamp', inplace=True)
            df.drop('date', axis=1, inplace=True)
            
            # Ensure all required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"❌ Missing column: {col}")
                    return pd.DataFrame()
            
            # Sort by timestamp
            df.sort_index(inplace=True)
            
            logger.info(f"✅ Data fetched: {len(df)} records")
            logger.info(f"📈 Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch historical data: {e}")
            return pd.DataFrame()
    
    def prepare_backtest_data(self, 
                            signal_instrument: str = "256265",  # NIFTY 50
                            trading_instrument: str = "2707457",  # NIFTYBEES
                            days_back: int = 30,
                            interval: str = "30minute") -> pd.DataFrame:
        """
        Prepare data for backtesting with proper price scaling
        
        Args:
            signal_instrument: Token for signal generation (NIFTY 50)
            trading_instrument: Token for trading prices (NIFTYBEES)
            days_back: Number of days of historical data
            interval: Data interval
        
        Returns:
            Combined DataFrame with both signal and trading data
        """
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        logger.info(f"🎯 Preparing backtest data")
        logger.info(f"📊 Signal source: {signal_instrument}")
        logger.info(f"💰 Trading prices: {trading_instrument}")
        
        # Fetch signal data (NIFTY 50)
        signal_data = self.fetch_historical_data(signal_instrument, start_str, end_str, interval)
        if signal_data.empty:
            logger.error("❌ Failed to fetch signal data")
            return pd.DataFrame()
        
        # Fetch trading data (NIFTYBEES)
        trading_data = self.fetch_historical_data(trading_instrument, start_str, end_str, interval)
        if trading_data.empty:
            logger.error("❌ Failed to fetch trading data")
            return pd.DataFrame()
        
        # Align data by timestamp (use inner join to ensure matching timestamps)
        combined = signal_data.join(trading_data, how='inner', rsuffix='_trading')
        
        if combined.empty:
            logger.error("❌ No matching timestamps between signal and trading data")
            return pd.DataFrame()
        
        # Use signal data for strategy calculations, trading data for prices
        # Keep signal OHLCV for indicator calculations
        # Keep trading close price for actual trade execution
        combined['trading_price'] = combined['close_trading']
        
        # Calculate some basic statistics
        signal_mean = combined['close'].mean()
        trading_mean = combined['trading_price'].mean()
        price_ratio = signal_mean / trading_mean
        
        logger.info(f"📊 Combined data: {len(combined)} records")
        logger.info(f"📈 Signal price avg: ₹{signal_mean:.2f}")
        logger.info(f"💰 Trading price avg: ₹{trading_mean:.2f}")
        logger.info(f"📊 Price ratio: {price_ratio:.2f}")
        
        return combined
    
    def load_sample_data(self, days: int = 30) -> pd.DataFrame:
        """
        Load sample data for testing (generates synthetic data if Kite unavailable)
        """
        try:
            # Try to fetch real data first
            return self.prepare_backtest_data(days_back=days)
        except:
            logger.warning("⚠️ Could not fetch real data, generating sample data")
            return self.generate_sample_data(days)
    
    def generate_sample_data(self, days: int = 30) -> pd.DataFrame:
        """Generate synthetic market data for testing"""
        
        logger.info(f"🔄 Generating {days} days of sample data")
        
        # Generate timestamps (30-minute intervals during market hours)
        start_date = datetime.now() - timedelta(days=days)
        timestamps = []
        
        current_date = start_date
        while current_date <= datetime.now():
            # Only market hours: 9:15 AM to 3:30 PM
            if current_date.weekday() < 5:  # Monday to Friday
                market_start = current_date.replace(hour=9, minute=15, second=0, microsecond=0)
                market_end = current_date.replace(hour=15, minute=30, second=0, microsecond=0)
                
                current_time = market_start
                while current_time <= market_end:
                    timestamps.append(current_time)
                    current_time += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
        
        # Generate realistic price data
        n_points = len(timestamps)
        base_price = 25000  # NIFTY base price
        
        # Generate random walk with trend
        returns = np.random.normal(0.0001, 0.01, n_points)  # Small positive drift
        price_series = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV data
        data = []
        for i, (timestamp, close) in enumerate(zip(timestamps, price_series)):
            # Generate realistic OHLC from close price
            volatility = close * 0.005  # 0.5% volatility
            
            high = close + np.random.exponential(volatility * 0.5)
            low = close - np.random.exponential(volatility * 0.5)
            
            if i == 0:
                open_price = close
            else:
                open_price = data[-1]['close'] + np.random.normal(0, volatility * 0.2)
            
            volume = np.random.randint(1000000, 5000000)
            
            # Add trading price (NIFTYBEES ≈ NIFTY/100)
            trading_price = close / 100 + np.random.normal(0, 0.1)
            
            data.append({
                'open': open_price,
                'high': max(open_price, high, close),
                'low': min(open_price, low, close),
                'close': close,
                'volume': volume,
                'trading_price': trading_price
            })
        
        df = pd.DataFrame(data, index=timestamps)
        
        logger.info(f"✅ Generated {len(df)} sample data points")
        logger.info(f"📈 Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
        
        return df
    
    def save_data(self, df: pd.DataFrame, filename: str):
        """Save data to CSV file"""
        try:
            df.to_csv(filename)
            logger.info(f"💾 Data saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save data: {e}")
    
    def load_data(self, filename: str) -> pd.DataFrame:
        """Load data from CSV file"""
        try:
            df = pd.read_csv(filename, index_col=0, parse_dates=True)
            logger.info(f"📂 Data loaded from {filename}: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return pd.DataFrame()
