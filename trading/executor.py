# trading/executor.py

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class OrderExecutor:
    """Order execution class for Kite Connect trading"""
    
    def __init__(self, kite):
        self.kite = kite
        logger.info("✅ OrderExecutor initialized")
    
    def place_order(self, tradingsymbol: str, transaction_type: str, quantity: int) -> Optional[str]:
        """
        Place order with correct Kite SDK format
        
        Args:
            tradingsymbol: Trading symbol (e.g., 'NIFTYBEES')
            transaction_type: 'BUY' or 'SELL'
            quantity: Number of shares
            
        Returns:
            Order ID if successful, None if failed
        """
        try:
            # Use the corrected format with variety as first positional argument
            order_id = self.kite.place_order(
                variety='regular',           # First positional argument (THE FIX!)
                tradingsymbol=tradingsymbol,
                exchange='NSE',
                transaction_type=transaction_type,
                order_type='MARKET',
                quantity=int(quantity),
                product='MIS',               # Intraday
                validity='DAY'               # Added required validity parameter
            )
            
            logger.info(f"✅ Order placed: {transaction_type} {quantity} {tradingsymbol} - ID: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"❌ Order failed: {transaction_type} {quantity} {tradingsymbol} - Error: {e}")
            return None
    
    def get_historical_data(self, instrument_token: str, from_date: datetime, to_date: datetime, interval: str = "30minute") -> pd.DataFrame:
        """
        Get historical data for analysis
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: Data interval
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Get historical data from Kite
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if not historical_data:
                logger.warning(f"No historical data received for {instrument_token}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Ensure we have the required columns
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing column {col} in historical data")
                    return pd.DataFrame()
            
            # Convert date column if it exists
            if 'date' in df.columns:
                df['timestamp'] = pd.to_datetime(df['date'])
            
            logger.info(f"✅ Historical data: {len(df)} records for {instrument_token}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Failed to get historical data for {instrument_token}: {e}")
            return pd.DataFrame()
    
    def get_latest_price(self, instrument_token: str) -> Optional[float]:
        """
        Get latest price for an instrument
        
        Args:
            instrument_token: Instrument token
            
        Returns:
            Latest price or None if failed
        """
        try:
            # Get quote data
            quote = self.kite.quote([instrument_token])
            
            if instrument_token in quote:
                latest_price = quote[instrument_token]['last_price']
                logger.debug(f"Latest price for {instrument_token}: ₹{latest_price}")
                return float(latest_price)
            else:
                logger.warning(f"No quote data for {instrument_token}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get latest price for {instrument_token}: {e}")
            return None
    
    def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions
        
        Returns:
            Dictionary with position information
        """
        try:
            positions = self.kite.positions()
            logger.debug("✅ Retrieved positions")
            return positions
            
        except Exception as e:
            logger.error(f"❌ Failed to get positions: {e}")
            return {}
    
    def sync_position_with_broker(self, current_position: Dict[str, Any]) -> tuple:
        """
        Sync position with broker to detect external changes
        
        Args:
            current_position: Current position tracking
            
        Returns:
            Tuple of (sync_needed: bool, status: str)
        """
        try:
            # Get actual positions from broker
            positions = self.get_positions()
            day_positions = positions.get('day', [])
            
            # Look for the current symbol
            symbol = current_position.get('tradingsymbol')
            if not symbol:
                return False, "NO_SYMBOL"
            
            # Find matching position
            broker_position = None
            for pos in day_positions:
                if pos.get('tradingsymbol') == symbol and pos.get('exchange') == 'NSE':
                    broker_position = pos
                    break
            
            current_qty = current_position.get('quantity', 0)
            
            if broker_position:
                broker_qty = broker_position.get('quantity', 0)
                
                if current_qty != broker_qty:
                    logger.warning(f"⚠️ Position mismatch: Bot={current_qty}, Broker={broker_qty}")
                    
                    if broker_qty == 0 and current_qty > 0:
                        logger.info("📉 Position was closed externally (auto square-off)")
                        return True, "CLOSED_EXTERNALLY"
                    else:
                        logger.info(f"🔄 Position synced: {broker_qty} shares")
                        current_position['quantity'] = broker_qty
                        return True, "SYNCED"
            else:
                if current_qty > 0:
                    logger.warning("⚠️ Position not found in broker, assuming closed")
                    return True, "CLOSED_EXTERNALLY"
            
            return False, "IN_SYNC"
            
        except Exception as e:
            logger.error(f"❌ Position sync failed: {e}")
            return False, "ERROR"
    
    def is_market_close_time(self) -> bool:
        """
        Check if it's close to market close time
        
        Returns:
            True if approaching market close
        """
        current_time = datetime.now().time()
        close_time = datetime.strptime("15:15", "%H:%M").time()  # 15 min before actual close
        return current_time >= close_time
