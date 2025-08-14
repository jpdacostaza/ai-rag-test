"""
title: Optimized Weather Tool
author: Weather Team
version: 4.0.0
license: MIT
requirements: 
description: |-
  Streamlined weather tool following industry best practices.
  Zero-configuration deployment using only ddgs library.
  Modular design with separated concerns and minimal code duplication.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

# Zero-conf web search import
try:
    from utilities.enhanced_web_search import search_web
    WEB_SEARCH_AVAILABLE = True
    print(f"[WeatherTool] Zero-conf web search available")
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    print(f"[WeatherTool] Web search unavailable")

PRINT_PREFIX = "[WeatherTool]"


class WeatherConfig:
    """Configuration constants for weather tool"""
    NETHERLANDS_KEYWORDS = [
        "netherlands", "holland", "amsterdam", "rotterdam", "the hague", 
        "utrecht", "eindhoven", "tilburg", "groningen", "almere", "breda", 
        "nijmegen", "enschede", "haarlem", "arnhem", "zaanstad", 
        "haarlemmermeer", "'s-hertogenbosch", "apeldoorn", "hoofddorp", 
        "maastricht", "leiden", "dordrecht", "zoetermeer", "zwolle", "knmi"
    ]
    
    KNMI_QUERIES = [
        "site:knmi.nl/nederland-nu/weer/verwachtingen temperature celsius weather today",
        "knmi.nl nederland-nu weer verwachtingen temperatuur vandaag graden",
        "KNMI weather Netherlands current temperature conditions celsius"
    ]
    
    INTERNATIONAL_QUERIES = [
        "{location} weather today current temperature celsius forecast",
        "current weather {location} temperature conditions",
        "weather forecast {location} real time live"
    ]
    
    TEMP_PATTERNS = [
        r'(\d+)°?c', r'(\d+)/(\d+)°', r'max.*?(\d+)°?', r'min.*?(\d+)°?',
        r'rond\s*(\d+)°', r'tot\s*(\d+)°', r'temperatuur.*?(\d+)°?', 
        r'(\d+)\s*graden', r'maximumtemperatuur.*?(\d+)', r'(\d{1,2})/(\d{1,2})\s*°c'
    ]
    
    CONDITION_MAP = {
        'zonnig': '☀️ Sunny', 'warm': '🌡️ Warm', 'heet': '🔥 Hot',
        'droog': '🏜️ Dry', 'bewolkt': '☁️ Cloudy', 'regen': '🌧️ Rain',
        'wind': '💨 Windy', 'code geel': '⚠️ Code Yellow Warning',
        'code oranje': '🟠 Code Orange Warning', 'hitte': '🔥 Heat',
        'tropisch': '🌴 Tropical'
    }


class WeatherParser:
    """Weather data parser with zero-conf text analysis"""
    
    @staticmethod
    def extract_temperatures(content: str) -> List[str]:
        """Extract temperature values from text"""
        temperatures = []
        for pattern in WeatherConfig.TEMP_PATTERNS:
            matches = re.findall(pattern, content.lower())
            for match in matches:
                if isinstance(match, tuple):
                    temperatures.extend([t for t in match if t.isdigit()])
                elif match.isdigit():
                    temperatures.append(match)
        return sorted(list(set(temperatures)), key=int) if temperatures else []
    
    @staticmethod
    def extract_conditions(content: str) -> List[str]:
        """Extract weather conditions from text"""
        content_lower = content.lower()
        found_conditions = []
        for dutch_term, emoji_condition in WeatherConfig.CONDITION_MAP.items():
            if dutch_term in content_lower:
                found_conditions.append(emoji_condition)
        return found_conditions[:5]  # Limit to 5 conditions
    
    @staticmethod
    def format_weather_data(location: str, temps: List[str], conditions: List[str], 
                          content: str, source: str) -> str:
        """Format extracted weather data into structured output"""
        current_time = datetime.now()
        date_str = current_time.strftime('%A, %B %d, %Y')
        time_str = current_time.strftime('%H:%M')
        
        result = f"🌡️ **LIVE WEATHER DATA - {location.upper()}**\n"
        result += f"📅 Retrieved: {date_str} at {time_str}\n"
        result += f"🌐 Source: {source}\n"
        result += f"📊 Method: Zero-configuration web search\n\n"
        
        if temps:
            result += f"🌡️ **TEMPERATURES:**\n"
            if len(temps) == 1:
                result += f"   Current: {temps[0]}°C\n"
            else:
                result += f"   Range: {min(temps, key=int)}°C - {max(temps, key=int)}°C\n"
            result += "\n"
        
        if conditions:
            result += f"🌤️ **CONDITIONS:**\n"
            for condition in conditions:
                result += f"   {condition}\n"
            result += "\n"
        
        if content and len(content) > 50:
            clean_content = re.sub(r'[^\w\s°]+', ' ', content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            result += f"📋 **FORECAST DETAILS:**\n"
            result += f"   {clean_content[:200]}{'...' if len(clean_content) > 200 else ''}\n\n"
        
        return result


class WeatherSearcher:
    """Weather search service with zero-conf implementation"""
    
    @staticmethod
    async def search_knmi(location: str) -> Optional[str]:
        """Search KNMI official weather data"""
        print(f"{PRINT_PREFIX} Searching KNMI for {location}")
        
        for query in WeatherConfig.KNMI_QUERIES:
            try:
                results = await search_web(query, max_results=3)
                if results.get("results"):
                    for item in results["results"]:
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')
                        link = item.get('link', '')
                        
                        if 'knmi.nl' in link.lower() and any(
                            word in (title + ' ' + snippet).lower() 
                            for word in ['verwachtingen', 'nederland-nu', 'temperatuur', 'weather']
                        ):
                            print(f"{PRINT_PREFIX} Found KNMI data: {title[:50]}")
                            
                            temps = WeatherParser.extract_temperatures(snippet)
                            conditions = WeatherParser.extract_conditions(snippet)
                            
                            return WeatherParser.format_weather_data(
                                location, temps, conditions, snippet, link
                            )
            except Exception as e:
                print(f"{PRINT_PREFIX} KNMI query failed: {e}")
                continue
        
        return None
    
    @staticmethod
    async def search_international(location: str) -> Optional[str]:
        """Search international weather data"""
        print(f"{PRINT_PREFIX} Searching international weather for {location}")
        
        for query_template in WeatherConfig.INTERNATIONAL_QUERIES:
            try:
                query = query_template.format(location=location)
                results = await search_web(query, max_results=3)
                
                if results.get("results"):
                    for item in results["results"]:
                        title = item.get('title', '')
                        snippet = item.get('snippet', '')
                        link = item.get('link', '')
                        
                        # Filter out non-weather content
                        content_check = (title + ' ' + snippet).lower()
                        reject_keywords = [
                            'windows', 'microsoft', 'file', 'download', 
                            'software', 'tutorial', 'computer'
                        ]
                        
                        if any(reject in content_check for reject in reject_keywords):
                            continue
                        
                        weather_keywords = [
                            'temperature', 'weather', 'forecast', 'celsius', 
                            'wind', 'rain', 'sunny', 'cloudy'
                        ]
                        
                        if any(keyword in content_check for keyword in weather_keywords):
                            temps = WeatherParser.extract_temperatures(snippet)
                            conditions = WeatherParser.extract_conditions(snippet)
                            
                            if temps or conditions:  # Only return if we found weather data
                                return WeatherParser.format_weather_data(
                                    location, temps, conditions, snippet, link
                                )
            except Exception as e:
                print(f"{PRINT_PREFIX} International query failed: {e}")
                continue
        
        return None


class WeatherFilter:
    """Weather filter with optimized model-specific prompting"""
    
    def __init__(self):
        self.valves = FilterValves()
    
    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        if not self.valves.enable_weather_lookup:
            return body
        
        messages = body.get("messages", [])
        if not messages:
            return body
        
        last_message = messages[-1]
        content = last_message.get("content", "").lower()
        
        # Weather detection patterns
        weather_patterns = [
            r'\bweather\b.*?\b(in|for|at)\s+([a-zA-Z\s,]+)',
            r'\btemperature\b.*?\b(in|for|at)\s+([a-zA-Z\s,]+)',
            r'\b(what\'s|whats|how)\s+.*weather.*\b(in|for|at)\s+([a-zA-Z\s,]+)',
            r'\b(check|get|show)\s+weather\s+.*?([a-zA-Z\s,]+)',
            r'\bweather\s+(today|now|current).*?\b([a-zA-Z\s,]+)'
        ]
        
        for pattern in weather_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                location = match.groups()[-1].strip()
                weather_info = await self._get_weather_info(location)
                
                # Optimized model-specific prompting
                model_name = body.get("model", "").lower()
                
                if "gemma" in model_name:
                    # Gemma: Direct injection into user message
                    original_content = last_message.get("content", "")
                    weather_injected_content = f"""REAL-TIME WEATHER DATA FOR {location.upper()}:
{weather_info}

⚠️ CRITICAL: Use ONLY the weather data above. Ignore any cached/training data about weather.

USER QUESTION: {original_content}"""
                    last_message["content"] = weather_injected_content
                    
                else:
                    # Standard: System message injection
                    system_prompt = f"""LIVE WEATHER DATA FOR {location.upper()}:
{weather_info}

INSTRUCTIONS: Answer using ONLY this current weather data. Ignore any training data about weather."""
                    
                    messages.insert(0, {"role": "system", "content": system_prompt})
                
                body["messages"] = messages
                break
        
        return body
    
    async def _get_weather_info(self, location: str) -> str:
        """Get weather information for location"""
        if not WEB_SEARCH_AVAILABLE:
            return "Weather service unavailable - web search not found."
        
        try:
            # Check if location is in Netherlands
            is_netherlands = any(
                keyword in location.lower() 
                for keyword in WeatherConfig.NETHERLANDS_KEYWORDS
            )
            
            if is_netherlands:
                result = await WeatherSearcher.search_knmi(location)
                if result:
                    return result
            
            # International or fallback search
            result = await WeatherSearcher.search_international(location)
            if result:
                return result
            
            return f"Unable to retrieve current weather data for {location}"
            
        except Exception as e:
            print(f"{PRINT_PREFIX} Error in weather lookup: {e}")
            return f"Weather lookup error for {location}: {str(e)}"


class FilterValves(BaseModel):
    enable_weather_lookup: bool = Field(
        default=True, description="Enable automatic weather lookups"
    )


# Tool classes for external usage
class Tools:
    def __init__(self):
        self.filter = WeatherFilter()
    
    async def get_weather(self, location: str = "Netherlands", include_forecast: bool = True) -> str:
        """Get current weather information"""
        try:
            return await self.filter._get_weather_info(location)
        except Exception as e:
            return f"Error getting weather for {location}: {str(e)}"
    
    async def get_current_weather(self, location: str = "Netherlands") -> str:
        """Get current weather conditions only"""
        return await self.get_weather(location, include_forecast=False)


# Export classes
Filter = WeatherFilter
