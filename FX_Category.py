import requests
import pandas as pd
import schedule
import time

API_KEY = '776MJAEFDFVXQSUG'
BASE_URL = 'https://www.alphavantage.co/query'
TELEGRAM_TOKEN = '7714933281:AAHFBcBOdZXGye3-W1gdpknFrAJE9HTLSro'
CHAT_ID = '1172894152'

# List to hold categorized pairs
pair_categories = {}


# Fetch data from Alpha Vantage API for 15-min timeframe
def fetch_forex_15min(pair):
    try:
        params = {
            'function': 'FX_INTRADAY',
            'from_symbol': pair[:3],
            'to_symbol': pair[3:],
            'interval': '15min',
            'apikey': API_KEY
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # Extract 15-minute time series
        df = pd.DataFrame(data['Time Series FX (15min)']).T
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        print(f"Error fetching 15-min data for {pair}: {e}")
        return None


# Calculate EMA
def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()


# Categorize pairs based on 200 EMA and 800 EMA crossover (runs once a day)
def categorize_pairs_once():
    global pair_categories
    forex_pairs = ['EURUSD', 'GBPUSD', 'XAUUSD', 'GBPJPY', 'USDJPY', 'EURJPY', 'GBPCAD',
                   'GBPAUD', 'EURCAD', 'EURAUD', 'USDCAD', 'AUDJPY', 'CADJPY']

    for pair in forex_pairs:
        # Fetch 15-minute data
        min15_data = fetch_forex_15min(pair)

        if min15_data is None:
            continue

        ema_200 = calculate_ema(min15_data, 200)
        ema_800 = calculate_ema(min15_data, 800)

        if ema_200.iloc[-1] > ema_800.iloc[-1]:
            category = "Buy"
        else:
            category = "Sell"

        # Store category for later use
        pair_categories[pair] = category

        # Send categorized message
        category_message = f"{pair} is categorized as a {category} signal based on 200/800 EMA crossover."
        send_telegram_alert(category_message)


# Check if price is touching the 200 EMA or 800 EMA (runs continuously)
def check_price_touch_ema():
    global pair_categories
    forex_pairs = list(pair_categories.keys())  # Only check pairs that are categorized

    for pair in forex_pairs:
        # Fetch 15-minute data
        min15_data = fetch_forex_15min(pair)

        if min15_data is None:
            continue

        ema_200 = calculate_ema(min15_data, 200)
        ema_800 = calculate_ema(min15_data, 800)
        current_price = min15_data['close'].iloc[-1]

        # Check if the price is touching the 200 EMA or 800 EMA
        touching_200_ema = abs(current_price - ema_200.iloc[-1]) <= 0.0005  # Adjust tolerance
        touching_800_ema = abs(current_price - ema_800.iloc[-1]) <= 0.0005

        if touching_200_ema:
            alert_message = f"Price is touching the 200 EMA for {pair_categories[pair]} signal on {pair}."
            send_telegram_alert(alert_message)
        elif touching_800_ema:
            alert_message = f"Price is touching the 800 EMA for {pair_categories[pair]} signal on {pair}."
            send_telegram_alert(alert_message)


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


# Schedule categorization once a day
schedule.every().day.at("10:00").do(categorize_pairs_once)

# Schedule price check every 5 minutes
schedule.every(5).minutes.do(check_price_touch_ema)
print("Running")

print("Tracker is running...")

while True:
    schedule.run_pending()
    time.sleep(1)
