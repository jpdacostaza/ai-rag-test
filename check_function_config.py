#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Check the current function configuration
cursor.execute("SELECT id, name, type, is_active, is_global, meta FROM function WHERE id = 'memory_function'")
func = cursor.fetchone()
if func:
    print('Current function:', func)
    print('Type:', func[2])
    print('Active:', func[3])
    print('Global:', func[4])
    if func[5]:
        print('Meta:', func[5])
else:
    print('Function not found!')

# Also check if there are any model-specific configurations
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%model%'")
model_tables = cursor.fetchall()
print('Model-related tables:', model_tables)

conn.close()
