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

- `OPENWEATHER_API_KEY`: Your OpenWeather API key
- `IFTT_WEBHOOK_URL`: Your IFTT webhook URL
- `COORDINATES`: Location coordinates in format `lat,lon` (e.g., `40.7128,-74.0060`)

### 2. IFTT Webhook Setup

1. Create an IFTT account and set up a webhook
2. The webhook will receive three values:
   - `value1`: Alert message with pressure drop amount
   - `value2`: Current and minimum pressure values
   - `value3`: Expected time of minimum pressure

### 3. OpenWeather API

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

### Other Configurable Parameters

- **API Settings**: Timeout, units, URL
- **Forecast Analysis**: Hours to analyze, intervals to check
- **Logging**: Level, format, file name
- **Webhook**: Timeout settings
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