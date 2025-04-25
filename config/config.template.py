"""
Local configuration file for RSI Screener.
Copy this file to config.local.py and customize with your settings.
"""

# Email notification settings
EMAIL_FROM = 'your-email@example.com'  # Replace with your email address
EMAIL_TO = 'your-phone@carrier.com'    # Replace with your carrier's SMS gateway

# Twilio settings
TWILIO_ACCOUNT_SID = 'your_account_sid_here'  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = 'your_auth_token_here'    # Replace with your Twilio Auth Token
TWILIO_PHONE_NUMBER = '+1234567890'           # Replace with your Twilio phone number
TWILIO_TO_NUMBER = '+1234567890'              # Replace with your phone number

# SMTP Email Server settings
# (e.g., for Gmail: host='smtp.gmail.com', port=587, use_tls=True)
# (If using Gmail, you might need an App Password: https://support.google.com/accounts/answer/185833)
EMAIL_HOST = 'smtp.example.com'            # Replace with your SMTP server hostname
EMAIL_PORT = 587                            # Replace with your SMTP server port (e.g., 587 for TLS, 465 for SSL, 25 for unencrypted)
EMAIL_USE_TLS = True                        # Set to True if your server uses TLS, False otherwise
EMAIL_USER = 'your-login-username@example.com' # Replace with your SMTP login username (often same as EMAIL_FROM)
EMAIL_PASSWORD = 'your_password_here'          # Replace with your SMTP login password (or app password)

# Slack settings (optional)
SLACK_WEBHOOK = 'your_slack_webhook_url'      # Replace with your Slack webhook URL

# Example carrier SMS gateways:
# T-Mobile: number@tmomail.net
# AT&T: number@txt.att.net
# Verizon: number@vtext.com
# Sprint: number@messaging.sprintpcs.com
# Virgin Mobile: number@vmobl.com 