#!/usr/bin/env python3
"""
AI Tools Demonstration
Shows the real-time tools available to the LLM system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_tools import get_current_time, get_weather, calculate, convert_units, wikipedia_search, web_search, run_python_code, get_system_info
import json

def main():
    print('🔧 AI Tools Real-time Demonstration')
    print('=' * 60)
    
    print('\n🕐 Time & Date Service:')
    print(f'   Current time: {get_current_time()}')
    try:
        print(f'   Tokyo time: {get_current_time("Asia/Tokyo")}')
    except Exception as e:
        print(f'   Tokyo time: Error - {str(e)}')
    
    print('\n🌤️ Weather Service:')
    try:
        london_weather = get_weather("London")
        print(f'   London: {london_weather}')
        
        tokyo_weather = get_weather("Tokyo")
        print(f'   Tokyo: {tokyo_weather}')
    except Exception as e:
        print(f'   Weather service: {str(e)}')
    
    print('\n🧮 Mathematical Calculator:')
    calculations = [
        "2 + 3 * 4",
        "sqrt(16)",
        "sin(pi/2)",
        "log(100)",
        "2**10"
    ]
    
    for calc in calculations:
        try:
            result = calculate(calc)
            print(f'   {calc} = {result}')
        except Exception as e:
            print(f'   {calc} = Error: {str(e)}')    
    print('\n🔄 Unit Conversion Service:')
    conversions = [
        (25, "celsius", "fahrenheit"),
        (10, "km", "miles"),
        (100, "meters", "feet"),
        (1, "kg", "pounds")
    ]
    
    for value, from_unit, to_unit in conversions:
        try:
            result = convert_units(value, from_unit, to_unit)
            print(f'   {value} {from_unit} = {result}')
        except Exception as e:
            print(f'   {value} {from_unit} to {to_unit} = Error: {str(e)}')
    
    print('\n📚 Wikipedia Search:')
    try:
        wiki_result = wikipedia_search("Python programming language", 2)
        print(f'   Python info: {wiki_result[:100]}...')
    except Exception as e:
        print(f'   Wikipedia search: Error - {str(e)}')
    
    print('\n🐍 Python Code Execution:')
    try:
        code_result = run_python_code('print("Hello from embedded Python!"); result = 5 * 5; print(f"5 x 5 = {result}")')
        print(f'   Code output: {code_result}')
    except Exception as e:
        print(f'   Python execution: Error - {str(e)}')
    
    print('\n💻 System Information:')
    try:
        sys_info = get_system_info()
        print(f'   System: {sys_info[:150]}...')
    except Exception as e:
        print(f'   System info: Error - {str(e)}')
    
    print('\n✅ AI Tools demonstration completed!')
    print('   These tools are available to the LLM for real-time assistance')

if __name__ == "__main__":
    main()
