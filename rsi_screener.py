#!/usr/bin/env python3

"""RSI Screener with File Input

Usage examples
--------------
# Scan tickers listed in tickers.txt (one per line, comma‑ or space‑separated OK)
python rsi_screener.py --file tickers.txt

# Mix file + extra tickers
python rsi_screener.py --file tickers.txt --tickers NVDA MSFT

# Override thresholds
python rsi_screener.py --file tickers.txt --overbought 80 --oversold 20

# Set continuous monitoring (default is single run)
python rsi_screener.py --file tickers.txt --continuous

# Set interval between checks (in seconds, default is 300)
python rsi_screener.py --file tickers.txt --continuous --interval 600

Environment variables for optional notifications
------------------------------------------------
SLACK_WEBHOOK   – Slack incoming‑webhook URL
EMAIL_FROM      – sender address for SMTP localhost
EMAIL_TO        – comma‑separated recipient list
"""

import argparse
import os
import sys
import re
import time
import numpy as np
from datetime import datetime

import pandas as pd
import yfinance as yf


# Custom RSI calculation instead of using pandas_ta
def calculate_rsi(data, window=14):
    """Calculate RSI directly without pandas_ta dependency"""
    delta = data.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    down = down.abs()
    
    avg_gain = up.rolling(window=window).mean()
    avg_loss = down.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ----------------------------------------------------------------------
def parse_ticker_file(path: str) -> list[str]:
    """Read a file and extract tickers separated by commas, whitespace or newlines."""
    if not os.path.exists(path):
        sys.exit(f"Ticker file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = fh.read()
    # split on comma or whitespace, remove empties, uppercase
    return [tok.upper() for tok in re.split(r"[,\s]+", data.strip()) if tok]


def fetch_rsi(symbol: str, period: str, interval: str, length: int = 14):
    """Return last close and RSI value."""
    df = yf.download(symbol, period=period, interval=interval, progress=False, threads=False)
    if df.empty:
        raise ValueError("no data")
    
    # Calculate RSI using our custom function
    df['RSI'] = calculate_rsi(df['Close'], window=length)
    
    latest = df.iloc[-1]
    # Fix warnings by using iloc[0] for Pandas Series conversion
    last_rsi = latest['RSI'].iloc[0] if isinstance(latest['RSI'], pd.Series) else latest['RSI']
    last_close = latest['Close'].iloc[0] if isinstance(latest['Close'], pd.Series) else latest['Close']
    
    return float(last_close), float(last_rsi)


def calculate_rsi_for_ticker(ticker, period="1mo", interval="1d", rsi_length=14):
    """Calculate RSI for a given ticker"""
    try:
        close, rsi = fetch_rsi(ticker, period, interval, rsi_length)
        return {
            'ticker': ticker,
            'rsi': rsi,
            'price': close,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"Error calculating RSI for {ticker}: {str(e)}")
        return None


def alert_slack(msg: str):
    url = os.getenv('SLACK_WEBHOOK')
    if not url:
        return
    import requests, json
    try:
        requests.post(url, json={'text': msg}, timeout=5)
    except Exception:
        pass


def alert_email(subject: str, body: str):
    sender = os.getenv('EMAIL_FROM')
    recipients = os.getenv('EMAIL_TO')
    if not (sender and recipients):
        return
    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText(body)
    msg['Subject'], msg['From'], msg['To'] = subject, sender, recipients
    with smtplib.SMTP('localhost') as s:
        s.sendmail(sender, recipients.split(','), msg.as_string())


def check_rsi_signals(rsi_data, oversold_threshold=30, overbought_threshold=70):
    """Check if RSI is in oversold or overbought territory"""
    if rsi_data is None:
        return None
    
    ticker = rsi_data['ticker']
    rsi = rsi_data['rsi']
    price = rsi_data['price']
    time_str = rsi_data['time']
    
    if pd.isna(rsi):
        return None
        
    signal = None
    if rsi <= oversold_threshold:
        signal = "OVERSOLD"
        message = f"\n🔵 OVERSOLD ALERT - {time_str}"
        message += f"\nStock: {ticker}"
        message += f"\nCurrent Price: ${price:.2f}"
        message += f"\nRSI: {rsi:.2f} (Below {oversold_threshold})"
        message += f"\nSignal: Potential Buy Opportunity"
        print(message)
        return f"⚠️ {ticker} RSI={rsi:.1f} (<{oversold_threshold})"
        
    elif rsi >= overbought_threshold:
        signal = "OVERBOUGHT"
        message = f"\n🔴 OVERBOUGHT ALERT - {time_str}"
        message += f"\nStock: {ticker}"
        message += f"\nCurrent Price: ${price:.2f}"
        message += f"\nRSI: {rsi:.2f} (Above {overbought_threshold})"
        message += f"\nSignal: Potential Sell Opportunity"
        print(message)
        return f"⚠️ {ticker} RSI={rsi:.1f} (>{overbought_threshold})"
    
    return None


def validate_ticker(ticker):
    """Validate if a ticker is still active and suggest alternatives if needed."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Check various error conditions
        if 'regularMarketPrice' not in info or info['regularMarketPrice'] is None:
            return False, "No price data available"
        
        if info.get('state') == 'DELISTED':
            return False, f"Delisted on {info.get('delistedDate', 'unknown date')}"
            
        if info.get('quoteType') == 'NONE':
            return False, "Invalid symbol"
        
        # Additional checks for specific error conditions
        if info.get('regularMarketPrice') == 0:
            return False, "Zero price - possible trading halt or delisting"
            
        return True, None
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return False, "Symbol not found"
        elif "timeout" in error_msg.lower():
            return False, "Connection timeout - try again later"
        return False, str(e)


def suggest_ticker_update(ticker):
    """Suggest updates for problematic tickers with exchange suffixes."""
    known_updates = {
        # Merged/Acquired Companies
        'CS': 'UBS',  # Credit Suisse was acquired by UBS
        
        # European Exchanges
        'ALV': 'ALV.DE',    # Allianz SE (Deutsche Börse)
        'BN': 'BN.PA',      # Danone (Euronext Paris)
        'ENGI': 'ENGI.PA',  # Engie (Euronext Paris)
        'EOAN': 'EOAN.DE',  # E.ON SE (Deutsche Börse)
        'MUV2': 'MUV2.DE',  # Munich Re (Deutsche Börse)
        'NESN': 'NESN.SW',  # Nestlé (SIX Swiss Exchange)
        'RWE': 'RWE.DE',    # RWE AG (Deutsche Börse)
        'UNA': 'UNA.AS',    # Unilever (Euronext Amsterdam)
        'VIE': 'VIE.PA',    # Veolia (Euronext Paris)
        
        # Exchange descriptions for error messages
        '_EXCHANGES': {
            'DE': 'Deutsche Börse (German Exchange)',
            'PA': 'Euronext Paris',
            'AS': 'Euronext Amsterdam',
            'SW': 'SIX Swiss Exchange'
        }
    }
    
    if ticker in known_updates:
        suggested = known_updates[ticker]
        if '.' in suggested:  # If it's an exchange-specific symbol
            exchange = suggested.split('.')[1]
            exchange_desc = known_updates['_EXCHANGES'].get(exchange, exchange)
            return suggested, f"Listed on {exchange_desc}"
        return suggested, "Updated symbol after corporate action"
    return None, None


# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="RSI screener with optional file input.")
    p.add_argument('--tickers', nargs='*', default=[], help='symbols to scan (space‑separated)')
    p.add_argument('--file', help='path to text file containing tickers')
    p.add_argument('--overbought', type=float, default=70.0, help='RSI overbought threshold')
    p.add_argument('--oversold', type=float, default=30.0, help='RSI oversold threshold')
    p.add_argument('--period', default='90d', help='Time period for data (e.g., 90d, 1y)')
    p.add_argument('--data-interval', default='1d', help='Data interval (e.g., 1d, 1h)')
    p.add_argument('--continuous', action='store_true', help='Run continuously')
    p.add_argument('--interval', type=int, default=300, help='Seconds between checks in continuous mode')
    p.add_argument('--limit', type=int, help='Limit to the top N tickers (useful for testing)')
    args = p.parse_args()

    symbols: list[str] = []
    if args.file:
        symbols.extend(parse_ticker_file(args.file))
    symbols.extend([s.upper() for s in args.tickers])

    if not symbols:
        sys.exit("No tickers supplied. Use --tickers or --file")

    # de‑duplicate while preserving order
    seen = set()
    symbols = [x for x in symbols if not (x in seen or seen.add(x))]
    
    # Limit number of tickers if specified
    if args.limit and args.limit > 0 and args.limit < len(symbols):
        symbols = symbols[:args.limit]
        print(f"Limited to {args.limit} tickers: {', '.join(symbols)}")

    if args.continuous:
        run_continuous_mode(symbols, args)
    else:
        run_single_check(symbols, args)


def run_single_check(symbols, args):
    rows, alerts = [], []
    for sym in symbols:
        try:
            rsi_data = calculate_rsi_for_ticker(sym, args.period, args.data_interval)
            if rsi_data:
                status = '-'
                rsi_val = rsi_data['rsi']
                price = rsi_data['price']
                
                alert_msg = check_rsi_signals(rsi_data, args.oversold, args.overbought)
                if alert_msg:
                    alerts.append(alert_msg)
                    status = "OVERBOUGHT" if rsi_val >= args.overbought else "OVERSOLD"
                
                rows.append({'Symbol': sym, 'Close': f"{price:.2f}", 'RSI': f"{rsi_val:.1f}", 'Signal': status})
        except Exception as e:
            rows.append({'Symbol': sym, 'Close': 'n/a', 'RSI': 'n/a', 'Signal': str(e)})

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    if alerts:
        message = '\n'.join(alerts)
        alert_slack(message)
        alert_email('RSI Screener Alert', message)


def run_continuous_mode(symbols, args):
    print("RSI Screener Started in Continuous Mode...")
    
    # Validate tickers first
    valid_symbols = []
    invalid_symbols = []
    print("\nValidating tickers...")
    
    for ticker in symbols:
        is_valid, error = validate_ticker(ticker)
        if not is_valid:
            suggestion, reason = suggest_ticker_update(ticker)
            print(f"\n⚠️  Warning: {ticker} - {error}")
            if suggestion:
                print(f"   Suggestion: Use {suggestion} instead")
                print(f"   Reason: {reason}")
                # Try validating the suggested ticker
                is_suggested_valid, suggested_error = validate_ticker(suggestion)
                if is_suggested_valid:
                    print(f"   ✅ Verified: {suggestion} is valid")
                    valid_symbols.append(suggestion)
                else:
                    print(f"   ❌ Note: Suggested ticker {suggestion} also has issues: {suggested_error}")
            invalid_symbols.append(ticker)
        else:
            valid_symbols.append(ticker)
            print(f"✅ {ticker} - Valid")
    
    if invalid_symbols:
        print("\nSummary of Invalid Tickers:")
        for ticker in invalid_symbols:
            suggestion, reason = suggest_ticker_update(ticker)
            if suggestion:
                print(f"• {ticker} → {suggestion} ({reason})")
            else:
                print(f"• {ticker} - No alternative found")
    
    if not valid_symbols:
        print("\nNo valid tickers found. Please update your tickers.txt file with the suggested symbols.")
        return
    
    print(f"\nMonitoring {len(valid_symbols)} valid tickers for RSI signals (Press Ctrl+C to stop)")
    print(f"Checking every {args.interval} seconds")
    print("----------------------------------------")
    
    try:
        while True:
            print(f"\nChecking RSI levels - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            alerts = []
            rows = []  # Store data for table display
            
            for ticker in valid_symbols:
                try:
                    rsi_data = calculate_rsi_for_ticker(ticker, args.period, args.data_interval)
                    if rsi_data:
                        status = '-'
                        alert_msg = check_rsi_signals(rsi_data, args.oversold, args.overbought)
                        if alert_msg:
                            alerts.append(alert_msg)
                            status = "OVERBOUGHT" if rsi_data['rsi'] >= args.overbought else "OVERSOLD"
                        
                        rows.append({
                            'Symbol': ticker,
                            'Price': f"${rsi_data['price']:.2f}",
                            'RSI': rsi_data['rsi'],  # Store as float for sorting
                            'Signal': status
                        })
                except Exception as e:
                    error_msg = str(e)
                    if len(error_msg) > 50:  # Truncate long error messages
                        error_msg = error_msg[:47] + "..."
                    rows.append({
                        'Symbol': ticker,
                        'Price': 'n/a',
                        'RSI': float('-inf'),  # Use -inf for sorting errors to bottom
                        'Signal': f'ERROR: {error_msg}'
                    })
            
            # Print current status table
            if rows:
                df = pd.DataFrame(rows)
                # Sort by RSI in descending order
                df = df.sort_values('RSI', ascending=False)
                # Format RSI after sorting
                df['RSI'] = df['RSI'].apply(lambda x: f"{x:.1f}" if x != float('-inf') else 'n/a')
                print("\nCurrent Status (Sorted by RSI):")
                print(df.to_string(index=False))
            
            # Send alerts to Slack/email if any
            if alerts:
                message = '\n'.join(alerts)
                alert_slack(message)
                alert_email('RSI Screener Alert', message)
            
            # Wait before next check
            wait_time = args.interval
            print(f"\nWaiting {wait_time} seconds before next check...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\nRSI Screener stopped by user")


if __name__ == '__main__':
    main()
