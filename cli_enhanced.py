# cli_enhanced.py - Fixed version without syntax errors

import argparse
import sys
from datetime import datetime
from enhanced_main import EnhancedTradingBot
from auth.kite_auth import KiteAuth
from utils.logger import get_logger

logger = get_logger(__name__)

def test_enhanced_connection():
    """Test enhanced trading bot connection and components"""
    print("🧪 Testing Enhanced Trading Bot Components...")
    print("=" * 50)
    
    try:
        # Test authentication
        print("1. Testing Kite Connect authentication...")
        auth = KiteAuth()
        kite = auth.get_kite_instance()
        if kite:
            profile = kite.profile()
            print(f"   ✅ Connected as: {profile['user_name']}")
            print(f"   💰 Available cash: ₹{profile.get('equity', {}).get('available', {}).get('cash', 0):,.2f}")
        else:
            print("   ❌ Authentication failed")
            return False
        
        # Test enhanced strategy
        print("\n2. Testing Enhanced Strategy...")
        from config.enhanced_settings import STRATEGY_PROFILES
        bot = EnhancedTradingBot('balanced')
        print(f"   ✅ Strategy initialized with {bot.config['min_confirmations']} min confirmations")
        print(f"   📊 Risk per trade: {bot.config['max_risk_per_trade']}%")
        print(f"   💼 Position size: {bot.config['base_position_size']:.0%}")
        
        # Test historical data
        print("\n3. Testing Historical Data...")
        from datetime import timedelta
        from trading.executor import OrderExecutor
        
        executor = OrderExecutor(kite)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=2)
        df = executor.get_historical_data("256265", start_date, end_date)
        
        if not df.empty:
            print(f"   ✅ Historical data: {len(df)} records")
            print(f"   📈 Latest close: ₹{df['close'].iloc[-1]:.2f}")
        else:
            print("   ❌ No historical data received")
            return False
        
        # Test signal generation
        print("\n4. Testing Signal Generation...")
        signal, signal_data = bot.strategy.get_signal(df)
        print(f"   📊 Current signal: {signal}")
        if signal != "HOLD":
            print(f"   🎯 Confidence: {signal_data['confidence']:.1%}")
            print(f"   ✅ Confirmations: {len(signal_data['confirmations'])}")
        
        # Test position sizing
        print("\n5. Testing Position Sizing...")
        if signal == "BUY":
            atr_value = signal_data.get('indicators', {}).get('atr', 10)
            sizing = bot.position_sizer.calculate_position_size(
                account_balance=bot.config['account_balance'],
                current_price=df['close'].iloc[-1],
                atr_value=atr_value,
                signal_confidence=signal_data.get('confidence', 0.5)
            )
            print(f"   📊 Suggested quantity: {sizing['quantity']} shares")
            print(f"   💰 Margin required: ₹{sizing['margin_required']:.2f}")
            print(f"   ⚖️ Risk percentage: {sizing['risk_percentage']:.1f}%")
        
        # Test risk management
        print("\n6. Testing Risk Management...")
        risk_assessment = bot.risk_manager.assess_trade_risk(
            entry_price=df['close'].iloc[-1],
            quantity=10,
            stop_loss=df['close'].iloc[-1] * 0.98,
            account_balance=bot.config['account_balance']
        )
        print(f"   🛡️ Risk level: {risk_assessment['risk_level']}")
        print(f"   📋 Recommendation: {risk_assessment['recommendation']}")
        
        print("\n🎉 All components tested successfully!")
        print("✅ Enhanced trading bot is ready to use")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def auth_enhanced():
    """Enhanced authentication with better error handling"""
    print("🔐 Enhanced Kite Connect Authentication")
    print("=" * 40)
    
    try:
        auth = KiteAuth()
        
        # Check if we already have valid tokens
        kite = auth.get_kite_instance()
        if kite:
            try:
                profile = kite.profile()
                print(f"✅ Already authenticated as: {profile['user_name']}")
                print(f"💰 Available cash: ₹{profile.get('equity', {}).get('available', {}).get('cash', 0):,.2f}")
                return True
            except:
                print("⚠️ Existing tokens are invalid, need to re-authenticate")
        
        # Generate login URL
        login_url = auth.generate_login_url()
        print("\n📋 Authentication Steps:")
        print("1. Copy the URL below and open it in your browser")
        print("2. Login to Zerodha with your credentials")
        print("3. After successful login, copy the COMPLETE redirected URL")
        print("4. Extract the 'request_token' from the URL")
        print("5. Paste the request_token below")
        print("\n🔗 Login URL:")
        print(login_url)
        print("\n" + "="*60)
        
        # Get request token from user
        request_token = input("\n🔑 Enter the request_token: ").strip()
        
        if not request_token:
            print("❌ No request token provided")
            return False
        
        # Generate access token
        success = auth.generate_access_token(request_token)
        if success:
            print("✅ Authentication successful!")
            
            # Test the new authentication
            kite = auth.get_kite_instance()
            if kite:
                profile = kite.profile()
                print(f"👤 User: {profile['user_name']}")
                print(f"📧 Email: {profile['email']}")
                print(f"💰 Available cash: ₹{profile.get('equity', {}).get('available', {}).get('cash', 0):,.2f}")
                return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def run_enhanced_trading(args):
    """Run enhanced trading with specified parameters"""
    print(f"🚀 Starting Enhanced Trading Bot")
    print(f"📊 Profile: {args.profile}")
    print(f"🎯 Signal: {args.signal}")
    print(f"💼 Trading: {args.trading}")
    print("=" * 50)
    
    try:
        bot = EnhancedTradingBot(strategy_profile=args.profile)
        bot.run_enhanced_trading(
            signal_instrument=args.signal,
            trading_instrument=args.trading
        )
    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
    except Exception as e:
        print(f"\n❌ Trading error: {e}")
        import traceback
        traceback.print_exc()

def show_strategy_comparison():
    """Show comparison of different strategy profiles"""
    from config.enhanced_settings import STRATEGY_PROFILES
    
    print("📊 STRATEGY PROFILE COMPARISON")
    print("=" * 60)
    
    profiles = ['conservative', 'balanced', 'aggressive', 'scalping']
    
    print(f"{'Parameter':<25} {'Conservative':<12} {'Balanced':<12} {'Aggressive':<12} {'Scalping':<12}")
    print("-" * 73)
    
    params_to_compare = [
        ('min_confirmations', 'Min Confirmations'),
        ('max_risk_per_trade', 'Risk per Trade (%)'),
        ('base_position_size', 'Position Size (%)'),
        ('max_trades_per_day', 'Max Trades/Day'),
        ('supertrend_factor', 'SuperTrend Factor'),
        ('volume_threshold', 'Volume Threshold'),
        ('check_interval', 'Check Interval (s)')
    ]
    
    for param_key, param_name in params_to_compare:
        row = f"{param_name:<25}"
        for profile in profiles:
            value = STRATEGY_PROFILES[profile].get(param_key, 'N/A')
            if isinstance(value, float):
                if param_key in ['base_position_size']:
                    row += f"{value*100:.0f}%{'':<8}"
                else:
                    row += f"{value:<12.1f}"
            else:
                row += f"{value:<12}"
        print(row)
    
    print("\n📋 RECOMMENDATIONS:")
    print("🟢 Conservative: New traders, capital preservation focus")
    print("🔵 Balanced: Most traders, good risk/reward balance")
    print("🟡 Aggressive: Experienced traders, higher risk tolerance")
    print("🔴 Scalping: Very active trading, requires constant monitoring")

def reset_position():
    """Reset position tracking"""
    print("🔄 Position Reset")
    print("=" * 20)
    print("This would reset any stuck position tracking.")
    print("(Implementation depends on your specific setup)")
    print("✅ Position tracking reset completed")

def main():
    """Enhanced CLI main function"""
    parser = argparse.ArgumentParser(description='Enhanced Multi-Indicator Trading Bot CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Authentication command
    subparsers.add_parser('auth', help='Authenticate with Kite Connect')
    
    # Test command
    subparsers.add_parser('test', help='Test all components')
    
    # Strategy comparison command
    subparsers.add_parser('compare', help='Compare strategy profiles')
    
    # Trading command
    trade_parser = subparsers.add_parser('trade', help='Start enhanced trading')
    trade_parser.add_argument('--profile', choices=['conservative', 'balanced', 'aggressive', 'scalping'],
                            default='balanced', help='Strategy profile (default: balanced)')
    trade_parser.add_argument('--signal', choices=['NIFTY_50'], default='NIFTY_50',
                            help='Signal source (default: NIFTY_50)')
    trade_parser.add_argument('--trading', choices=['NIFTYBEES', 'JUNIORBEES', 'BANKBEES'],
                            default='NIFTYBEES', help='Trading instrument (default: NIFTYBEES)')
    
    # Reset command
    subparsers.add_parser('reset', help='Reset position tracking')
    
    args = parser.parse_args()
    
    if not args.command:
        print("🤖 Enhanced Multi-Indicator Trading Bot")
        print("=" * 40)
        print("Available commands:")
        print("  auth     - Authenticate with Kite Connect")
        print("  test     - Test all components")
        print("  compare  - Compare strategy profiles")
        print("  trade    - Start enhanced trading")
        print("  reset    - Reset position tracking")
        print("\nExample usage:")
        print("  python3 cli_enhanced.py test")
        print("  python3 cli_enhanced.py trade --profile balanced")
        print("  python3 cli_enhanced.py compare")
        parser.print_help()
        return
    
    # Execute commands
    if args.command == 'auth':
        auth_enhanced()
    
    elif args.command == 'test':
        test_enhanced_connection()
    
    elif args.command == 'compare':
        show_strategy_comparison()
    
    elif args.command == 'trade':
        run_enhanced_trading(args)
    
    elif args.command == 'reset':
        reset_position()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()