#!/usr/bin/env python3
import sqlite3
import json

# Connect to the database
conn = sqlite3.connect('webui.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables found:", tables)

# Check for users table
if 'user' in tables:
    print("\n=== USER TABLE ===")
    cursor.execute("PRAGMA table_info(user)")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
    
    cursor.execute("SELECT * FROM user LIMIT 5")
    users = cursor.fetchall()
    print(f"Found {len(users)} users (showing first 5):")
    for user in users:
        print(user)

# Check for users table (plural)
if 'users' in tables:
    print("\n=== USERS TABLE ===")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
    
    cursor.execute("SELECT * FROM users LIMIT 5")
    users = cursor.fetchall()
    print(f"Found {len(users)} users (showing first 5):")
    for user in users:
        print(user)

# Check auth table
if 'auth' in tables:
    print("\n=== AUTH TABLE ===")
    cursor.execute("PRAGMA table_info(auth)")
    columns = cursor.fetchall()
    print("Columns:", [col[1] for col in columns])
    
    cursor.execute("SELECT * FROM auth LIMIT 5")
    auths = cursor.fetchall()
    print(f"Found {len(auths)} auth records (showing first 5):")
    for auth in auths:
        print(auth)

conn.close()
