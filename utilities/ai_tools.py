# ai_tools.py: Real-time tools for LLM augmentation (time, weather, math, etc.)


import io

# --- Tool: Time & Date ---
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

from core.unified_logging import get_logger, log_service_status

logger = get_logger(__name__)
import wikipedia
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from RestrictedPython import compile_restricted
import ast


def get_current_time(timezone: Optional[str] = None) -> str:
    """TODO: Add proper docstring for get_current_time."""
    try:
        if timezone:
            now = datetime.now(ZoneInfo(timezone))
        else:
            now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        log_service_status("AI_TOOLS", "error", f"Error getting current time: {e}")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Tool: Weather (Open-Meteo, no API key required) ---
def get_weather_weatherapi(city: str = "London") -> str:
    """TODO: Add proper docstring for get_weather_weatherapi."""
    api_key = os.getenv("WEATHERAPI_KEY", "")
    if not api_key:
        logger.warning("[WeatherAPI] API key not set.")
        return "WeatherAPI.com API key not set."
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        logger.debug(f"[WeatherAPI] Requesting: {url}")
        with httpx.Client(timeout=10) as client:
            resp = client.get(url)
            data = resp.json()
        logger.debug(f"[WeatherAPI] Response: {data}")
        if resp.status_code != 200 or "error" in data:
            return f"WeatherAPI.com error: {data.get('error', {}).get('message', 'Unknown error')}"
        c = data["current"]
        loc = data["location"]
        return (
            f"Weather in {loc['name']}, {loc['country']}: {c['temp_c']}C, "
            f"{c['condition']['text']}, wind {c['wind_kph']} kph, humidity {c['humidity']}%"
        )
    except Exception as e:
        logger.error(f"[WeatherAPI] Exception: {e}")
        return f"WeatherAPI.com lookup failed: {e}"


# --- Tool: Weather (Multi-provider: KNMI, WeatherAPI.com, Open-Meteo) ---
async def get_weather(city: str = "London") -> str:
    """
    Get weather information using multiple providers in priority order:
    1. Universal Weather Tool (for all locations, uses KNMI for Netherlands)
    2. WeatherAPI.com (if API key available)
    3. Open-Meteo (fallback)
    
    Args:
        city: City name to get weather for
        
    Returns:
        Formatted weather information string
    """
    
    # First try the universal weather tool (handles both Netherlands and international)
    try:
        logger.info(f"[WeatherTool] Using universal weather tool for: {city}")
        from tools.weather_tool import Action
        weather_action = Action()
        result = await weather_action.run(city, include_forecast=False)
        if result and not result.startswith("Error") and not result.startswith("Unable") and not result.startswith("❌"):
            return result
        logger.warning(f"[WeatherTool] Universal weather tool failed for {city}, falling back to other providers")
    except Exception as e:
        logger.error(f"[WeatherTool] Universal weather tool error for {city}: {e}")
    
    # Try WeatherAPI.com if API key is available
    api_key = os.getenv("WEATHERAPI_KEY", "")
    logger.debug(f"[WeatherTool] WEATHERAPI_KEY set: {bool(api_key)}")
    if api_key:
        result = get_weather_weatherapi(city)
        logger.debug(f"[WeatherTool] WeatherAPI.com result: {result}")
        if result and not result.startswith("WeatherAPI.com API key not set"):
            return result

    # Fallback to Open-Meteo
    try:
        logger.info(f"[WeatherTool] Falling back to Open-Meteo for city: {city}")
        with httpx.Client(timeout=10) as client:
            geo_resp = client.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}")
            geo = geo_resp.json()
        logger.debug(f"[WeatherTool] Open-Meteo geo response: {geo}")
        if not geo.get("results"):
            return f"Could not find city: {city}"
        lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
        with httpx.Client(timeout=10) as client:
            weather_resp = client.get(
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            )
            weather = weather_resp.json()
        logger.debug(f"[WeatherTool] Open-Meteo weather response: {weather}")
        w = weather.get("current_weather", {})
        return f"Weather in {city}: {w.get('temperature', '?')}C, wind {w.get('windspeed', '?')} km/h, code {w.get('weathercode', '?')}"
    except Exception as e:
        logger.error(f"[WeatherTool] Error fetching weather for {city}: {e}")
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
            separators=["\n\n", "\n", " ", ""])
        chunks = text_splitter.split_text(text)
        logger.debug(f"[CHUNKING] Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
    except Exception as e:
        logger.error(f"[CHUNKING] Error chunking text: {e}")
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
        # Normalize unit names to lowercase and handle variations
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()

        # Handle common variations
        unit_variations = {
            "kilometers": "km",
            "kilometer": "km",
            "metres": "m",
            "meters": "m",
            "meter": "m",
            "miles": "mile",
            "pounds": "lb",
            "pound": "lb",
            "kilograms": "kg",
            "kilogram": "kg",
            "grams": "g",
            "gram": "g",
            "celsius": "c",
            "fahrenheit": "f",
            "kelvin": "k",
        }

        from_unit = unit_variations.get(from_unit, from_unit)
        to_unit = unit_variations.get(to_unit, to_unit)

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
            ("miles", "km"): 1.60934,
            ("km", "miles"): 0.621371,
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
            return f"{value}C = {result:.2f}F"
        elif from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
            result = (value - 32) * 5 / 9
            return f"{value}F = {result:.2f}C"
        elif from_unit in ["celsius", "c"] and to_unit in ["kelvin", "k"]:
            result = value + 273.15
            return f"{value}C = {result:.2f}K"
        elif from_unit in ["kelvin", "k"] and to_unit in ["celsius", "c"]:
            result = value - 273.15
            return f"{value}K = {result:.2f}C"

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
        logger.error(f"[CONVERSION] Error converting {value} {from_unit} to {to_unit}: {e}")
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
                    return f"Current time in {location}: {matches[0]} (via timeanddate.com)"

            return f"Could not extract time for {location} from timeanddate.com"

    except httpx.RequestError as e:
        logger.error(f"[TIMEANDDATE] Network error for {location}: {e}")
        return f"Network error getting time for {location}: {e}"
    except Exception as e:
        logger.error(f"[TIMEANDDATE] Error getting time for {location}: {e}")
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
        except Exception:
            return f"Multiple results found for '{query}'. Be more specific."
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for '{query}'"
    except Exception as e:
        logger.error(f"[WIKIPEDIA] Error searching for {query}: {e}")
        return f"Error searching Wikipedia for '{query}': {e}"


def run_python_code(code: str) -> str:
    """
    Execute Python code safely using RestrictedPython.

    Args:
        code: Python code to execute

    Returns:
        Execution result or error message
    """
    try:
        # If RestrictedPython is importable above, use it; else fallback handled by except ImportError below
        use_restricted = True

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
                "min": min,
                "max": max,
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
            return f"Error: {stderr_result}"
        elif stdout_result:
            return stdout_result.strip()
        else:
            return "Code executed successfully (no output)"

    except ImportError:
        return "RestrictedPython not available - code execution disabled for security"
    except Exception as e:
        logger.error(f"[PYTHON_EXEC] Error executing code: {e}")
        return f"Error executing Python code: {e}"
def calculate(expression: str) -> str:
    """
    Safely evaluate mathematical expressions.

    Args:
        expression: Mathematical expression as string (e.g., "2 + 2 * 3")

    Returns:
        Result of the calculation or error message
    """
    try:
        # Replace ^ with ** for exponentiation and strip whitespace
        expr = expression.replace("^", "**").strip()

        # Parse expression into AST and only allow safe nodes
        tree = ast.parse(expr, mode="eval")

        allowed_nodes = (
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd, ast.FloorDiv, ast.LShift, ast.RShift,
            ast.BitOr, ast.BitAnd, ast.BitXor, ast.MatMult,  # optionally allow bitwise
            ast.Call, ast.Name, ast.Load, ast.Tuple
        )

        allowed_names = {"pi": math.pi, "e": math.e}

        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                return "Error: Invalid expression"
            if isinstance(node, ast.Call):
                return "Error: Function calls are not allowed"
            if isinstance(node, ast.Name) and node.id not in allowed_names:
                return "Error: Unknown identifier"

        def _eval(n):
            if isinstance(n, ast.Expression):
                return _eval(n.body)
            if isinstance(n, ast.Constant):
                if isinstance(n.value, (int, float)):
                    return n.value
                raise ValueError("Invalid constant")
            if isinstance(n, ast.Num):
                return n.n
            if isinstance(n, ast.BinOp):
                left, right = _eval(n.left), _eval(n.right)
                if isinstance(n.op, ast.Add):
                    return left + right
                if isinstance(n.op, ast.Sub):
                    return left - right
                if isinstance(n.op, ast.Mult):
                    return left * right
                if isinstance(n.op, ast.Div):
                    return left / right
                if isinstance(n.op, ast.FloorDiv):
                    return left // right
                if isinstance(n.op, ast.Mod):
                    return left % right
                if isinstance(n.op, ast.Pow):
                    return left ** right
                if isinstance(n.op, ast.BitAnd):
                    return int(left) & int(right)
                if isinstance(n.op, ast.BitOr):
                    return int(left) | int(right)
                if isinstance(n.op, ast.BitXor):
                    return int(left) ^ int(right)
                raise ValueError("Unsupported operator")
            if isinstance(n, ast.UnaryOp):
                operand = _eval(n.operand)
                if isinstance(n.op, ast.UAdd):
                    return +operand
                if isinstance(n.op, ast.USub):
                    return -operand
                raise ValueError("Unsupported unary operator")
            if isinstance(n, ast.Name):
                return allowed_names[n.id]
            if isinstance(n, ast.Tuple):
                return tuple(_eval(elt) for elt in n.elts)
            raise ValueError("Unsupported expression")

        result = _eval(tree)
        return str(result)

    except Exception as e:
        return f"Calculation error: {str(e)}"


def web_search(query: str, num_results: int = 5) -> str:
    """Lightweight synchronous web search (DuckDuckGo Instant Answer API).

    NOTE:
        Advanced, structured async search is provided by utilities.enhanced_web_search.
        This function remains synchronous so ToolService can call it from non-async
        contexts without event loop conflicts.
    """
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
            data = resp.json()
        if data.get("AbstractText"):
            return f"Search result for '{query}': {data['AbstractText']}"
        if data.get("Definition"):
            return f"Definition for '{query}': {data['Definition']}"
        return f"No detailed results found for '{query}'. Try a more specific search."
    except Exception as e:
        return f"Web search unavailable: {e}"


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
        return (
            f"News lookup is currently unavailable. Would you like me to search the web for '{category}' news instead?"
        )

    except Exception as e:
        return f"News service error: {str(e)}"


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
    try:  # Use a free exchange rate API
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


# Removed KNMI-specific functions - now using universal weather tool



# Removed KNMI-specific functions - now using universal weather tool


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
        
        return "System Information: " + ", ".join([f"{k}: {v}" for k, v in info.items()])
    
    except Exception as e:
        return f"System info unavailable: {str(e)}"


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

    except Exception as e:
        return f"Timezone lookup failed: {str(e)}"
