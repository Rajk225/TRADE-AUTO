import requests
import pandas as pd
import schedule
import time

API_KEY = '776MJAEFDFVXQSUG'
BASE_URL = 'https://www.alphavantage.co/query'
TELEGRAM_TOKEN = '7714933281:AAHFBcBOdZXGye3-W1gdpknFrAJE9HTLSro'
CHAT_ID = '1172894152'
pair = ['EURUSD', 'GBPUSD', 'XAUUSD', 'GBPJPY', 'USDJPY', 'EURJPY', 'GBPCAD',
                   'GBPAUD', 'EURCAD', 'EURAUD', 'USDCAD', 'AUDJPY', 'CADJPY']
# Fetch data from Alpha Vantage API
def fetch_forex_data(pair, timeframe='daily'):
    try:
        function = 'FX_DAILY' if timeframe == 'daily' else 'FX_WEEKLY'
        params = {
            'function': function,
            'from_symbol': pair[:3],
            'to_symbol': pair[3:],
            'apikey': API_KEY
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # Extract the correct time series
        time_series_key = 'Time Series FX (Daily)' if timeframe == 'daily' else 'Time Series FX (Weekly)'
        df = pd.DataFrame(data[time_series_key]).T
        df.columns = ['open', 'high', 'low', 'close']
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Error fetching {timeframe} data for {pair}: {e}")
        return None

# Get the previous day's or week's high/low
def get_previous_high_low(data, period='day'):
    try:
        previous = data.iloc[1]  # Second row is the previous day's/week's data
        return previous['high'], previous['low']
    except Exception as e:
        print(f"Error calculating previous {period}'s high/low: {e}")
        return None, None

# Check if the current price crosses previous high/low
def check_cross(current_price, previous_high, previous_low=None):
    if current_price > previous_high:
        return f"Price has crossed above the previous high: {previous_high}"
    if previous_low and current_price < previous_low:
        return f"Price has crossed below the previous low: {previous_low}"
    return None

# Send alert via Telegram
def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot7714933281:AAHFBcBOdZXGye3-W1gdpknFrAJE9HTLSro/sendMessage"
        params = {'chat_id': CHAT_ID, 'text': message}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("Alert sent on Telegram")
        else:
            print(f"Failed to send alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

# Main tracker function
def run_tracker():
    forex_pairs = ['EURUSD', 'GBPUSD', 'XAUUSD', 'GBPJPY', 'USDJPY', 'EURJPY', 'GBPCAD',
                   'GBPAUD', 'EURCAD', 'EURAUD', 'USDCAD', 'AUDJPY', 'CADJPY']

    for pair in forex_pairs:
        # Get daily and weekly data
        daily_data = fetch_forex_data(pair, timeframe='daily')
        weekly_data = fetch_forex_data(pair, timeframe='weekly')

        if daily_data is None or weekly_data is None:
            continue

        # Get current price
        current_price = daily_data['close'].iloc[0]  # Today's latest price

        # Get previous high/low
        prev_day_high, prev_day_low = get_previous_high_low(daily_data, 'day')
        prev_week_high, prev_week_low = get_previous_high_low(weekly_data, 'week')

        if prev_day_high is None or prev_week_high is None:
            continue

        # Check for crosses
        alert_day = check_cross(current_price, prev_day_high, prev_day_low)
        alert_week = check_cross(current_price, prev_week_high, prev_week_low)

        # Send alerts if any
        if alert_day:
            send_telegram_alert(f"{pair}: {alert_day}")
        if alert_week:
            send_telegram_alert(f"{pair}: {alert_week}")

# Schedule to run the tracker every 5 minutes
schedule.every(5).minutes.do(run_tracker)

print("Tracker is running...")

while True:
    schedule.run_pending()
    time.sleep(1)
