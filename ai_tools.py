# ai_tools.py: Real-time tools for LLM augmentation (time, weather, math, etc.)
from datetime import datetime
from typing import Optional, List
import requests
import math
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
from bs4 import BeautifulSoup
import wikipedia
import os

# --- Tool: Time & Date ---
def get_current_time(timezone: Optional[str] = None) -> str:
    try:
        if timezone:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(timezone))
        else:
            now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Tool: Weather (Open-Meteo, no API key required) ---
def get_weather_weatherapi(city: str = "London") -> str:
    api_key = os.getenv("WEATHERAPI_KEY", "")
    if not api_key:
        logging.warning("[WeatherAPI] API key not set.")
        return "WeatherAPI.com API key not set."
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        logging.debug(f"[WeatherAPI] Requesting: {url}")
        resp = requests.get(url, timeout=10)
        data = resp.json()
        logging.debug(f"[WeatherAPI] Response: {data}")
        if resp.status_code != 200 or 'error' in data:
            return f"WeatherAPI.com error: {data.get('error', {}).get('message', 'Unknown error')}"
        c = data['current']
        loc = data['location']
        return (f"Weather in {loc['name']}, {loc['country']}: {c['temp_c']}°C, "
                f"{c['condition']['text']}, wind {c['wind_kph']} kph, humidity {c['humidity']}%")
    except Exception as e:
        logging.error(f"[WeatherAPI] Exception: {e}")
        return f"WeatherAPI.com lookup failed: {e}"

# --- Tool: Weather (Open-Meteo or WeatherAPI.com) ---
def get_weather(city: str = "London") -> str:
    api_key = os.getenv("WEATHERAPI_KEY", "")
    logging.debug(f"[WeatherTool] WEATHERAPI_KEY set: {bool(api_key)}")
    if api_key:
        result = get_weather_weatherapi(city)
        logging.debug(f"[WeatherTool] WeatherAPI.com result: {result}")
        if result and not result.startswith("WeatherAPI.com API key not set"):
            return result
    try:
        logging.info(f"[WeatherTool] Falling back to Open-Meteo for city: {city}")
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}").json()
        logging.debug(f"[WeatherTool] Open-Meteo geo response: {geo}")
        if not geo.get("results"): return f"Could not find city: {city}"
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        weather = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
        logging.debug(f"[WeatherTool] Open-Meteo weather response: {weather}")
        w = weather.get("current_weather", {})
        return f"Weather in {city}: {w.get('temperature','?')}°C, wind {w.get('windspeed','?')} km/h, {w.get('weathercode','?')}"
    except Exception as e:
        logging.error(f"[WeatherTool] Error fetching weather for {city}: {e}")
        return f"Error fetching weather for {city}: {e}"

# --- Tool: Text Chunking ---
def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks using LangChain's RecursiveCharacterTextSplitter.
    
    Args:
        text: Input text to split
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(text)
        logging.debug(f"[CHUNKING] Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    except Exception as e:
        logging.error(f"[CHUNKING] Error chunking text: {e}")
        return [text]  # Return original text as single chunk if splitting fails

# --- Tool: Unit Conversion ---
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """
    Convert between different units.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit (e.g., 'km', 'lb', 'celsius')
        to_unit: Target unit (e.g., 'm', 'kg', 'fahrenheit')
        
    Returns:
        String with conversion result
    """
    try:
        # Normalize unit names to lowercase
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()
        
        # Length conversions
        length_conversions = {
            ('km', 'm'): 1000,
            ('m', 'km'): 0.001,
            ('m', 'cm'): 100,
            ('cm', 'm'): 0.01,
            ('m', 'mm'): 1000,
            ('mm', 'm'): 0.001,
            ('ft', 'm'): 0.3048,
            ('m', 'ft'): 3.28084,
            ('in', 'cm'): 2.54,
            ('cm', 'in'): 0.393701,
            ('mile', 'km'): 1.60934,
            ('km', 'mile'): 0.621371,
        }
        
        # Weight conversions
        weight_conversions = {
            ('kg', 'g'): 1000,
            ('g', 'kg'): 0.001,
            ('kg', 'lb'): 2.20462,
            ('lb', 'kg'): 0.453592,
            ('g', 'oz'): 0.035274,
            ('oz', 'g'): 28.3495,
        }
        
        # Temperature conversions (special handling)
        if from_unit in ['celsius', 'c'] and to_unit in ['fahrenheit', 'f']:
            result = (value * 9/5) + 32
            return f"{value}°C = {result:.2f}°F"
        elif from_unit in ['fahrenheit', 'f'] and to_unit in ['celsius', 'c']:
            result = (value - 32) * 5/9
            return f"{value}°F = {result:.2f}°C"
        elif from_unit in ['celsius', 'c'] and to_unit in ['kelvin', 'k']:
            result = value + 273.15
            return f"{value}°C = {result:.2f}K"
        elif from_unit in ['kelvin', 'k'] and to_unit in ['celsius', 'c']:
            result = value - 273.15
            return f"{value}K = {result:.2f}°C"
        
        # Check conversions dictionaries
        conversion_key = (from_unit, to_unit)
        reverse_key = (to_unit, from_unit)
        
        for conversions in [length_conversions, weight_conversions]:
            if conversion_key in conversions:
                result = value * conversions[conversion_key]
                return f"{value} {from_unit} = {result:.4f} {to_unit}"
            elif reverse_key in conversions:
                result = value / conversions[reverse_key]
                return f"{value} {from_unit} = {result:.4f} {to_unit}"
        
        # If no conversion found
        return f"Conversion from {from_unit} to {to_unit} is not supported yet."
        
    except Exception as e:
        logging.error(f"[CONVERSION] Error converting {value} {from_unit} to {to_unit}: {e}")
        return f"Error performing unit conversion: {e}"

# --- Tool: Time from timeanddate.com ---
def get_time_from_timeanddate(location: str) -> str:
    """
    Get current time for a location using timeanddate.com scraping.
    
    Args:
        location: City or country name
        
    Returns:
        String with current time and location
    """
    try:
        # Clean up location name for URL
        location_clean = location.strip().lower().replace(' ', '-')
        
        # Map some common locations to timeanddate.com format
        location_mappings = {
            'netherlands': 'netherlands/amsterdam',
            'amsterdam': 'netherlands/amsterdam',
            'london': 'uk/london',
            'new-york': 'usa/new-york',
            'tokyo': 'japan/tokyo',
            'paris': 'france/paris',
            'berlin': 'germany/berlin',
            'moscow': 'russia/moscow',
            'sydney': 'australia/sydney',
        }
        
        location_url = location_mappings.get(location_clean, f'world/{location_clean}')
        url = f"https://www.timeanddate.com/worldclock/{location_url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML to extract time
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for time elements (timeanddate.com uses specific IDs/classes)
        time_element = soup.find('span', {'id': 'ct'}) or soup.find('span', class_='h1')
        
        if time_element:
            current_time = time_element.get_text().strip()
            return f"Current time in {location}: {current_time} (via timeanddate.com)"
        else:
            # Fallback: look for any time-like text
            time_patterns = [
                r'\d{1,2}:\d{2}:\d{2}',
                r'\d{1,2}:\d{2}\s*(AM|PM)',
            ]
            
            page_text = soup.get_text()
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    return f"Current time in {location}: {matches[0]} (via timeanddate.com)"
            
            return f"Could not extract time for {location} from timeanddate.com"
            
    except requests.exceptions.RequestException as e:
        logging.error(f"[TIMEANDDATE] Network error for {location}: {e}")
        return f"Network error getting time for {location}: {e}"
    except Exception as e:
        logging.error(f"[TIMEANDDATE] Error getting time for {location}: {e}")
        return f"Error getting time for {location}: {e}"

# --- Tool: Wikipedia Search ---
def wikipedia_search(query: str, sentences: int = 3) -> str:
    """
    Search Wikipedia and return a summary.
    
    Args:
        query: Search query
        sentences: Number of sentences to return
        
    Returns:
        Wikipedia summary text
    """
    try:
        # Search for the topic
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            return f"No Wikipedia results found for '{query}'"
        
        # Get summary of the first result
        page_title = search_results[0]
        summary = wikipedia.summary(page_title, sentences=sentences)
        
        return f"Wikipedia summary for '{page_title}':\n{summary}"
        
    except wikipedia.exceptions.DisambiguationError as e:
        # Handle disambiguation pages
        try:
            summary = wikipedia.summary(e.options[0], sentences=sentences)
            return f"Wikipedia summary for '{e.options[0]}':\n{summary}"
        except:
            return f"Multiple results found for '{query}'. Be more specific."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'"
    except Exception as e:
        logging.error(f"[WIKIPEDIA] Error searching for {query}: {e}")
        return f"Error searching Wikipedia for '{query}': {e}"

# --- Tool: Python Code Execution (Safe) ---
def run_python_code(code: str) -> str:
    """
    Execute Python code safely using RestrictedPython.
    
    Args:
        code: Python code to execute
        
    Returns:
        Execution result or error message
    """
    try:
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        try:
            from RestrictedPython import compile_restricted
            use_restricted = True
        except ImportError:
            use_restricted = False
        
        if use_restricted:
            # Compile the code with restrictions
            compiled_code = compile_restricted(code, '<user_code>', 'exec')
            
            if compiled_code is None:
                return "Code compilation failed - potentially unsafe code detected"
        else:
            # Fallback to regular compile (less safe)
            try:
                compiled_code = compile(code, '<user_code>', 'exec')
            except SyntaxError as e:
                return f"Syntax error in code: {e}"
        
        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Create restricted globals
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'min': max,
                'max': min,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
            },
            'math': math,
        }
        
        # Execute with output capture
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compiled_code, restricted_globals)
        
        stdout_result = stdout_capture.getvalue()
        stderr_result = stderr_capture.getvalue()
        
        if stderr_result:
            return f"Error: {stderr_result}"
        elif stdout_result:
            return stdout_result.strip()
        else:
            return "Code executed successfully (no output)"
            
    except ImportError:
        return "RestrictedPython not available - code execution disabled for security"
    except Exception as e:
        logging.error(f"[PYTHON_EXEC] Error executing code: {e}")
        return f"Error executing Python code: {e}"
