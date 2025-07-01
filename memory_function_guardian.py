#!/usr/bin/env python3
"""
Memory Function Auto-Recovery System
==================================
This script monitors and automatically re-enables the memory function if it gets disabled.
"""

import sqlite3
import time
import json
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_and_fix_function():
    """Check if the memory function is enabled and fix if needed"""
    db_path = "storage/openwebui/webui.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check function status
        cursor.execute("SELECT id, is_active FROM function WHERE id = 'memory_function'")
        result = cursor.fetchone()
        
        if not result:
            logger.error("❌ Memory function not found in database!")
            return False
            
        function_id, is_active = result
        
        if not is_active:
            logger.warning("⚠️  Memory function is disabled - re-enabling...")
            
            # Re-enable the function
            cursor.execute("""
                UPDATE function 
                SET is_active = 1,
                    updated_at = ?
                WHERE id = 'memory_function'
            """, (int(time.time()),))
            
            conn.commit()
            logger.info("✅ Memory function re-enabled!")
        else:
            logger.info("✅ Memory function is already active")
        
        # Check model configurations
        cursor.execute("SELECT id, name, params FROM model")
        models = cursor.fetchall()
        
        for model_id, model_name, params_str in models:
            if params_str:
                try:
                    params = json.loads(params_str)
                    filters = params.get('filter_ids', [])
                    
                    if 'memory_function' not in filters:
                        logger.info(f"🔧 Adding memory function to model: {model_name}")
                        filters.append('memory_function')
                        params['filter_ids'] = filters
                        
                        cursor.execute("""
                            UPDATE model 
                            SET params = ?,
                                updated_at = ?
                            WHERE id = ?
                        """, (json.dumps(params), int(time.time()), model_id))
                        
                        logger.info(f"✅ Memory function added to {model_name}")
                except json.JSONDecodeError:
                    logger.warning(f"⚠️  Could not parse params for model {model_name}")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking function status: {e}")
        return False

def monitor_function():
    """Continuously monitor the function status"""
    logger.info("🔄 Starting memory function monitor...")
    
    while True:
        try:
            check_and_fix_function()
            time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        monitor_function()
    else:
        print("🔧 Checking Memory Function Status...")
        if check_and_fix_function():
            print("🎉 Memory function check complete!")
        else:
            print("💥 Memory function check failed!")
            sys.exit(1)
