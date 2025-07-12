# Pressure Monitor

A Python script that monitors weather pressure changes using the OpenWeather API and triggers IFTT webhooks when forecasted pressure drops more than 8 mmHg in the next 24 hours.

## Features

- **Hourly Monitoring**: Runs every hour via GitHub Actions cron job
- **Pressure Analysis**: Analyzes 24-hour forecast for pressure drops
- **IFTT Integration**: Triggers webhooks when conditions are met
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Error Handling**: Robust retry logic with 10 attempts, 1-minute intervals
- **Unit Conversion**: Automatic conversion from hPa to mmHg

## Setup

### 1. Repository Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

#### Required Secrets:
- `OPENWEATHER_API_KEY`: Your OpenWeather API key
- `COORDINATES`: Location coordinates in format `lat,lon` (e.g., `40.7128,-74.0060`)

#### Notification Channel Secrets:

**IFTTT (Default):**
- `IFTT_WEBHOOK_URL`: Your IFTT webhook URL

**Telegram (Optional):**
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID

### 2. IFTT Webhook Setup

1. Create an IFTT account and set up a webhook
2. The webhook will receive three values:
   - `value1`: Alert message with pressure drop amount
   - `value2`: Current and minimum pressure values
   - `value3`: Expected time of minimum pressure

### 3. Telegram Bot Setup

Follow these steps to set up Telegram notifications:

#### Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather by clicking "Start"
3. **Send the command**: `/newbot`
4. **Follow the prompts**:
   - Enter a name for your bot (e.g., "Pressure Monitor")
   - Enter a username for your bot (must end with 'bot', e.g., "pressure_monitor_bot")
5. **Save the bot token** that BotFather sends you (you'll need this for `TELEGRAM_BOT_TOKEN`)

#### Step 2: Get Your Chat ID

**Method 1: Using the Bot (Recommended)**
1. **Search for your bot** by username in Telegram
2. **Start a chat** with your bot by clicking "Start"
3. **Send any message** to the bot (e.g., "Hello")
4. **Visit this URL** in your browser (replace `YOUR_BOT_TOKEN` with your actual token):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
5. **Find your chat ID** in the response JSON (look for `"chat":{"id":123456789}`)
6. **Save the chat ID** (you'll need this for `TELEGRAM_CHAT_ID`)

**Method 2: Using @userinfobot**
1. **Search for `@userinfobot`** in Telegram
2. **Start a chat** with @userinfobot
3. **Send any message** to get your chat ID
4. **Note**: This gives you your personal chat ID, which you can use for direct messages

#### Step 3: Test Your Bot

1. **Send a test message** to your bot using this URL (replace with your details):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage?chat_id=YOUR_CHAT_ID&text=Test message
   ```
2. **Check your Telegram** to see if you received the test message

#### Step 4: Configure GitHub Secrets

Add these secrets to your GitHub repository:
- `TELEGRAM_BOT_TOKEN`: Your bot token from Step 1
- `TELEGRAM_CHAT_ID`: Your chat ID from Step 2

#### Step 5: Enable Telegram Notifications

Edit `config.py` and enable Telegram:
```python
'telegram': {
    'enabled': True,  # Change from False to True
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
    'parse_mode': 'HTML'
}
```

### 4. OpenWeather API

1. Sign up at [OpenWeather](https://openweathermap.org/api)
2. Get your API key from the dashboard
3. The script uses the 5-day forecast API

## Configuration

All configuration parameters are centralized in `config.py` for easy maintenance and customization.

### Pressure Threshold

The default threshold is 8 mmHg. To modify this, edit the `PRESSURE_THRESHOLD_MMHG` variable in `config.py`:

```python
PRESSURE_THRESHOLD_MMHG = 8.0  # mmHg - threshold for pressure drop alert
```

### Retry Settings

Default retry configuration:
- Maximum retries: 10
- Retry delay: 60 seconds

Modify in `config.py`:

```python
MAX_RETRIES = 10
RETRY_DELAY = 60  # seconds
```

### Notification Channels

The system supports multiple notification channels that can be enabled/disabled in `config.py`:

```python
NOTIFICATION_CHANNELS = {
    'ifttt': {
        'enabled': True,  # Enable/disable IFTTT notifications
        'webhook_url': os.getenv('IFTT_WEBHOOK_URL'),
        'timeout': 30  # seconds
    },
    'telegram': {
        'enabled': False,  # Enable/disable Telegram notifications
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        'parse_mode': os.getenv('TELEGRAM_PARSE_MODE', 'HTML'),
        'disable_web_page_preview': True,
        'timeout': 30  # seconds
    }
}
```

### Configuration Parameters

All configuration parameters are centralized in `config.py`:

- **API Settings**: URLs, timeouts, units
- **Pressure Monitoring**: Threshold, forecast intervals
- **Retry Logic**: Max retries, delay intervals
- **Logging**: Level, format, file settings
- **Channel Settings**: Timeouts, formatting options

### Other Configurable Parameters

- **API Settings**: Timeout, units, URL
- **Forecast Analysis**: Hours to analyze, intervals to check
- **Logging**: Level, format, file name
- **Channel Settings**: Timeouts, formatting options
- **Unit Conversion**: hPa to mmHg ratio

## Local Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your environment variables:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   IFTT_WEBHOOK_URL=your_webhook_url_here
   COORDINATES=40.7128,-74.0060
   ```

3. Run the script:
   ```bash
   python pressure_monitor.py
   ```

## GitHub Actions

The workflow (`/.github/workflows/pressure-monitor.yml`) runs every hour and:

1. Sets up Python 3.11
2. Installs dependencies
3. Runs the pressure monitor script
4. Uploads logs as artifacts (retained for 7 days)

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab for testing.

## Logging

The script creates detailed logs in `pressure_monitor.log` including:

- API request attempts and results
- Pressure analysis details
- Webhook trigger status
- Error messages and retry attempts

Logs are also uploaded as GitHub Actions artifacts for easy access.

## How It Works

1. **Data Fetching**: Retrieves 5-day forecast from OpenWeather API
2. **Pressure Analysis**: Compares current pressure with 24-hour forecast minimum
3. **Threshold Check**: Triggers alert if pressure drop exceeds 8 mmHg
4. **Webhook Notification**: Sends formatted alert to IFTT webhook
5. **Logging**: Records all activities for monitoring and debugging

## Error Handling

- **API Failures**: Retries up to 10 times with 1-minute delays
- **Invalid Data**: Graceful handling of malformed API responses
- **Network Issues**: Timeout handling and connection error recovery
- **Environment Variables**: Validation of required configuration

## Monitoring

Check the GitHub Actions tab to monitor:
- Workflow execution status
- Log artifacts for debugging
- Manual trigger capability for testing

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all secrets are set in GitHub
2. **API Key Issues**: Verify OpenWeather API key is valid
3. **Webhook Failures**: Check IFTT webhook URL and connectivity
4. **Coordinate Format**: Ensure coordinates are in `lat,lon` format

### Debug Steps

1. Check GitHub Actions logs for error messages
2. Download log artifacts for detailed analysis
3. Test locally with `.env` file for isolated debugging
4. Verify API responses manually if needed

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details. 