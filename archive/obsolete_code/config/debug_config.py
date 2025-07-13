#!/usr/bin/env python3
"""Debug script to test config loading."""

from config.config_unified import Config

def main():
    print("Testing config loading...")
    
    config = Config.get_instance()
    
    print(f"Database config: {config.database}")
    print(f"Redis host: {config.database.redis_host}")
    print(f"Redis port: {config.database.redis_port}")
    
    print(f"Service config: {config.service}")
    print(f"API timeout: {config.service.api_timeout}")
    print(f"API timeout type: {type(config.service.api_timeout)}")

if __name__ == "__main__":
    main()
