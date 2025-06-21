# backtesting/backtest_engine.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Trade:
    """Single trade record"""
    entry_time: datetime
    exit_time: datetime
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    pnl_percent: float
    stop_loss: float
    take_profit: float
    exit_reason: str
    confidence: float
    atr: float
    duration_minutes: int

@dataclass
class BacktestResults:
    """Backtest results summary"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    max_drawdown: float
    max_drawdown_percent: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    avg_trade_duration: float
    trades: List[Trade]

class BacktestEngine:
    """Enhanced backtesting engine for multi-indicator strategy"""
    
    def __init__(self, strategy, position_sizer, risk_manager, config):
        self.strategy = strategy
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.config = config
        
        # Backtest state
        self.current_capital = config.get('account_balance', 10000)
        self.initial_capital = self.current_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        
        logger.info("🎯 Backtest engine initialized")
        logger.info(f"   Initial capital: ₹{self.initial_capital:,.2f}")
        logger.info(f"   Strategy: {config.get('profile', 'unknown')}")
    
    def run_backtest(self, data: pd.DataFrame, start_date: str = None, end_date: str = None) -> BacktestResults:
        """Run complete backtest on historical data"""
        
        logger.info("🚀 Starting backtest...")
        
        # Filter data by date range if provided
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 50:
            raise ValueError(f"Insufficient data: {len(data)} rows. Need at least 50.")
        
        logger.info(f"📊 Backtesting period: {data.index[0]} to {data.index[-1]}")
        logger.info(f"📈 Data points: {len(data)} candles")
        
        # Reset state
        self.current_capital = self.initial_capital
        self.positions = []
        self.trades = []
        self.equity_curve = []
        self.daily_returns = []
        
        # Main backtest loop
        for i in range(50, len(data)):  # Start after warmup period
            current_time = data.index[i]
            current_data = data.iloc[:i+1]  # Data up to current point
            current_price = data.iloc[i]['close']
            
            # Record equity curve
            portfolio_value = self.calculate_portfolio_value(current_price)
            self.equity_curve.append({
                'timestamp': current_time,
                'portfolio_value': portfolio_value,
                'cash': self.current_capital,
                'unrealized_pnl': self.calculate_unrealized_pnl(current_price)
            })
            
            # Check for exit conditions first
            self.check_exit_conditions(current_time, current_price, current_data)
            
            # Generate trading signal
            if len(self.positions) == 0:  # Only enter new positions if no current position
                signal, signal_data = self.strategy.get_signal(current_data)
                
                if signal in ['BUY', 'SELL']:
                    self.process_entry_signal(signal, signal_data, current_time, current_price)
            
            # Log progress periodically
            if i % 1000 == 0:
                logger.info(f"📊 Progress: {i}/{len(data)} ({i/len(data)*100:.1f}%)")
        
        # Close any remaining positions
        if self.positions:
            final_price = data.iloc[-1]['close']
            final_time = data.index[-1]
            self.close_position(final_time, final_price, "End of backtest")
        
        # Calculate results
        results = self.calculate_results(data.index[0], data.index[-1])
        
        logger.info("✅ Backtest completed")
        logger.info(f"📊 Total trades: {results.total_trades}")
        logger.info(f"🎯 Win rate: {results.win_rate:.1%}")
        logger.info(f"💰 Total return: {results.total_return_percent:.1%}")
        logger.info(f"📉 Max drawdown: {results.max_drawdown_percent:.1%}")
        
        return results
    
    def process_entry_signal(self, signal: str, signal_data: Dict, timestamp: datetime, price: float):
        """Process entry signal and create position"""
        
        # Calculate position size
        atr_value = signal_data.get('indicators', {}).get('atr', price * 0.02)
        confidence = signal_data.get('confidence', 0.5)
        
        sizing = self.position_sizer.calculate_position_size(
            account_balance=self.current_capital,
            current_price=price,
            atr_value=atr_value,
            signal_confidence=confidence
        )
        
        # Risk assessment
        stop_loss_price = price - (atr_value * 2) if signal == 'BUY' else price + (atr_value * 2)
        
        risk_assessment = self.risk_manager.assess_trade_risk(
            entry_price=price,
            quantity=sizing['quantity'],
            stop_loss=stop_loss_price,
            account_balance=self.current_capital
        )
        
        # Skip trade if risk is too high
        if risk_assessment['recommendation'] == 'REJECT':
            return
        
        # Adjust quantity if needed
        quantity = sizing['quantity']
        if risk_assessment['recommendation'] == 'REDUCE_SIZE':
            quantity = risk_assessment['suggested_quantity']
        
        # Calculate margin required
        leverage = sizing.get('leverage_used', 5.0)
        margin_required = quantity * price / leverage
        
        # Check if we have enough capital
        if margin_required > self.current_capital * 0.9:  # Keep 10% buffer
            return
        
        # Create position
        position = {
            'entry_time': timestamp,
            'direction': signal,
            'entry_price': price,
            'quantity': quantity if signal == 'BUY' else -quantity,
            'stop_loss': stop_loss_price,
            'take_profit': price + (atr_value * 4) if signal == 'BUY' else price - (atr_value * 4),
            'confidence': confidence,
            'atr': atr_value,
            'margin_used': margin_required
        }
        
        self.positions.append(position)
        self.current_capital -= margin_required
        
        logger.debug(f"📈 {signal} position opened at ₹{price:.2f}, quantity: {abs(quantity)}")
    
    def check_exit_conditions(self, timestamp: datetime, price: float, data: pd.DataFrame):
        """Check and process exit conditions"""
        
        if not self.positions:
            return
        
        position = self.positions[0]  # Assuming single position for now
        is_long = position['quantity'] > 0
        
        should_exit = False
        exit_reason = ""
        
        # Stop loss check
        if is_long and price <= position['stop_loss']:
            should_exit = True
            exit_reason = "Stop Loss"
        elif not is_long and price >= position['stop_loss']:
            should_exit = True
            exit_reason = "Stop Loss"
        
        # Take profit check
        elif is_long and price >= position['take_profit']:
            should_exit = True
            exit_reason = "Take Profit"
        elif not is_long and price <= position['take_profit']:
            should_exit = True
            exit_reason = "Take Profit"
        
        # Signal reversal check
        elif len(data) > 50:  # Ensure enough data for signal
            signal, _ = self.strategy.get_signal(data)
            if (is_long and signal == 'SELL') or (not is_long and signal == 'BUY'):
                should_exit = True
                exit_reason = "Signal Reversal"
        
        # Time-based exit (optional - for testing)
        elif (timestamp - position['entry_time']).total_seconds() > 4 * 3600:  # 4 hours max
            should_exit = True
            exit_reason = "Time Limit"
        
        if should_exit:
            self.close_position(timestamp, price, exit_reason)
    
    def close_position(self, timestamp: datetime, price: float, reason: str):
        """Close current position and record trade"""
        
        if not self.positions:
            return
        
        position = self.positions.pop(0)
        
        # Calculate P&L
        quantity = abs(position['quantity'])
        if position['quantity'] > 0:  # Long position
            pnl = (price - position['entry_price']) * quantity
        else:  # Short position
            pnl = (position['entry_price'] - price) * quantity
        
        pnl_percent = pnl / (position['entry_price'] * quantity) * 100
        
        # Return margin to capital
        self.current_capital += position['margin_used'] + pnl
        
        # Create trade record
        trade = Trade(
            entry_time=position['entry_time'],
            exit_time=timestamp,
            direction=position['direction'],
            entry_price=position['entry_price'],
            exit_price=price,
            quantity=quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            stop_loss=position['stop_loss'],
            take_profit=position['take_profit'],
            exit_reason=reason,
            confidence=position['confidence'],
            atr=position['atr'],
            duration_minutes=int((timestamp - position['entry_time']).total_seconds() / 60)
        )
        
        self.trades.append(trade)
        
        logger.debug(f"📉 Position closed: {reason}, P&L: ₹{pnl:.2f}")
    
    def calculate_portfolio_value(self, current_price: float) -> float:
        """Calculate current portfolio value"""
        portfolio_value = self.current_capital
        
        if self.positions:
            position = self.positions[0]
            unrealized_pnl = self.calculate_unrealized_pnl(current_price)
            portfolio_value += unrealized_pnl
        
        return portfolio_value
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L for open positions"""
        if not self.positions:
            return 0
        
        position = self.positions[0]
        quantity = abs(position['quantity'])
        
        if position['quantity'] > 0:  # Long
            return (current_price - position['entry_price']) * quantity
        else:  # Short
            return (position['entry_price'] - current_price) * quantity
    
    def calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResults:
        """Calculate comprehensive backtest results"""
        
        if not self.trades:
            logger.warning("No trades executed during backtest")
            return BacktestResults(
                start_date=start_date,
                end_date=end_date,
                initial_capital=self.initial_capital,
                final_capital=self.current_capital,
                total_return=0,
                total_return_percent=0,
                max_drawdown=0,
                max_drawdown_percent=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                avg_win=0,
                avg_loss=0,
                profit_factor=0,
                sharpe_ratio=0,
                max_consecutive_wins=0,
                max_consecutive_losses=0,
                avg_trade_duration=0,
                trades=[]
            )
        
        # Basic metrics
        total_return = self.current_capital - self.initial_capital
        total_return_percent = total_return / self.initial_capital * 100
        
        # Trade analysis
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) * 100
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else float('inf')
        
        # Drawdown calculation
        equity_values = [e['portfolio_value'] for e in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        max_drawdown_percent = max_drawdown / peak * 100 if peak > 0 else 0
        
        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for trade in self.trades:
            if trade.pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        # Sharpe ratio (simplified)
        if len(self.trades) > 1:
            returns = [t.pnl_percent for t in self.trades]
            sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Average trade duration
        avg_duration = np.mean([t.duration_minutes for t in self.trades])
        
        return BacktestResults(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=self.current_capital,
            total_return=total_return,
            total_return_percent=total_return_percent,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            avg_trade_duration=avg_duration,
            trades=self.trades
        )
    
    def save_results(self, results: BacktestResults, filename: str):
        """Save backtest results to file"""
        
        # Convert results to dictionary
        results_dict = {
            'summary': {
                'start_date': results.start_date.isoformat(),
                'end_date': results.end_date.isoformat(),
                'initial_capital': results.initial_capital,
                'final_capital': results.final_capital,
                'total_return': results.total_return,
                'total_return_percent': results.total_return_percent,
                'max_drawdown': results.max_drawdown,
                'max_drawdown_percent': results.max_drawdown_percent,
                'total_trades': results.total_trades,
                'winning_trades': results.winning_trades,
                'losing_trades': results.losing_trades,
                'win_rate': results.win_rate,
                'avg_win': results.avg_win,
                'avg_loss': results.avg_loss,
                'profit_factor': results.profit_factor,
                'sharpe_ratio': results.sharpe_ratio,
                'max_consecutive_wins': results.max_consecutive_wins,
                'max_consecutive_losses': results.max_consecutive_losses,
                'avg_trade_duration': results.avg_trade_duration
            },
            'trades': [
                {
                    'entry_time': trade.entry_time.isoformat(),
                    'exit_time': trade.exit_time.isoformat(),
                    'direction': trade.direction,
                    'entry_price': trade.entry_price,
                    'exit_price': trade.exit_price,
                    'quantity': trade.quantity,
                    'pnl': trade.pnl,
                    'pnl_percent': trade.pnl_percent,
                    'exit_reason': trade.exit_reason,
                    'confidence': trade.confidence,
                    'duration_minutes': trade.duration_minutes
                }
                for trade in results.trades
            ],
            'equity_curve': self.equity_curve
        }
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)
        
        logger.info(f"💾 Results saved to {filename}")
    
    def generate_report(self, results: BacktestResults) -> str:
        """Generate detailed backtest report"""
        
        report = f"""
🎯 ENHANCED TRADING BOT BACKTEST REPORT
{'='*50}

📊 PERFORMANCE SUMMARY
{'='*25}
Period: {results.start_date.strftime('%Y-%m-%d')} to {results.end_date.strftime('%Y-%m-%d')}
Initial Capital: ₹{results.initial_capital:,.2f}
Final Capital: ₹{results.final_capital:,.2f}
Total Return: ₹{results.total_return:,.2f} ({results.total_return_percent:+.1f}%)
Max Drawdown: ₹{results.max_drawdown:,.2f} ({results.max_drawdown_percent:.1f}%)

📈 TRADING STATISTICS
{'='*25}
Total Trades: {results.total_trades}
Winning Trades: {results.winning_trades} ({results.win_rate:.1f}%)
Losing Trades: {results.losing_trades} ({100-results.win_rate:.1f}%)
Average Win: ₹{results.avg_win:.2f}
Average Loss: ₹{results.avg_loss:.2f}
Profit Factor: {results.profit_factor:.2f}
Sharpe Ratio: {results.sharpe_ratio:.2f}

🔥 STREAKS
{'='*25}
Max Consecutive Wins: {results.max_consecutive_wins}
Max Consecutive Losses: {results.max_consecutive_losses}
Average Trade Duration: {results.avg_trade_duration:.0f} minutes

📋 TRADE BREAKDOWN
{'='*25}"""

        if results.trades:
            report += f"\nFirst 10 Trades:\n"
            for i, trade in enumerate(results.trades[:10]):
                pnl_color = "🟢" if trade.pnl > 0 else "🔴"
                report += f"{i+1:2d}. {pnl_color} {trade.direction} ₹{trade.entry_price:.2f}→₹{trade.exit_price:.2f} "
                report += f"P&L: ₹{trade.pnl:+.2f} ({trade.pnl_percent:+.1f}%) [{trade.exit_reason}]\n"
        
        return report
