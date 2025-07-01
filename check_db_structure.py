#!/usr/bin/env python3
"""
Check OpenWebUI Database Structure
"""

import sqlite3
import json

def check_database():
    """Check the OpenWebUI database structure and contents"""
    db_path = 'storage/openwebui/webui.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current functions
        print('=== CURRENT FUNCTIONS ===')
        cursor.execute('SELECT id, name, type, is_active FROM function')
        functions = cursor.fetchall()
        for f in functions:
            print(f'ID: {f[0]}, Name: {f[1]}, Type: {f[2]}, Active: {f[3]}')
        
        # Check all tables
        print('\n=== ALL TABLES ===')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f'\nTable: {table_name}')
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f'  - {col[1]} ({col[2]})')
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()
