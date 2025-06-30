#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Check function status
cursor.execute("SELECT id, name, type, is_active, is_global, content FROM function WHERE id = 'memory_function'")
func = cursor.fetchone()

if func:
    print(f"Function ID: {func[0]}")
    print(f"Name: {func[1]}")
    print(f"Type: {func[2]}")
    print(f"Active: {func[3]}")
    print(f"Global: {func[4]}")
    print(f"Code length: {len(func[5])} characters")
    
    # Check for syntax errors by trying to compile the code
    try:
        compile(func[5], '<function>', 'exec')
        print("✅ Function code compiles successfully")
    except SyntaxError as e:
        print(f"❌ Syntax error in function code: {e}")
        print(f"   Line {e.lineno}: {e.text}")
    except Exception as e:
        print(f"❌ Error in function code: {e}")
else:
    print("❌ Function not found!")

conn.close()
