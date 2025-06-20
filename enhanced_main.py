# enhanced_main.py - FIXED VERSION WITH PROPER INSTRUMENT HANDLING

import time
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Import existing components
from auth.kite_auth import KiteAuth
from trading.executor import OrderExecutor
from utils.logger import get_logger

# Import new enhanced components
from trading.enhanced_strategy import EnhancedTradingStrategy
from trading.position_sizer import EnhancedPositionSizer
from trading.risk_manager import EnhancedRiskManager
from config.enhanced_settings import STRATEGY_PROFILES, MARKET_CONFIG, INSTRUMENTS

logger = get_logger(__name__)

class EnhancedTradingBot:
    """Enhanced trading bot with multi-indicator strategy and professional risk management"""
    
    def __init__(self, strategy_profile='balanced'):
        # Load strategy configuration
        if strategy_profile in STRATEGY_PROFILES:
            self.config = STRATEGY_PROFILES[strategy_profile]
            logger.info(f"✅ Loaded {strategy_profile} strategy profile")
        else:
            self.config = STRATEGY_PROFILES['balanced']
            logger.warning(f"⚠️ Unknown profile '{strategy_profile}', using balanced")
        
        # Initialize trading components
        self.auth = KiteAuth()
        self.kite = None
        self.executor = None
        
        # Initialize enhanced components
        self.strategy = EnhancedTradingStrategy(self.config)
        self.position_sizer = EnhancedPositionSizer(self.config)
        self.risk_manager = EnhancedRiskManager(self.config)
        
        # Trading state
        self.is_running = False
        self.current_position = {
            "quantity": 0,
            "entry_price": 0,
            "entry_time": None,
            "stop_loss": 0,
            "take_profit": 0,
            "pnl": 0,
            "symbol": None,
            "tradingsymbol": None
        }
        
        # Performance tracking
        self.daily_trades = []
        self.total_pnl = 0
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
        logger.info("🚀 Enhanced Trading Bot initialized")
        logger.info(f"📊 Strategy: {strategy_profile}")
        logger.info(f"🎯 Min confirmations: {self.config['min_confirmations']}")
        logger.info(f"💰 Account balance: ₹{self.config['account_balance']:,.2f}")
    
    def setup_connections(self) -> bool:
        """Setup Kite connection and executor"""
        try:
            self.kite = self.auth.get_kite_instance()
            if not self.kite:
                logger.error("❌ Failed to get Kite instance")
                return False
            
            self.executor = OrderExecutor(self.kite)
            logger.info("✅ Trading connections established")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection setup failed: {e}")
            return False
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        
        # Check if it's a trading day (Monday to Friday)
        if now.weekday() not in MARKET_CONFIG['trading_days']:
            return False
        
        current_time = now.time()
        market_open = datetime.strptime(MARKET_CONFIG['market_open_time'], "%H:%M").time()
        market_close = datetime.strptime(MARKET_CONFIG['market_close_time'], "%H:%M").time()
        
        return market_open <= current_time <= market_close
    
    def run_enhanced_trading(self, signal_instrument='NIFTY_50', trading_instrument='NIFTYBEES'):
        """COMPLETE enhanced trading loop with FIXED instrument handling"""
        logger.info("🚀 Starting Enhanced Multi-Indicator Trading Bot")
        logger.info(f"📊 Signal Source: {signal_instrument}")
        logger.info(f"💼 Trading Instrument: {trading_instrument}")
        
        if not self.setup_connections():
            logger.error("❌ Failed to setup connections")
            return
        
        # Get instrument tokens - FIXED
        signal_token = INSTRUMENTS.get(signal_instrument, {}).get('token', '256265')
        trading_token = INSTRUMENTS.get(trading_instrument, {}).get('token', '2707457')  # NIFTYBEES token
        trading_symbol = INSTRUMENTS.get(trading_instrument, {}).get('symbol', 'NIFTYBEES')
        
        logger.info(f"🔍 Signal Token: {signal_token} ({signal_instrument})")
        logger.info(f"💼 Trading Token: {trading_token} ({trading_symbol})")
        
        logger.info("✅ Enhanced trading bot is now running (LIVE MODE)...")
        logger.info("🛑 Press Ctrl+C to stop")
        
        self.is_running = True
        last_signal = "HOLD"
        
        try:
            while self.is_running:
                # Check if market is open
                if not self.is_market_open():
                    logger.info("📅 Market is closed, waiting...")
                    time.sleep(60)  # Check every minute when market closed
                    continue
                
                # Check risk management - stop trading if limits hit
                should_stop, reason = self.risk_manager.should_stop_trading()
                if should_stop:
                    logger.warning(f"🛑 Trading stopped: {reason}")
                    break
                
                try:
                    # Step 1: Get historical data for SIGNAL analysis (NIFTY 50)
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=2)
                    
                    signal_df = self.executor.get_historical_data(signal_token, start_date, end_date)
                    
                    if signal_df.empty:
                        logger.warning("⚠️ No signal data received, retrying...")
                        time.sleep(self.config['check_interval'])
                        continue
                    
                    # Step 2: Get current TRADING instrument price (NIFTYBEES)
                    trading_price = self.executor.get_latest_price(f"NSE:{trading_token}")
                    
                    if not trading_price:
                        # Fallback: get from historical data
                        trading_df = self.executor.get_historical_data(trading_token, start_date, end_date)
                        if not trading_df.empty:
                            trading_price = trading_df['close'].iloc[-1]
                        else:
                            logger.warning("⚠️ Could not get trading price, retrying...")
                            time.sleep(self.config['check_interval'])
                            continue
                    
                    # Step 3: Generate trading signal using NIFTY 50 data
                    signal, signal_data = self.strategy.get_signal(signal_df)
                    
                    # Step 4: Use NIFTYBEES price for actual trading calculations
                    current_price = trading_price
                    
                    # Step 5: Log current market status
                    if signal != last_signal:
                        logger.info(f"📊 Signal Change: {last_signal} → {signal}")
                        logger.info(f"📈 NIFTY 50: ₹{signal_df['close'].iloc[-1]:.2f}")
                        logger.info(f"💰 NIFTYBEES: ₹{current_price:.2f}")
                        if signal != "HOLD":
                            logger.info(f"🎯 Confidence: {signal_data.get('confidence', 0):.1%}")
                            logger.info(f"✅ Confirmations: {', '.join(signal_data.get('confirmations', []))}")
                        last_signal = signal
                    
                    # Step 6: Execute trading logic using correct prices
                    if self.current_position['quantity'] == 0:
                        # No position - look for entry signals
                        if signal in ["BUY", "SELL"]:
                            self.handle_entry_signal(signal, signal_data, current_price, trading_symbol)
                    else:
                        # Have position - manage existing trade
                        self.handle_position_management(signal, current_price, signal_df)
                    
                except Exception as e:
                    logger.error(f"❌ Error in trading loop: {e}")
                    import traceback
                    traceback.print_exc()
                
                # Wait before next check
                time.sleep(self.config['check_interval'])
                
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Fatal error in main trading loop: {e}")
        finally:
            logger.info("📅 Enhanced trading session ended")
            self.is_running = False
    
    def handle_entry_signal(self, signal: str, signal_data: Dict, current_price: float, trading_symbol: str):
        """Handle entry signals for new positions - FIXED pricing"""
        try:
            # Get ATR from signal data (calculated from NIFTY 50)
            nifty_atr = signal_data.get('indicators', {}).get('atr', 500)  # NIFTY ATR
            
            # Convert NIFTY ATR to NIFTYBEES ATR (approximate ratio)
            # NIFTYBEES ≈ NIFTY/100, so ATR ratio is similar
            trading_atr = nifty_atr / 100  # Approximate conversion
            
            # Ensure minimum ATR for NIFTYBEES
            trading_atr = max(trading_atr, current_price * 0.015)  # Minimum 1.5% of price
            
            logger.info(f"📊 ATR Analysis: NIFTY ATR: ₹{nifty_atr:.2f} → NIFTYBEES ATR: ₹{trading_atr:.2f}")
            
            # Calculate position size using NIFTYBEES price and ATR
            sizing = self.position_sizer.calculate_position_size(
                account_balance=self.config['account_balance'],
                current_price=current_price,  # NIFTYBEES price
                atr_value=trading_atr,        # NIFTYBEES ATR
                signal_confidence=signal_data.get('confidence', 0.5),
                symbol=trading_symbol
            )
            
            # Ensure minimum quantity
            if sizing['quantity'] < 1:
                logger.warning("📉 Calculated quantity too small, setting minimum to 1 share")
                sizing['quantity'] = 1
                sizing['margin_required'] = current_price / 5  # 5x leverage
                sizing['trade_value'] = current_price
                sizing['risk_percentage'] = (trading_atr * 2) / self.config['account_balance'] * 100
            
            # Risk assessment using NIFTYBEES parameters
            stop_loss_price = current_price - (trading_atr * 2) if signal == "BUY" else current_price + (trading_atr * 2)
            
            risk_assessment = self.risk_manager.assess_trade_risk(
                entry_price=current_price,
                quantity=sizing['quantity'],
                stop_loss=stop_loss_price,
                account_balance=self.config['account_balance']
            )
            
            # Check if trade is acceptable
            if risk_assessment['recommendation'] in ['REJECT']:
                logger.warning(f"🚫 Trade rejected: {', '.join(risk_assessment['warnings'])}")
                return
            
            # Adjust quantity if needed
            if risk_assessment['recommendation'] == 'REDUCE_SIZE':
                sizing['quantity'] = max(1, risk_assessment['suggested_quantity'])
                logger.info(f"📉 Position size reduced to {sizing['quantity']} shares")
            
            # Log trade details
            logger.info(f"🟢 {signal} ENTRY SIGNAL DETECTED")
            logger.info(f"📋 Trade Details:")
            logger.info(f"   Instrument: {trading_symbol}")
            logger.info(f"   Quantity: {sizing['quantity']} shares")
            logger.info(f"   Price: ₹{current_price:.2f}")
            logger.info(f"   Trade Value: ₹{sizing['quantity'] * current_price:,.2f}")
            logger.info(f"   Margin Required: ₹{sizing['margin_required']:,.2f}")
            logger.info(f"   Confidence: {signal_data.get('confidence', 0):.1%}")
            logger.info(f"   Risk: {sizing['risk_percentage']:.1f}%")
            logger.info(f"   Stop Loss: ₹{stop_loss_price:.2f}")
            logger.info(f"   ATR: ₹{trading_atr:.2f}")
            
            # Place order
            transaction_type = "BUY" if signal == "BUY" else "SELL"
            order_id = self.executor.place_order(trading_symbol, transaction_type, sizing['quantity'])
            
            if order_id:
                # Update position tracking
                self.current_position.update({
                    "quantity": sizing['quantity'] if signal == "BUY" else -sizing['quantity'],
                    "entry_price": current_price,
                    "entry_time": datetime.now(),
                    "stop_loss": stop_loss_price,
                    "take_profit": current_price + (trading_atr * 4) if signal == "BUY" else current_price - (trading_atr * 4),
                    "symbol": trading_symbol,
                    "tradingsymbol": trading_symbol,
                    "order_id": order_id,
                    "atr": trading_atr
                })
                
                # Update risk management
                self.risk_manager.increment_trade_count()
                
                logger.info(f"✅ POSITION OPENED: {sizing['quantity']} {trading_symbol} at ₹{current_price:.2f}")
                logger.info(f"📋 Order ID: {order_id}")
            else:
                logger.error("❌ Order placement failed")
                
        except Exception as e:
            logger.error(f"❌ Error handling entry signal: {e}")
            import traceback
            traceback.print_exc()
    
    def handle_position_management(self, signal: str, current_price: float, df):
        """Manage existing positions"""
        try:
            if self.current_position['quantity'] == 0:
                return
            
            is_long = self.current_position['quantity'] > 0
            entry_price = self.current_position['entry_price']
            stop_loss = self.current_position['stop_loss']
            take_profit = self.current_position['take_profit']
            
            # Calculate current P&L
            if is_long:
                pnl = (current_price - entry_price) * abs(self.current_position['quantity'])
            else:
                pnl = (entry_price - current_price) * abs(self.current_position['quantity'])
            
            self.current_position['pnl'] = pnl
            
            # Check exit conditions
            should_exit = False
            exit_reason = ""
            
            # Stop loss check
            if is_long and current_price <= stop_loss:
                should_exit = True
                exit_reason = "Stop Loss Hit"
            elif not is_long and current_price >= stop_loss:
                should_exit = True
                exit_reason = "Stop Loss Hit"
            
            # Take profit check
            elif is_long and current_price >= take_profit:
                should_exit = True
                exit_reason = "Take Profit Hit"
            elif not is_long and current_price <= take_profit:
                should_exit = True
                exit_reason = "Take Profit Hit"
            
            # Signal reversal check
            elif (is_long and signal == "SELL") or (not is_long and signal == "BUY"):
                should_exit = True
                exit_reason = "Signal Reversal"
            
            # Market close check
            elif self.executor.is_market_close_time():
                should_exit = True
                exit_reason = "Market Close Approaching"
            
            # Execute exit if needed
            if should_exit:
                self.execute_exit(current_price, exit_reason)
            else:
                # Log position status periodically
                if datetime.now().second % 60 == 0:  # Every minute
                    logger.info(f"📊 Position: {abs(self.current_position['quantity'])} shares, P&L: ₹{pnl:.2f}")
                
        except Exception as e:
            logger.error(f"❌ Error in position management: {e}")
    
    def execute_exit(self, current_price: float, reason: str):
        """Execute position exit"""
        try:
            quantity = abs(self.current_position['quantity'])
            is_long = self.current_position['quantity'] > 0
            trading_symbol = self.current_position['tradingsymbol']
            
            # Determine transaction type for exit
            transaction_type = "SELL" if is_long else "BUY"
            
            logger.info(f"🔴 POSITION EXIT: {reason}")
            logger.info(f"   Quantity: {quantity} shares")
            logger.info(f"   Exit Price: ₹{current_price:.2f}")
            logger.info(f"   P&L: ₹{self.current_position['pnl']:.2f}")
            
            # Place exit order
            order_id = self.executor.place_order(trading_symbol, transaction_type, quantity)
            
            if order_id:
                # Update P&L tracking
                self.risk_manager.update_daily_pnl(self.current_position['pnl'])
                self.total_pnl += self.current_position['pnl']
                
                logger.info(f"✅ POSITION CLOSED: {reason}")
                logger.info(f"📋 Exit Order ID: {order_id}")
                logger.info(f"💰 Total P&L Today: ₹{self.total_pnl:.2f}")
                
                # Reset position
                self.current_position = {
                    "quantity": 0,
                    "entry_price": 0,
                    "entry_time": None,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "pnl": 0,
                    "symbol": None,
                    "tradingsymbol": None
                }
                
            else:
                logger.error("❌ Exit order placement failed")
                
        except Exception as e:
            logger.error(f"❌ Error executing exit: {e}")
    
    def shutdown_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("🛑 Shutdown signal received")
        self.is_running = False
        
        # Close any open positions if needed
        if self.current_position['quantity'] != 0:
            logger.info("🔄 Closing open position before shutdown...")
            try:
                trading_token = INSTRUMENTS['NIFTYBEES']['token']
                current_price = self.executor.get_latest_price(f"NSE:{trading_token}")
                if current_price:
                    self.execute_exit(current_price, "System Shutdown")
            except Exception as e:
                logger.error(f"Error closing position on shutdown: {e}")
        
        sys.exit(0)

def main():
    """Main function to run the enhanced trading bot"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Multi-Indicator Trading Bot')
    parser.add_argument('--profile', choices=['conservative', 'balanced', 'aggressive', 'scalping'], 
                       default='balanced', help='Strategy profile to use')
    parser.add_argument('--signal', choices=['NIFTY_50'], default='NIFTY_50', 
                       help='Signal source instrument')
    parser.add_argument('--trading', choices=['NIFTYBEES', 'JUNIORBEES', 'BANKBEES'], 
                       default='NIFTYBEES', help='Trading instrument')
    
    args = parser.parse_args()
    
    # Create and run bot
    bot = EnhancedTradingBot(strategy_profile=args.profile)
    bot.run_enhanced_trading(signal_instrument=args.signal, trading_instrument=args.trading)

if __name__ == "__main__":
    main()