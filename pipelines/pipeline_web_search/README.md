# Enhanced Web Search Pipeline for OpenWebUI

## Overview

This pipeline provides real-time web search capabilities with current date awareness for July 2025. It automatically detects when users need current information and when the assistant shows uncertainty, triggering web search as needed.

## Features

- ✅ **Zero Configuration**: Works out of the box
- ✅ **Multiple Search Engines**: Brave Search, DuckDuckGo with automatic fallback
- ✅ **Current Date Awareness**: Prioritizes July 2025 content
- ✅ **Automatic Triggering**: Detects news queries and uncertain responses
- ✅ **Real-time Results**: Bypasses cached outdated results
- ✅ **Pipeline Architecture**: Proper OpenWebUI filter pipeline

## Installation

1. **File Location**: This pipeline is already in the correct location:
   ```
   pipelines/pipeline_web_search/enhanced_web_search_pipeline.py
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install -r pipelines/pipeline_web_search/requirements.txt
   ```

3. **Enable in OpenWebUI**:
   - Go to Admin Settings → Pipelines
   - Enable "Enhanced Web Search Pipeline"
   - Configure valve settings as needed

## Configuration

### Pipeline Valves (Configurable in OpenWebUI Admin)

- `max_results`: Maximum search results per query (default: 5)
- `auto_search_enabled`: Enable automatic search triggering (default: true)
- `news_keywords`: Keywords that trigger news search
- `uncertainty_phrases`: Phrases that indicate need for web search

### Search Triggers

**Automatic triggering occurs for:**

1. **News Queries**: "news", "headlines", "current", "latest", "today", "breaking", "2025"
2. **Uncertain Responses**: "I don't know", "I'm not sure", "I cannot provide", "cutoff date"

### Search Engines (in priority order)

1. **DuckDuckGo**: Enhanced HTML parsing with current filtering
2. **Brave Search**: Real-time news results with API
3. **DuckDuckGo Instant**: Instant answers for quick results
4. **Curated Fallback**: Current July 2025 news when APIs fail

## Usage Examples

### Automatic News Search
```
User: "What are the latest headlines?"
→ Pipeline automatically searches for current news
→ Returns July 2025 headlines
```

### Uncertainty Detection
```
User: "Tell me about recent political events"
Assistant: "I don't have current information..."
→ Pipeline detects uncertainty
→ Searches for political news
→ Enhances response with current data
```

### Manual Search
```
User: "Search for current tech news 2025"
→ Pipeline detects search keywords
→ Returns current technology headlines
```

## Architecture

### Filter Pipeline Design

```python
Pipeline Type: Filter
├── inlet() - Pre-processes user messages
│   ├── Detects search keywords
│   ├── Performs web search if needed
│   └── Injects results into conversation
│
└── outlet() - Post-processes assistant responses
    ├── Detects uncertainty phrases
    ├── Triggers search if needed
    └── Enhances response with current data
```

### Search Engine Flow

```
Query → DuckDuckGo HTML Parsing
      ↓ (if fails)
      → Brave Search API
      ↓ (if fails)  
      → DuckDuckGo Instant API
      ↓ (if fails)
      → Curated Current News Fallback
```

## Benefits vs Built-in OpenWebUI Search

| Feature | Built-in Search | Enhanced Pipeline |
|---------|----------------|-------------------|
| Zero Config | ❌ Requires setup | ✅ Works immediately |
| Current 2025 Data | ❌ May return cached | ✅ Prioritizes current |
| Auto Triggering | ❌ Manual only | ✅ Smart detection |
| Multiple Fallbacks | ❌ Single engine | ✅ 4 fallback methods |
| Uncertainty Detection | ❌ No detection | ✅ Auto-enhances responses |
| Pipeline Integration | ❌ Separate system | ✅ Native pipeline |

## File Structure

```
pipelines/pipeline_web_search/
├── enhanced_web_search_pipeline.py  # Main pipeline
├── config.json                      # Configuration
├── requirements.txt                  # Dependencies  
├── valves.json                      # Pipeline valves
└── README.md                        # This file
```

## Monitoring & Debugging

### Logs
- Pipeline startup/shutdown events
- Search method attempts and failures
- Trigger detection events

### Testing
```python
# Test search functionality
User query: "latest news July 2025"
Expected: Current headlines with sources

# Test uncertainty detection  
Assistant: "I don't have current information"
Expected: Automatic web search triggered
```

## Migration from Legacy

The old `utilities/web_search_tool.py` has been deprecated and now redirects to this pipeline. This provides:

- Better performance with real search APIs
- Current date awareness (July 2025)
- Automatic uncertainty detection
- Zero configuration requirements

## Troubleshooting

### No Search Results
1. Check internet connectivity
2. Verify pipeline is enabled in admin
3. Check valve configuration
4. Review logs for API failures

### Outdated Results
1. Ensure `auto_search_enabled` is true
2. Verify current date logic
3. Check search query enhancement
4. Confirm curated news fallback

### Performance Issues
1. Adjust `max_results` valve
2. Monitor search timeout settings
3. Check multiple API fallbacks
4. Review async execution

## Support

For issues or feature requests, this pipeline provides comprehensive logging and error handling. Check the OpenWebUI pipeline logs for detailed debugging information.

## Version History

- **v1.0** (2025-07-18): Initial release with multi-engine search and auto-triggering
