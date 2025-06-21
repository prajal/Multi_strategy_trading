# enhanced_main.py - FIXED VERSION WITH IMPROVED POSITION MANAGEMENT

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
    """Enhanced trading bot with improved position management and regime filtering"""
    
    def __init__(self, strategy_profile='balanced'):
        # Load strategy configuration
        if strategy_profile in STRATEGY_PROFILES:
            self.config = STRATEGY_PROFILES[strategy_profile]
            logger.info(f"✅ Loaded {strategy_profile} strategy profile")
        else:
            self.config = STRATEGY_PROFILES['balanced']
            logger.warning(f"⚠️ Unknown profile '{strategy_profile}', using balanced")
        
        # Store profile name
        self.strategy_profile = strategy_profile
        
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
            "tradingsymbol": None,
            "confidence": 0,
            "atr": 0
        }
        
        # Performance tracking
        self.daily_trades = []
        self.total_pnl = 0
        
        # NEW: Enhanced settings
        self.min_hold_time_hours = self.config.get('min_hold_time_hours', 2)
        self.signal_reversal_threshold = self.config.get('signal_reversal_threshold', 0.65)
        
        # Signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown_handler)
        signal.signal(signal.SIGINT, self.shutdown_handler)
        
        logger.info("🚀 Enhanced Trading Bot initialized with improved position management")
        logger.info(f"📊 Strategy: {strategy_profile}")
        logger.info(f"🎯 Min confirmations: {self.config['min_confirmations']}")
        logger.info(f"💰 Account balance: ₹{self.config['account_balance']:,.2f}")
        logger.info(f"⏰ Min hold time: {self.min_hold_time_hours} hours")
        logger.info(f"🔄 Reversal threshold: {self.signal_reversal_threshold:.1%}")
    
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
        """Enhanced trading loop with improved position management"""
        logger.info("🚀 Starting Enhanced Multi-Indicator Trading Bot")
        logger.info(f"📊 Signal Source: {signal_instrument}")
        logger.info(f"💼 Trading Instrument: {trading_instrument}")
        
        if not self.setup_connections():
            logger.error("❌ Failed to setup connections")
            return
        
        # Get instrument tokens
        signal_token = INSTRUMENTS.get(signal_instrument, {}).get('token', '256265')
        trading_token = INSTRUMENTS.get(trading_instrument, {}).get('token', '2707457')
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
                            logger.info(f"⭐ Quality: {signal_data.get('quality_score', 0):.1%}")
                            logger.info(f"✅ Confirmations: {', '.join(signal_data.get('confirmations', []))}")
                        last_signal = signal
                    
                    # Step 6: Execute trading logic using correct prices
                    if self.current_position['quantity'] == 0:
                        # No position - look for entry signals
                        if signal in ["BUY", "SELL"]:
                            self.handle_entry_signal(signal, signal_data, current_price, trading_symbol)
                    else:
                        # Have position - manage existing trade
                        self.handle_position_management(signal, signal_data, current_price, signal_df)
                    
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
        """Handle entry signals for new positions - IMPROVED VERSION"""
        try:
            # Get scaled ATR from signal data
            nifty_atr = signal_data.get('indicators', {}).get('atr', 500)
            
            # Position sizer will handle ATR scaling internally
            sizing = self.position_sizer.calculate_position_size(
                account_balance=self.config['account_balance'],
                current_price=current_price,
                atr_value=nifty_atr,
                signal_confidence=signal_data.get('confidence', 0.5),
                symbol=trading_symbol
            )
            
            # Use the properly scaled ATR from position sizer
            trading_atr = sizing['scaled_atr']
            
            # Calculate stop loss using scaled ATR
            stop_loss_price = current_price - (trading_atr * 2.5) if signal == "BUY" else current_price + (trading_atr * 2.5)
            
            # Risk assessment using NIFTYBEES parameters
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
            
            # Calculate take profit
            take_profit_price = current_price + (trading_atr * 3.0) if signal == "BUY" else current_price - (trading_atr * 3.0)
            
            # Log trade details
            logger.info(f"🟢 {signal} ENTRY SIGNAL DETECTED")
            logger.info(f"📋 Trade Details:")
            logger.info(f"   Instrument: {trading_symbol}")
            logger.info(f"   Quantity: {sizing['quantity']} shares")
            logger.info(f"   Price: ₹{current_price:.2f}")
            logger.info(f"   Trade Value: ₹{sizing['quantity'] * current_price:,.2f}")
            logger.info(f"   Margin Required: ₹{sizing['margin_required']:,.2f}")
            logger.info(f"   Confidence: {signal_data.get('confidence', 0):.1%}")
            logger.info(f"   Quality: {signal_data.get('quality_score', 0):.1%}")
            logger.info(f"   Risk: {sizing['risk_percentage']:.1f}%")
            logger.info(f"   Stop Loss: ₹{stop_loss_price:.2f}")
            logger.info(f"   Take Profit: ₹{take_profit_price:.2f}")
            logger.info(f"   Scaled ATR: ₹{trading_atr:.2f}")
            
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
                    "take_profit": take_profit_price,
                    "symbol": trading_symbol,
                    "tradingsymbol": trading_symbol,
                    "order_id": order_id,
                    "atr": trading_atr,
                    "confidence": signal_data.get('confidence', 0),
                    "quality_score": signal_data.get('quality_score', 0)
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
    
    def handle_position_management(self, signal: str, signal_data: Dict, current_price: float, df):
        """IMPROVED position management with better hold logic"""
        try:
            if self.current_position['quantity'] == 0:
                return
            
            is_long = self.current_position['quantity'] > 0
            entry_price = self.current_position['entry_price']
            entry_time = self.current_position['entry_time']
            stop_loss = self.current_position['stop_loss']
            take_profit = self.current_position['take_profit']
            
            # Calculate position age in hours
            position_age = (datetime.now() - entry_time).total_seconds() / 3600
            
            # Calculate current P&L
            if is_long:
                pnl = (current_price - entry_price) * abs(self.current_position['quantity'])
                pnl_percent = (current_price - entry_price) / entry_price * 100
            else:
                pnl = (entry_price - current_price) * abs(self.current_position['quantity'])
                pnl_percent = (entry_price - current_price) / entry_price * 100
            
            self.current_position['pnl'] = pnl
            
            should_exit = False
            exit_reason = ""
            
            # 1. Stop loss check (highest priority)
            if is_long and current_price <= stop_loss:
                should_exit = True
                exit_reason = "Stop Loss Hit"
            elif not is_long and current_price >= stop_loss:
                should_exit = True
                exit_reason = "Stop Loss Hit"
            
            # 2. Take profit check
            elif is_long and current_price >= take_profit:
                should_exit = True
                exit_reason = "Take Profit Hit"
            elif not is_long and current_price <= take_profit:
                should_exit = True
                exit_reason = "Take Profit Hit"
            
            # 3. NEW: Minimum hold time check (prevent whipsaw losses)
            elif position_age < self.min_hold_time_hours:
                # Don't exit on signal reversal too quickly
                logger.debug(f"⏰ Position age: {position_age:.1f}h < {self.min_hold_time_hours}h minimum hold time")
                pass
            
            # 4. IMPROVED: Signal reversal check with stronger confirmation
            elif position_age >= self.min_hold_time_hours:
                # Only check after minimum hold time
                
                # Require stronger opposite signal to exit
                opposite_confidence = signal_data.get('confidence', 0)
                quality_score = signal_data.get('quality_score', 0)
                
                # Calculate combined signal strength
                signal_strength = opposite_confidence * (1 + quality_score * 0.5)
                
                strong_reversal_conditions = [
                    (is_long and signal == "SELL" and signal_strength >= self.signal_reversal_threshold),
                    (not is_long and signal == "BUY" and signal_strength >= self.signal_reversal_threshold)
                ]
                
                if any(strong_reversal_conditions):
                    should_exit = True
                    exit_reason = f"Strong Signal Reversal (Confidence: {opposite_confidence:.1%}, Quality: {quality_score:.1%})"
                    logger.info(f"🔄 Strong reversal signal detected after {position_age:.1f}h hold time")
            
            # 5. Time-based exit (risk management)
            elif position_age > 48:  # Exit after 48 hours max
                should_exit = True
                exit_reason = "Maximum Hold Time Exceeded"
            
            # 6. Market close check
            elif self.executor.is_market_close_time():
                should_exit = True
                exit_reason = "Market Close Approaching"
            
            # 7. NEW: Profit protection (trail stop for profitable trades)
            elif pnl_percent > 3.0:  # If profit is > 3%
                # Implement a trailing stop
                trail_stop_distance = self.current_position['atr'] * 1.5
                if is_long:
                    trail_stop = current_price - trail_stop_distance
                    if trail_stop > self.current_position.get('trail_stop', 0):
                        self.current_position['trail_stop'] = trail_stop
                        logger.info(f"📈 Trailing stop updated to ₹{trail_stop:.2f}")
                    
                    if current_price <= self.current_position.get('trail_stop', 0):
                        should_exit = True
                        exit_reason = "Trailing Stop Hit"
                else:
                    trail_stop = current_price + trail_stop_distance
                    if trail_stop < self.current_position.get('trail_stop', float('inf')):
                        self.current_position['trail_stop'] = trail_stop
                        logger.info(f"📈 Trailing stop updated to ₹{trail_stop:.2f}")
                    
                    if current_price >= self.current_position.get('trail_stop', float('inf')):
                        should_exit = True
                        exit_reason = "Trailing Stop Hit"
            
            # Execute exit if needed
            if should_exit:
                self.execute_exit(current_price, exit_reason)
            else:
                # Log position status periodically (every 30 minutes)
                if int(position_age * 60) % 30 == 0:  # Every 30 minutes
                    logger.info(f"📊 Position Status: {abs(self.current_position['quantity'])} shares, "
                              f"P&L: ₹{pnl:.2f} ({pnl_percent:+.1f}%), Age: {position_age:.1f}h")
                
        except Exception as e:
            logger.error(f"❌ Error in position management: {e}")
    
    def execute_exit(self, current_price: float, reason: str):
        """Execute position exit with improved logging"""
        try:
            quantity = abs(self.current_position['quantity'])
            is_long = self.current_position['quantity'] > 0
            trading_symbol = self.current_position['tradingsymbol']
            entry_price = self.current_position['entry_price']
            entry_time = self.current_position['entry_time']
            position_age = (datetime.now() - entry_time).total_seconds() / 3600
            
            # Determine transaction type for exit
            transaction_type = "SELL" if is_long else "BUY"
            
            logger.info(f"🔴 POSITION EXIT: {reason}")
            logger.info(f"   Quantity: {quantity} shares")
            logger.info(f"   Entry Price: ₹{entry_price:.2f}")
            logger.info(f"   Exit Price: ₹{current_price:.2f}")
            logger.info(f"   P&L: ₹{self.current_position['pnl']:.2f}")
            logger.info(f"   Hold Time: {position_age:.1f} hours")
            logger.info(f"   Entry Confidence: {self.current_position.get('confidence', 0):.1%}")
            logger.info(f"   Entry Quality: {self.current_position.get('quality_score', 0):.1%}")
            
            # Place exit order
            order_id = self.executor.place_order(trading_symbol, transaction_type, quantity)
            
            if order_id:
                # Create trade record for analysis
                trade_record = {
                    'entry_time': entry_time,
                    'exit_time': datetime.now(),
                    'symbol': trading_symbol,
                    'direction': 'LONG' if is_long else 'SHORT',
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl': self.current_position['pnl'],
                    'pnl_percent': (self.current_position['pnl'] / (entry_price * quantity)) * 100,
                    'hold_time_hours': position_age,
                    'exit_reason': reason,
                    'confidence': self.current_position.get('confidence', 0),
                    'quality_score': self.current_position.get('quality_score', 0),
                    'strategy_profile': self.strategy_profile
                }
                
                self.daily_trades.append(trade_record)
                
                # Update P&L tracking
                self.risk_manager.update_daily_pnl(self.current_position['pnl'])
                self.total_pnl += self.current_position['pnl']
                
                # Calculate performance metrics
                winning_trades = [t for t in self.daily_trades if t['pnl'] > 0]
                win_rate = len(winning_trades) / len(self.daily_trades) * 100 if self.daily_trades else 0
                
                logger.info(f"✅ POSITION CLOSED: {reason}")
                logger.info(f"📋 Exit Order ID: {order_id}")
                logger.info(f"💰 Total P&L Today: ₹{self.total_pnl:.2f}")
                logger.info(f"📊 Today's Stats: {len(self.daily_trades)} trades, {win_rate:.1f}% win rate")
                
                # Reset position
                self.current_position = {
                    "quantity": 0,
                    "entry_price": 0,
                    "entry_time": None,
                    "stop_loss": 0,
                    "take_profit": 0,
                    "pnl": 0,
                    "symbol": None,
                    "tradingsymbol": None,
                    "confidence": 0,
                    "quality_score": 0
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
        
        # Print session summary
        if self.daily_trades:
            logger.info("📊 SESSION SUMMARY:")
            logger.info(f"   Total Trades: {len(self.daily_trades)}")
            logger.info(f"   Total P&L: ₹{self.total_pnl:.2f}")
            winning_trades = [t for t in self.daily_trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(self.daily_trades) * 100
            logger.info(f"   Win Rate: {win_rate:.1f}%")
            avg_hold_time = sum(t['hold_time_hours'] for t in self.daily_trades) / len(self.daily_trades)
            logger.info(f"   Avg Hold Time: {avg_hold_time:.1f} hours")
        
        sys.exit(0)

def main():
    """Main function to run the enhanced trading bot"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Multi-Indicator Trading Bot with Improved Position Management')
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