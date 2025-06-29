📋 Manual Memory Function Import Guide
=========================================

Since the automated import is having API issues, let's import the function manually through the OpenWebUI interface:

## Step 1: Copy the Function Code
1. Open the file: memory_filter_function.py
2. Select all the code (Ctrl+A) and copy it (Ctrl+C)

## Step 2: Import via OpenWebUI Interface
1. In your browser, go to: http://localhost:3000
2. Click on your profile (top right) → Admin Settings
3. Navigate to: Functions (in the left sidebar)
4. Click: "Import Function" or "+" button
5. In the import dialog:
   - ID: memory_filter
   - Name: Memory Filter
   - Type: filter
   - Paste the copied code in the content area
   - Description: Memory filter that adds context from previous conversations
6. Click "Import" or "Save"

## Step 3: Enable the Function
1. After import, find "Memory Filter" in the functions list
2. Toggle it to "Enabled" (should be a switch/toggle)
3. Make sure "Active" is set to true

## Step 4: Assign to Model
1. Go to: Models (in the left sidebar)
2. Find your model (e.g., "llama3.2:3b")
3. Click on it to open settings
4. Look for "Filters" or "Functions" section
5. Add "Memory Filter" to the model
6. Save the model settings

## Step 5: Test Memory Functionality
1. Start a new chat with the model
2. Ask: "Remember that I like pizza"
3. In a new conversation, ask: "What do you know about my food preferences?"
4. The AI should remember the pizza preference from the previous conversation

## Troubleshooting
- If the function doesn't appear in the Functions list, check the browser console for errors
- If memory doesn't work, check that all Docker containers are running:
  ```
  docker-compose ps
  ```
- Verify memory API is accessible:
  ```
  curl http://localhost:8003/health
  ```

## Next Steps After Manual Import
Once the function is imported and working, we can:
1. Test the memory persistence across different chats
2. Adjust memory settings via the function's "Valves" (configuration)
3. Add more sophisticated memory features
4. Monitor memory API logs for debugging

Would you like me to help with any of these steps?
