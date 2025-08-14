# KNMI Weather Service Integration

## Overview

This integration adds comprehensive weather data support using the KNMI (Royal Netherlands Meteorological Institute) Open Data API. KNMI provides official weather data for the Netherlands with high accuracy and reliability.

## Features

- ✅ **Multi-tier API Key Support**: Anonymous, Registered, and Bulk keys
- ✅ **Automatic Key Management**: Monitors keys and updates automatically when they change
- ✅ **Rate Limiting**: Built-in rate limiting per key type
- ✅ **Caching**: Smart caching to reduce API calls
- ✅ **Fallback Integration**: Works with existing weather providers (WeatherAPI.com, Open-Meteo)
- ✅ **Netherlands Focus**: Optimized for Netherlands locations with KNMI priority
- ✅ **Real-time Monitoring**: Key expiry notifications and status monitoring

## Quick Start

### 1. Basic Setup (Anonymous Key)

No configuration needed! The service includes a default anonymous key valid until July 1, 2026.

```bash
# Test the integration
python tests/test_knmi_integration.py
```

### 2. Get Better API Keys (Recommended)

For higher rate limits and dedicated access:

1. **Register for Account**: Visit [KNMI Data Platform](https://dataplatform.knmi.nl/)
2. **Request API Key**: Go to API Catalog → Request an API key for Open Data API
3. **Configure Environment**: Add your key to the system

```bash
# Set registered key (200 req/sec, 1000 req/hour)
export KNMI_API_KEY="your_registered_key_here"

# Optional: Set bulk key for dataset downloads
export KNMI_BULK_KEY="your_bulk_key_here"
```

### 3. Key Update Management

The system automatically detects and uses updated keys:

```bash
# Update anonymous key when KNMI provides new one
export KNMI_ANONYMOUS_KEY_UPDATED="new_anonymous_key"
export KNMI_ANONYMOUS_KEY_EXPIRY="2027-07-01"  # Optional expiry date
```

## API Endpoints

### Weather Data
```bash
# Get Netherlands weather via KNMI
curl -X POST http://localhost:3000/tools/knmi_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Amsterdam"}'

# Response includes:
# - Current weather observations
# - Data file information
# - API key type being used
# - Forecast availability
```

### Service Status
```bash
# Check KNMI API connectivity and key status
curl http://localhost:3000/tools/knmi_status

# Response includes:
# - API connectivity status
# - Available datasets count
# - Current key information
# - Rate limit status
```

### Key Monitoring
```bash
# Run comprehensive key monitoring
curl -X POST http://localhost:3000/tools/knmi_monitor

# Response includes:
# - All configured keys validation
# - Environment updates detected
# - Expiry notifications
# - Auto-update results
```

## Integration with Existing Tools

### Weather Function Enhancement

The `get_weather()` function now automatically detects Netherlands locations and uses KNMI:

```python
# These will use KNMI automatically:
get_weather("Amsterdam")
get_weather("Netherlands") 
get_weather("Rotterdam")
get_weather("De Bilt")

# Other locations still use WeatherAPI.com or Open-Meteo
get_weather("London")  # Uses WeatherAPI.com or Open-Meteo
```

### Direct KNMI Functions

New dedicated functions for KNMI access:

```python
from utilities.ai_tools import get_knmi_weather_sync, check_knmi_status

# Get Netherlands weather directly
weather = get_knmi_weather_sync("Netherlands")

# Check service status
status = check_knmi_status()
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KNMI_API_KEY` | Registered API key (highest priority) | None |
| `KNMI_BULK_KEY` | Bulk download key | None |
| `KNMI_ANONYMOUS_KEY_UPDATED` | Updated anonymous key | None |
| `KNMI_ANONYMOUS_KEY_EXPIRY` | Expiry date for anonymous key | None |

### Auto-Updated Variables (Set by Monitor)

| Variable | Description | Source |
|----------|-------------|--------|
| `KNMI_API_KEY_AUTO` | Best available key (auto-selected) | Key Monitor |
| `KNMI_KEY_TYPE_AUTO` | Type of auto-selected key | Key Monitor |

### Key Priority Order

1. **Auto-Updated Key** (from monitoring service)
2. **Registered Key** (`KNMI_API_KEY`)
3. **Bulk Key** (`KNMI_BULK_KEY`) 
4. **Updated Anonymous Key** (`KNMI_ANONYMOUS_KEY_UPDATED`)
5. **Default Anonymous Key** (built-in, expires 2026-07-01)

## Key Management

### Automatic Key Updates

The system includes automatic key management:

1. **Environment Monitoring**: Checks for updated keys in environment variables every hour
2. **Key Validation**: Tests all configured keys for validity
3. **Expiry Notifications**: Alerts when keys are approaching expiry (30, 7, 1 days before)
4. **Auto-Selection**: Automatically chooses the best available key
5. **Service Updates**: Updates the weather service with the best key

### Manual Key Updates

When KNMI provides new keys, update them via environment:

```bash
# Method 1: Environment variables
export KNMI_ANONYMOUS_KEY_UPDATED="new_key_here"
export KNMI_ANONYMOUS_KEY_EXPIRY="2027-01-01"

# Method 2: Docker environment
# Add to docker-compose.yml:
environment:
  - KNMI_ANONYMOUS_KEY_UPDATED=new_key_here
  - KNMI_ANONYMOUS_KEY_EXPIRY=2027-01-01

# Method 3: Restart service (auto-detects changes)
docker-compose restart backend-main
```

### Key Storage

Keys are stored in:
- **Runtime**: Environment variables and service memory
- **Configuration**: `config/knmi_keys.json` (auto-generated)
- **Backup**: `config/knmi_keys_backup.json` (automatic backups)

## Rate Limits by Key Type

| Key Type | Requests/Second | Requests/Hour | Usage |
|----------|-----------------|---------------|-------|
| **Anonymous** | 50 (shared) | 3,000 (shared) | Basic usage |
| **Registered** | 200 (dedicated) | 1,000 (dedicated) | Normal usage |
| **Bulk** | 100 (dedicated) | 10,000+ (dataset) | Data downloads |

## Available Datasets

KNMI provides access to multiple weather datasets:

- **Current Weather**: `harmonie_arome_cy40_p1` - Current weather model
- **Forecast**: `harmonie_arome_cy40_p3` - 3-day forecast  
- **Observations**: `klimatologie-daggegevens` - Daily observations
- **Radar**: `radar_reflectivity_composites` - Radar data

## Testing

### Run Integration Tests

```bash
# Test all components
python tests/test_knmi_integration.py

# Test specific components
curl http://localhost:3000/tools/
curl http://localhost:3000/tools/knmi_status
curl -X POST http://localhost:3000/tools/knmi_monitor
```

### Test Weather Queries

```bash
# Test via existing weather tool (should auto-detect KNMI)
curl -X POST http://localhost:3000/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "weather in Amsterdam"}'

# Test direct KNMI endpoint
curl -X POST http://localhost:3000/tools/knmi_weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Netherlands"}'
```

## Troubleshooting

### Common Issues

1. **"KNMI weather service not available"**
   - Check if service started correctly in logs
   - Verify imports in `routes/tools.py`

2. **"Invalid API key"**
   - Verify key format and expiry
   - Check environment variables
   - Run key monitoring: `curl -X POST http://localhost:3000/tools/knmi_monitor`

3. **"Rate limit exceeded"**
   - Check key type and current usage
   - Wait for rate limit reset
   - Consider upgrading to registered key

4. **No data returned**
   - Verify API connectivity
   - Check KNMI service status
   - Review logs for error messages

### Debug Steps

```bash
# 1. Check service logs
docker logs backend-main --tail 50 | grep KNMI

# 2. Test API connectivity
curl http://localhost:3000/tools/knmi_status

# 3. Run monitoring cycle
curl -X POST http://localhost:3000/tools/knmi_monitor

# 4. Verify environment
python -c "import os; print([k for k in os.environ.keys() if 'KNMI' in k])"

# 5. Test integration script
python tests/test_knmi_integration.py
```

## Integration Benefits

1. **Netherlands Weather**: High-accuracy official weather data for Netherlands
2. **Automatic Failover**: Falls back to other providers for non-Netherlands locations
3. **Smart Key Management**: Handles key updates and expiry automatically
4. **Rate Optimization**: Built-in caching and rate limiting
5. **Monitoring**: Real-time status and health monitoring
6. **Easy Setup**: Works out-of-the-box with default anonymous key

## Future Enhancements

- [ ] Real-time weather alerts
- [ ] Historical weather data queries
- [ ] Weather map integration
- [ ] Extended forecast periods
- [ ] Multiple location support
- [ ] Custom notification channels

---

🌤️ **KNMI Weather Service** - Providing accurate Netherlands weather data with intelligent key management!
