"""
Integration Enhancement Module
Improves how the web search system integrates with other OpenWebUI components
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

class OpenWebUIIntegration:
    """Enhanced integration with OpenWebUI features"""
    
    @staticmethod
    def extract_search_intent(user_message: str) -> Optional[Dict[str, Any]]:
        """
        Analyze user message to determine if web search is needed
        Returns search parameters if search is recommended
        """
        search_triggers = [
            r'(?i)what.*(happening|news|latest|current|today|recent)',
            r'(?i)(search|find|look up|tell me about).*(latest|current|recent|today)',
            r'(?i)(latest|recent|current|today).*(news|information|updates|developments)',
            r'(?i)what.*(price|cost|stock|market)',
            r'(?i)(weather|forecast)',
            r'(?i)(breaking|trending|viral)',
            r'(?i)\b(2025|august|july|september)\b.*\b(news|updates|announcements)',
        ]
        
        for pattern in search_triggers:
            if re.search(pattern, user_message):
                # Extract potential search query
                query = OpenWebUIIntegration._extract_query_from_message(user_message)
                return {
                    "recommended": True,
                    "confidence": 0.8,
                    "extracted_query": query,
                    "trigger_pattern": pattern
                }
        
        return None
    
    @staticmethod
    def _extract_query_from_message(message: str) -> str:
        """Extract the core search query from a user message"""
        # Remove common question words and focus on the subject
        query = re.sub(r'(?i)\b(what|how|when|where|why|who|can|could|would|should|tell me|find|search for|look up)\b', '', message)
        query = re.sub(r'[?!.]', '', query)
        query = query.strip()
        
        # Limit to reasonable length
        words = query.split()
        if len(words) > 8:
            query = ' '.join(words[:8])
        
        return query
    
    @staticmethod
    def format_for_chat_context(search_results: str, user_query: str) -> str:
        """
        Format search results for optimal chat context injection
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        formatted = f"""[CURRENT WEB SEARCH RESULTS - {timestamp}]
User asked: "{user_query}"

{search_results}

[END WEB SEARCH RESULTS]

Instructions: Use the above current web search results to provide an accurate, up-to-date response to the user's question. Cite specific sources when possible."""
        
        return formatted
    
    @staticmethod
    def extract_cited_sources(response: str) -> List[str]:
        """Extract URLs that were cited in a model response"""
        url_pattern = r'https?://[^\s<>"\{\}|\\^`\[\]]+'
        urls = re.findall(url_pattern, response)
        return list(set(urls))  # Remove duplicates
    
    @staticmethod
    def generate_suggested_followups(search_results: str, original_query: str) -> List[str]:
        """Generate relevant follow-up questions based on search results"""
        followups = []
        
        # Extract key topics from search results
        titles = re.findall(r'\*\*\d+\. ([^*]+)\*\*', search_results)
        
        if titles:
            # Generate follow-ups based on found topics
            if len(titles) >= 2:
                followups.append(f"What are the differences between {titles[0][:50]}... and {titles[1][:50]}...?")
            
            followups.append(f"Can you explain more about {titles[0][:60]}...?")
            
            if "2025" in search_results:
                followups.append("What are the expected developments in this area for the rest of 2025?")
            
            if any(word in search_results.lower() for word in ['price', 'cost', 'stock', 'market']):
                followups.append("What factors are influencing these market changes?")
        
        # Generic relevant follow-ups
        followups.extend([
            f"What are the latest trends related to {original_query}?",
            f"Who are the key players or companies involved in {original_query}?",
            "What should I know about recent developments in this area?"
        ])
        
        return followups[:3]  # Limit to 3 suggestions

class PerformanceOptimizer:
    """Performance optimization utilities"""
    
    @staticmethod
    def optimize_query(query: str) -> str:
        """Optimize search query for better results"""
        # Remove stop words that don't add search value
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'}
        
        words = query.lower().split()
        optimized_words = []
        
        for word in words:
            # Keep important words even if they're in stop_words for search context
            if len(word) > 2 and (word not in stop_words or word in ['has', 'was', 'are', 'new', 'can']):
                optimized_words.append(word)
        
        # Add relevant context terms
        if any(word in optimized_words for word in ['ai', 'artificial', 'intelligence']):
            if '2025' not in query:
                optimized_words.append('2025')
        
        return ' '.join(optimized_words)
    
    @staticmethod
    def should_use_cache(query: str, user_context: Dict = None) -> bool:
        """Determine if caching should be used for this query"""
        # Don't cache time-sensitive queries
        time_sensitive_keywords = ['now', 'today', 'current', 'live', 'breaking', 'just', 'minutes', 'hours']
        
        if any(keyword in query.lower() for keyword in time_sensitive_keywords):
            return False
        
        # Always cache general information queries
        return True
    
    @staticmethod
    def estimate_freshness_requirement(query: str) -> int:
        """Estimate how fresh the results need to be (in minutes)"""
        if any(word in query.lower() for word in ['breaking', 'live', 'now', 'just happened']):
            return 5  # Very fresh
        elif any(word in query.lower() for word in ['today', 'latest', 'current']):
            return 60  # Within last hour
        elif any(word in query.lower() for word in ['recent', 'new', 'updated']):
            return 1440  # Within last day
        else:
            return 7200  # Within last 5 days

class SearchAnalytics:
    """Analytics and monitoring for search performance"""
    
    search_stats = {
        'total_searches': 0,
        'cache_hits': 0,
        'avg_response_time': 0,
        'popular_queries': {},
        'error_count': 0
    }
    
    @classmethod
    def record_search(cls, query: str, response_time: float, cached: bool = False, error: bool = False):
        """Record search statistics"""
        cls.search_stats['total_searches'] += 1
        
        if cached:
            cls.search_stats['cache_hits'] += 1
        
        if error:
            cls.search_stats['error_count'] += 1
        
        # Update average response time
        current_avg = cls.search_stats['avg_response_time']
        total = cls.search_stats['total_searches']
        cls.search_stats['avg_response_time'] = (current_avg * (total - 1) + response_time) / total
        
        # Track popular queries
        if query in cls.search_stats['popular_queries']:
            cls.search_stats['popular_queries'][query] += 1
        else:
            cls.search_stats['popular_queries'][query] = 1
    
    @classmethod
    def get_performance_summary(cls) -> str:
        """Get a formatted performance summary"""
        stats = cls.search_stats
        cache_rate = (stats['cache_hits'] / max(stats['total_searches'], 1)) * 100
        error_rate = (stats['error_count'] / max(stats['total_searches'], 1)) * 100
        
        # Get top 3 popular queries
        popular = sorted(stats['popular_queries'].items(), key=lambda x: x[1], reverse=True)[:3]
        
        summary = f"""📊 Search Performance Summary:
• Total searches: {stats['total_searches']}
• Cache hit rate: {cache_rate:.1f}%
• Average response time: {stats['avg_response_time']:.2f}s
• Error rate: {error_rate:.1f}%
• Popular queries: {', '.join([f'"{q}" ({c})' for q, c in popular])}"""
        
        return summary

print("[Integration] OpenWebUI Integration Enhancement Module Loaded")
