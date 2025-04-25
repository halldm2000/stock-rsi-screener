# RSI Stock Screener

A Python-based RSI (Relative Strength Index) screener that monitors multiple stocks across different exchanges and alerts you when they enter overbought or oversold conditions.

## Features

- Monitor multiple stocks simultaneously
- Support for international exchanges (US, German, French, Swiss, etc.)
- Real-time RSI calculations
- Configurable overbought/oversold thresholds
- Continuous monitoring mode
- Sorted display by RSI values
- Optional Slack and email notifications
- SMS notifications via carrier email gateways

## Installation

1. Clone the repository:
```bash
git clone https://github.com/halldm2000/stock-rsi-screener.git
cd stock-rsi-screener
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Edit `tickers.txt` with your stock symbols (one per line)

2. Run the screener:
```bash
# Basic usage with file input
python rsi_screener.py --file tickers.txt

# Continuous monitoring (checks every 5 minutes)
python rsi_screener.py --file tickers.txt --continuous

# Custom interval and period
python rsi_screener.py --file tickers.txt --continuous --interval 300 --period 30d

# Override RSI thresholds
python rsi_screener.py --file tickers.txt --overbought 80 --oversold 20
```

## Command Line Options

- `--file`: Path to text file containing tickers
- `--tickers`: Additional tickers to monitor (space-separated)
- `--continuous`: Run in continuous monitoring mode
- `--interval`: Seconds between checks in continuous mode (default: 300)
- `--period`: Time period for RSI calculation (default: 90d)
- `--overbought`: RSI overbought threshold (default: 70)
- `--oversold`: RSI oversold threshold (default: 30)
- `--data-interval`: Data interval for calculations (default: 1d)

## Notifications

The screener supports notifications via:
- Slack (set `SLACK_WEBHOOK` environment variable)
- Email (set `EMAIL_FROM` and `EMAIL_TO` environment variables)
- SMS via carrier email gateways (configure in `config.local.py`)

### Setting up SMS Notifications

1. Copy the template configuration:
```bash
cp config.template.py config.local.py
```

2. Edit `config.local.py` with your settings:
```python
EMAIL_FROM = 'your-gmail@gmail.com'  # Use your Gmail address
EMAIL_TO = 'your-phone-number@tmomail.net'  # Your carrier's email gateway
```

3. Set up Gmail App Password:
   - Go to your Google Account settings
   - Navigate to Security > 2-Step Verification
   - At the bottom, click on "App passwords"
   - Select "Mail" and your device
   - Copy the generated 16-character password
   - Set it as an environment variable:
     ```bash
     export GMAIL_APP_PASSWORD='your-16-character-app-password'
     ```

4. Carrier Email Gateways:
   - T-Mobile: number@tmomail.net
   - AT&T: number@txt.att.net
   - Verizon: number@vtext.com
   - Sprint: number@messaging.sprintpcs.com
   - Virgin Mobile: number@vmobl.com

## License

MIT License 