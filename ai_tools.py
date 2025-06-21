# ai_tools.py: Real-time tools for LLM augmentation (time, weather, math, etc.)


import io

# --- Tool: Time & Date ---
import logging
import math
import os
import platform
import re
import urllib.parse
from contextlib import redirect_stderr
from contextlib import redirect_stdout
from datetime import datetime
from typing import List
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
import wikipedia
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from RestrictedPython import compile_restricted


def get_current_time(timezone: Optional[str] = None) -> str:
    try:
        if timezone:

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
        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            data = resp.json()
        logging.debug(f"[WeatherAPI] Response: {data}")
        if resp.status_code != 200 or "error" in data:
            return f"WeatherAPI.com error: {data.get('error', {}).get('message', 'Unknown error')}"
        c = data["current"]
        loc = data["location"]
        return (
            f"Weather in {loc['name']}, {loc['country']}: {c['temp_c']}°C, "
            f"{c['condition']['text']}, wind {c['wind_kph']} kph, humidity {c['humidity']}%"
        )
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
        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}")
            geo = geo_resp.json()
        logging.debug(f"[WeatherTool] Open-Meteo geo response: {geo}")
        if not geo.get("results"):
            return f"Could not find city: {city}"
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        with httpx.Client(timeout=10) as client:
            weather_resp = client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            )
            weather = weather_resp.json()
        logging.debug(f"[WeatherTool] Open-Meteo weather response: {weather}")
        w = weather.get("current_weather", {})
        return f"Weather in {city}: {w.get('temperature', '?')}°C, wind {w.get('windspeed', '?')} km/h, code {w.get('weathercode', '?')}"
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
            separators=["\n\n", "\n", " ", ""],
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
            ("km", "m"): 1000,
            ("m", "km"): 0.001,
            ("m", "cm"): 100,
            ("cm", "m"): 0.01,
            ("m", "mm"): 1000,
            ("mm", "m"): 0.001,
            ("ft", "m"): 0.3048,
            ("m", "ft"): 3.28084,
            ("in", "cm"): 2.54,
            ("cm", "in"): 0.393701,
            ("mile", "km"): 1.60934,
            ("km", "mile"): 0.621371,
        }

        # Weight conversions
        weight_conversions = {
            ("kg", "g"): 1000,
            ("g", "kg"): 0.001,
            ("kg", "lb"): 2.20462,
            ("lb", "kg"): 0.453592,
            ("g", "oz"): 0.035274,
            ("oz", "g"): 28.3495,
        }

        # Temperature conversions (special handling)
        if from_unit in ["celsius", "c"] and to_unit in ["fahrenheit", "f"]:
            result = (value * 9 / 5) + 32
            return f"{value}°C = {result:.2f}°F"
        elif from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
            result = (value - 32) * 5 / 9
            return f"{value}°F = {result:.2f}°C"
        elif from_unit in ["celsius", "c"] and to_unit in ["kelvin", "k"]:
            result = value + 273.15
            return f"{value}°C = {result:.2f}K"
        elif from_unit in ["kelvin", "k"] and to_unit in ["celsius", "c"]:
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
        location_clean = location.strip().lower().replace(" ", "-")

        # Map some common locations to timeanddate.com format
        location_mappings = {
            "netherlands": "netherlands/amsterdam",
            "amsterdam": "netherlands/amsterdam",
            "london": "uk/london",
            "new-york": "usa/new-york",
            "tokyo": "japan/tokyo",
            "paris": "france/paris",
            "berlin": "germany/berlin",
            "moscow": "russia/moscow",
            "sydney": "australia/sydney",
        }

        location_url = location_mappings.get(location_clean, f"world/{location_clean}")
        url = f"https://www.timeanddate.com/worldclock/{location_url}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        # Parse HTML to extract time
        soup = BeautifulSoup(response.content, "html.parser")

        # Look for time elements (timeanddate.com uses specific IDs/classes)
        time_element = soup.find("span", {"id": "ct"}) or soup.find("span", class_="h1")

        if time_element:
            current_time = time_element.get_text().strip()
            return f"Current time in {location}: {current_time} (via timeanddate.com)"
        else:
            # Fallback: look for any time-like text
            time_patterns = [
                r"\d{1,2}:\d{2}:\d{2}",
                r"\d{1,2}:\d{2}\s*(AM|PM)",
            ]

            page_text = soup.get_text()
            for pattern in time_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    return "Current time in {location}: {matches[0]} (via timeanddate.com)"

            return "Could not extract time for {location} from timeanddate.com"

    except httpx.RequestError:
        logging.error("[TIMEANDDATE] Network error for {location}: {e}")
        return "Network error getting time for {location}: {e}"
    except Exception:
        logging.error("[TIMEANDDATE] Error getting time for {location}: {e}")
        return "Error getting time for {location}: {e}"


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
        except Exception:
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

        try:

            use_restricted = True
        except ImportError:
            use_restricted = False

        if use_restricted:
            # Compile the code with restrictions
            compiled_code = compile_restricted(code, "<user_code>", "exec")

            if compiled_code is None:
                return "Code compilation failed - potentially unsafe code detected"
        else:
            # Fallback to regular compile (less safe)
            try:
                compiled_code = compile(code, "<user_code>", "exec")
            except SyntaxError as e:
                return f"Syntax error in code: {e}"

        # Capture output
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Create restricted globals
        restricted_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sum": sum,
                "min": max,
                "max": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "any": any,
                "all": all,
            },
            "math": math,
        }

        # Execute with output capture
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compiled_code, restricted_globals)

        stdout_result = stdout_capture.getvalue()
        stderr_result = stderr_capture.getvalue()

        if stderr_result:
            return "Error: {stderr_result}"
        elif stdout_result:
            return stdout_result.strip()
        else:
            return "Code executed successfully (no output)"

    except ImportError:
        return "RestrictedPython not available - code execution disabled for security"
    except Exception:
        logging.error("[PYTHON_EXEC] Error executing code: {e}")
        return "Error executing Python code: {e}"


def calculate(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.

    Args:
        expression: Mathematical expression as string (e.g., "2 + 2 * 3")

    Returns:
        Result of the calculation or error message
    """
    try:
        # Remove any potentially dangerous characters
        expression = expression.replace(" ", "")

        # Only allow numbers, operators, parentheses, and decimal points
        allowed_chars = set("0123456789+-*/().^%")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"

        # Replace ^ with ** for Python exponentiation
        expression = expression.replace("^", "**")

        # Safe evaluation
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)

    except Exception:
        return "Calculation error: {str(e)}"


def web_search(query: str, num_results: int = 5) -> str:
    """
    Perform a web search and return results.

    Args:
        query: Search query
        num_results: Number of results to return

    Returns:
        Search results or error message"""
    try:

        # Use DuckDuckGo Instant Answer API as a simple search
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
                Chrome/91.0.4472.124 Safari/537.36"
        }

        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=headers)
            data = response.json()

        if data.get("AbstractText"):
            return "Search result for '{query}': {data['AbstractText']}"
        elif data.get("Definition"):
            return "Definition for '{query}': {data['Definition']}"
        else:
            return "No detailed results found for '{query}'. Try a more specific search."

    except Exception:
        return "Web search unavailable: {str(e)}"


def get_news(category: str = "general", country: str = "us") -> str:
    """
    Get latest news headlines.

    Args:
        category: News category (general, business, tech, etc.)
        country: Country code (us, uk, etc.)

    Returns:
        News headlines or error message
    """
    try:
        # For demo purposes, return a placeholder
        # In production, you would integrate with a news API like NewsAPI
        return "News lookup is currently unavailable. Would you like me to search the web for '{category}' news instead?"

    except Exception:
        return "News service error: {str(e)}"


def get_exchange_rate(from_currency: str, to_currency: str, amount: float = 1.0) -> str:
    """
    Get currency exchange rates.

    Args:
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
        amount: Amount to convert
          Returns:
        Exchange rate information or error message
    """
    try:        # Use a free exchange rate API
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
            data = response.json()

        if to_currency.upper() in data["rates"]:
            rate = data["rates"][to_currency.upper()]
            converted_amount = amount * rate
            return f"{amount} {from_currency.upper()} = {converted_amount:.2f} {to_currency.upper()} (Rate: {rate:.4f})"
        else:
            return f"Currency {to_currency.upper()} not found"

    except Exception as e:
        return f"Exchange rate lookup failed: {str(e)}"


def get_system_info() -> str:
    """
    Get system information.

    Returns:
        System information or error message
    """
    try:

        info = {
            "OS": platform.system(),
            "OS Version": platform.release(),
            "Architecture": platform.architecture()[0],
            "Python Version": platform.python_version(),
            "Hostname": platform.node(),
        }

        return "System Information: " + ", ".join(["{k}: {v}" for k, v in info.items()])

    except Exception:
        return "System info unavailable: {str(e)}"


def get_timezone_for_location(location: str) -> str:
    """
    Get timezone information for a location.

    Args:
        location: Location name or city

    Returns:
        Timezone information or error message
    """
    try:
        # This would typically use a timezone API
        # For now, return a placeholder that calls the time function
        return get_time_from_timeanddate(location)

    except Exception:
        return "Timezone lookup failed: {str(e)}"
