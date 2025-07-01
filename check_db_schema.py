#!/usr/bin/env python3
import sqlite3
import sys

db_path = '/tmp/openwebui/webui.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check function table schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='function'")
    result = cursor.fetchone()
    if result:
        print("Function table schema:")
        print(result[0])
    else:
        print("No function table found")
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nAll tables: {[t[0] for t in tables]}")
    
    # If function table exists, show its columns
    if result:
        cursor.execute("PRAGMA table_info(function)")
        columns = cursor.fetchall()
        print(f"\nFunction table columns:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
