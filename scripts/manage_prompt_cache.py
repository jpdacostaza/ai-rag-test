#!/usr/bin/env python3
"""
Prompt Caching Management Script
===============================

Provides command-line interface for managing advanced prompt caching system.
Includes cache optimization, performance monitoring, and maintenance operations.

Usage:
    python scripts/manage_prompt_cache.py --help
    python scripts/manage_prompt_cache.py stats
    python scripts/manage_prompt_cache.py optimize
    python scripts/manage_prompt_cache.py clear --type conversation
"""

import argparse
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.prompt_cache_service import prompt_cache_service
from services.enhanced_llm_service import enhanced_llm_service
from core.unified_logging import get_logger

logger = get_logger(__name__)


class PromptCacheManager:
    """Command-line management interface for prompt caching system."""
    
    def __init__(self):
        self.cache_service = prompt_cache_service
        self.llm_service = enhanced_llm_service
    
    async def show_stats(self, detailed: bool = False):
        """Display cache statistics and performance metrics."""
        print("🚀 Advanced Prompt Caching System - Statistics")
        print("=" * 50)
        
        try:
            stats = await self.llm_service.get_cache_statistics()
            
            # Basic metrics
            print(f"📊 Cache Performance:")
            print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
            print(f"   Total Hits: {stats['total_hits']:,}")
            print(f"   Total Misses: {stats['total_misses']:,}")
            print(f"   Memory Cache Size: {stats['memory_cache_size']:,} entries")
            
            if stats['redis_cache_size'] >= 0:
                print(f"   Redis Cache Size: {stats['redis_cache_size']:,} entries")
            else:
                print(f"   Redis Cache: Not available")
            
            # Provider availability
            print(f"\n🔗 Provider Availability:")
            providers = stats.get('providers', {})
            print(f"   Anthropic: {'✅ Available' if providers.get('anthropic_available') else '❌ Not configured'}")
            print(f"   OpenAI: {'✅ Available' if providers.get('openai_available') else '❌ Not configured'}")
            print(f"   Ollama: {'✅ Available' if providers.get('ollama_available') else '❌ Not available'}")
            
            # Token metrics
            print(f"\n🎯 Token Metrics:")
            print(f"   Cache Creation Tokens: {stats['cache_creation_tokens']:,}")
            print(f"   Cache Read Tokens: {stats['cache_read_tokens']:,}")
            print(f"   Estimated Cost Saved: ${stats['estimated_cost_saved']:.2f}")
            
            # Optimization recommendations
            recommendations = stats.get('optimization_recommendations', [])
            if recommendations:
                print(f"\n💡 Optimization Recommendations:")
                for rec in recommendations:
                    print(f"   • {rec}")
            else:
                print(f"\n✅ Cache performance is optimal")
            
            if detailed:
                print(f"\n⚙️ Configuration:")
                config = stats.get('config', {})
                for key, value in config.items():
                    print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ Error retrieving statistics: {e}")
            logger.error(f"Stats error: {e}")
    
    async def optimize_cache(self):
        """Perform cache optimization and cleanup."""
        print("🔧 Optimizing Prompt Cache System...")
        print("=" * 40)
        
        try:
            # Perform optimization
            await self.cache_service.optimize_cache_performance()
            
            # Get updated stats
            stats = self.cache_service.get_cache_stats()
            
            print(f"✅ Optimization completed!")
            print(f"   Current Hit Rate: {stats['hit_rate']:.1f}%")
            print(f"   Evictions Performed: {stats.get('evictions', 0)}")
            print(f"   Memory Cache Size: {stats['memory_cache_size']} entries")
            
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            logger.error(f"Optimization error: {e}")
    
    async def clear_cache(self, cache_type: str = None):
        """Clear cache entries, optionally filtered by type."""
        if cache_type:
            print(f"🗑️ Clearing cache entries of type: {cache_type}")
        else:
            print("🗑️ Clearing all cache entries...")
        
        try:
            cleared_count = await self.cache_service.clear_cache(cache_type)
            print(f"✅ Cleared {cleared_count} cache entries")
            
        except Exception as e:
            print(f"❌ Cache clear failed: {e}")
            logger.error(f"Clear cache error: {e}")
    
    async def test_caching(self):
        """Test caching functionality with sample queries."""
        print("🧪 Testing Prompt Caching System...")
        print("=" * 40)
        
        test_queries = [
            {
                "messages": [{"role": "user", "content": "What is machine learning?"}],
                "type": "educational",
                "description": "Educational query"
            },
            {
                "messages": [{"role": "user", "content": "Tell me a joke"}],
                "type": "conversation", 
                "description": "Conversation query"
            },
            {
                "messages": [{"role": "user", "content": "What's the weather like today?"}],
                "type": "weather",
                "description": "Weather query"
            }
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query['description']}")
            
            try:
                # First call (should be cache miss)
                start_time = asyncio.get_event_loop().time()
                response1 = await self.llm_service.call_llm_with_fallback(
                    query["messages"],
                    enable_caching=True
                )
                first_call_time = asyncio.get_event_loop().time() - start_time
                
                # Second call (should be cache hit)
                start_time = asyncio.get_event_loop().time()
                response2 = await self.llm_service.call_llm_with_fallback(
                    query["messages"],
                    enable_caching=True
                )
                second_call_time = asyncio.get_event_loop().time() - start_time
                
                # Compare results
                cache_hit = response1 == response2
                speedup = first_call_time / second_call_time if second_call_time > 0 else 1
                
                print(f"   First call: {first_call_time:.3f}s")
                print(f"   Second call: {second_call_time:.3f}s")
                print(f"   Cache hit: {'✅ Yes' if cache_hit else '❌ No'}")
                print(f"   Speedup: {speedup:.1f}x")
                
            except Exception as e:
                print(f"   ❌ Test failed: {e}")
    
    async def export_config(self, output_file: str):
        """Export current cache configuration."""
        print(f"📄 Exporting cache configuration to {output_file}...")
        
        try:
            stats = self.cache_service.get_cache_stats()
            config_data = {
                "timestamp": asyncio.get_event_loop().time(),
                "cache_stats": stats,
                "configuration": stats.get('config', {}),
                "recommendations": stats.get('optimization_recommendations', [])
            }
            
            with open(output_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Configuration exported successfully")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            logger.error(f"Export error: {e}")


async def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Manage Advanced Prompt Caching System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manage_prompt_cache.py stats
  python scripts/manage_prompt_cache.py stats --detailed
  python scripts/manage_prompt_cache.py optimize
  python scripts/manage_prompt_cache.py clear --type conversation
  python scripts/manage_prompt_cache.py test
  python scripts/manage_prompt_cache.py export --output cache_config.json
        """
    )
    
    parser.add_argument(
        'command',
        choices=['stats', 'optimize', 'clear', 'test', 'export'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed statistics'
    )
    
    parser.add_argument(
        '--type',
        type=str,
        help='Cache type for clear operation (conversation, weather, educational, etc.)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='cache_config.json',
        help='Output file for export command'
    )
    
    args = parser.parse_args()
    
    # Initialize cache manager
    manager = PromptCacheManager()
    
    try:
        if args.command == 'stats':
            await manager.show_stats(detailed=args.detailed)
        
        elif args.command == 'optimize':
            await manager.optimize_cache()
        
        elif args.command == 'clear':
            await manager.clear_cache(cache_type=args.type)
        
        elif args.command == 'test':
            await manager.test_caching()
        
        elif args.command == 'export':
            await manager.export_config(args.output)
    
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
