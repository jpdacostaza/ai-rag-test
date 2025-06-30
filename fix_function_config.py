#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

print("🔧 Fixing Memory Function Configuration...")

# Update the function to be active
cursor.execute("UPDATE function SET is_active = 1 WHERE id = 'memory_function'")

# Also check and update the type to ensure it's correct
cursor.execute("UPDATE function SET type = 'filter' WHERE id = 'memory_function'")

conn.commit()

# Verify the changes
cursor.execute("SELECT id, name, type, is_active, is_global FROM function WHERE id = 'memory_function'")
func = cursor.fetchone()
if func:
    print('✅ Updated function configuration:')
    print(f'   ID: {func[0]}')
    print(f'   Name: {func[1]}')
    print(f'   Type: {func[2]}')
    print(f'   Active: {func[3]}')
    print(f'   Global: {func[4]}')
else:
    print('❌ Function not found!')

conn.close()
print("🎉 Function configuration updated!")
