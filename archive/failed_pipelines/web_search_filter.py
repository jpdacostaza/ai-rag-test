"""
title: Real-time Web Search
author: open-webui
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 1.0.0
license: MIT
requirements: httpx
"""

import asyncio
import httpx
import json
from datetime import datetime
from urllib.parse import quote_plus
from typing import Optional
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        # List target pipeline ids (models) that this filter will be applied to.
        # If you want to apply this filter to all pipelines, you can set pipelines to ["*"]
        pipelines: list[str] = Field(default=["*"], description="Pipeline IDs")
        
        # Assign a priority level to the filter pipeline.
        # The priority level determines the order in which the filter pipelines are executed.
        # The lower the number, the higher the priority.
        priority: int = Field(default=0, description="Priority level")

    def __init__(self):
        # Pipeline filters are only compatible with Open WebUI
        # You can think of filter pipeline as a middleware that can be used to edit the form data before it is sent to the OpenAI API.
        self.type = "filter"
        
        # Optionally, you can set the id and name of the pipeline.
        # Best practice is to not specify the id so that it can be automatically inferred from the filename, in this case "function_calling_filter".
        self.name = "Real-time Web Search"
        
        # Initialize the valves
        self.valves = self.Valves()

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This filter is applied to the form data before it is sent to the OpenAI API.
        print(f"inlet:{__name__}")
        
        messages = body.get("messages", [])
        if not messages:
            return body
            
        last_message = messages[-1].get("content", "")
        
        # Check for web search keywords
        search_triggers = [
            "current weather", "latest news", "today's", "recent", "what's happening",
            "search the web", "find current", "real-time", "up to date", "current information"
        ]
        
        should_search = any(trigger in last_message.lower() for trigger in search_triggers)
        
        if should_search:
            print(f"🔍 Web search triggered for: {last_message}")
            
            try:
                # Perform web search
                search_results = await self.search_web(last_message)
                
                # Enhance the user's message with search results
                enhanced_content = f"{last_message}\n\n[CURRENT WEB SEARCH RESULTS]:\n{search_results}"
                messages[-1]["content"] = enhanced_content
                body["messages"] = messages
                
                print(f"✅ Enhanced message with web search results")
                
            except Exception as e:
                print(f"❌ Web search failed: {e}")
                # Add a note about search failure
                enhanced_content = f"{last_message}\n\n[NOTE: Web search attempted but failed. Providing response based on available knowledge. Today's date is {datetime.now().strftime('%B %d, %Y')}]"
                messages[-1]["content"] = enhanced_content
                body["messages"] = messages
        
        return body

    async def search_web(self, query: str) -> str:
        """Perform web search and return formatted results."""
        
        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Extract search terms
            search_query = query.lower()
            if "weather" in search_query:
                if "netherlands" in search_query or "holland" in search_query:
                    search_query = "current weather Netherlands today"
                elif "paris" in search_query:
                    search_query = "current weather Paris today"
                else:
                    search_query = f"current weather {query} today"
            elif "news" in search_query:
                search_query = f"latest news headlines {datetime.now().strftime('%Y')}"
            else:
                search_query = f"{query} {datetime.now().year}"
            
            # Use DuckDuckGo instant answer API with current date
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(search_query)}&format=json&no_html=1&skip_disambig=1"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url)
                data = response.json()
                
                results = []
                
                # Get abstract info
                if data.get("Abstract"):
                    results.append(f"📋 **{data.get('Heading', 'Information')}**")
                    results.append(f"{data.get('Abstract')}")
                    if data.get("AbstractURL"):
                        results.append(f"🔗 Source: {data.get('AbstractURL')}")
                
                # Get direct answer
                if data.get("Answer"):
                    results.append(f"💡 **Direct Answer**: {data.get('Answer')}")
                
                # Get related topics
                if data.get("RelatedTopics"):
                    related = data.get("RelatedTopics", [])[:3]
                    for i, topic in enumerate(related):
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append(f"📄 **Related {i+1}**: {topic.get('Text')[:200]}...")
                            if topic.get("FirstURL"):
                                results.append(f"🔗 {topic.get('FirstURL')}")
                
                if results:
                    formatted_results = f"🌐 **Real-time Web Search Results** (searched on {current_date}):\n\n"
                    formatted_results += "\n\n".join(results)
                    formatted_results += f"\n\n---\n*Search performed on {current_date} using DuckDuckGo*"
                    return formatted_results
                else:
                    return f"🔍 **Web search performed** but no specific results found for '{query}'. This may indicate the query is very specific or the information is not readily available in search engine instant answers. Current date: {current_date}"
                    
        except Exception as e:
            return f"❌ **Web search error**: {str(e)}. Current date: {datetime.now().strftime('%B %d, %Y')}"

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        # This filter is applied to the response before it is returned to the user.
        print(f"outlet:{__name__}")
        return body
