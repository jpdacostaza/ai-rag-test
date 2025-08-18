# OpenWebUI Duplicate Management Integration Guide

Complete implementation guide for production deployment

## 📋 Implementation Roadmap

### 🔧 Phase 1: Duplicate Prevention (Recommended First)

#### 1. Modify File Upload Router (`/app/backend/routers/files.py`):

```python
@app.post("/files/")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    # Calculate file hash
    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check for duplicates
    duplicate_manager = DuplicateFileManager()
    duplicate_info = duplicate_manager.check_duplicate_file(
        user_id, file_hash, file.filename
    )
    
    if duplicate_info['has_exact_duplicate']:
        return {
            "duplicate_detected": True,
            "recommendations": duplicate_info['recommendations'],
            "existing_files": duplicate_info['exact_matches']
        }
    
    # Proceed with normal upload...
    return await process_upload(file, user_id, file_hash)
```

#### 2. Add Frontend Duplicate Dialog:

```javascript
// In your upload component
if (uploadResponse.duplicate_detected) {
    showDuplicateDialog({
        filename: file.name,
        recommendations: uploadResponse.recommendations,
        onUserChoice: (action) => handleDuplicateChoice(action, file)
    });
}
```

#### 3. Implement User Choice Handler:

```javascript
async function handleDuplicateChoice(action, file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('action', action);
    
    const response = await fetch('/api/files/upload-with-choice', {
        method: 'POST',
        body: formData
    });
    
    return response.json();
}
```

### 🔍 Phase 2: Smart RAG Filtering (Performance Improvement)

#### 1. Modify RAG Query Function:

```python
async def enhanced_rag_query(user_id: str, query: str, n_results: int = 10):
    # Use smart filter instead of querying all collections
    smart_filter = SmartRAGFilter()
    
    # Get deduplicated results
    filtered_results = smart_filter.query_all_collections(
        user_id, query, n_results
    )
    
    # Format for chat response
    context_chunks = []
    for result in filtered_results:
        context_chunks.append({
            "content": result['content'],
            "source": result['metadata'].get('source', 'Unknown'),
            "relevance": 1 - result['distance'],
            "duplicate_count": result.get('duplicate_count', 1)
        })
    
    return context_chunks
```

#### 2. Update Chat Pipeline:

```python
# In your chat processing pipeline
if context_needed:
    context = await enhanced_rag_query(user_id, user_message)
    
    # Add context to prompt with duplicate info
    prompt = build_chat_prompt(user_message, context)
```

### 👨‍💼 Phase 3: Admin Management Tools (System Maintenance)

#### 1. Add Admin Routes (`/app/backend/routers/admin.py`):

```python
@router.get("/admin/duplicates/report")
async def get_duplicate_report(current_user: User = Depends(get_admin_user)):
    dashboard = DuplicateAdminDashboard()
    return dashboard.generate_system_report()

@router.post("/admin/duplicates/cleanup")
async def cleanup_duplicates(
    confirm: bool = False,
    current_user: User = Depends(get_admin_user)
):
    dashboard = DuplicateAdminDashboard()
    cleanup_plan = dashboard.create_cleanup_plan(dry_run=not confirm)
    
    if confirm:
        result = dashboard.execute_cleanup(cleanup_plan, confirm=True)
        return result
    else:
        return cleanup_plan
```

#### 2. Create Admin Dashboard Page:

```javascript
// Admin component for duplicate management
const DuplicateManagement = () => {
    const [report, setReport] = useState(null);
    const [cleanupPlan, setCleanupPlan] = useState(null);
    
    useEffect(() => {
        fetchDuplicateReport();
    }, []);
    
    const executeCleanup = async () => {
        if (confirm('This will permanently delete duplicate files!')) {
            await api.post('/admin/duplicates/cleanup', { confirm: true });
            fetchDuplicateReport(); // Refresh
        }
    };
    
    return (
        <div className="admin-duplicates">
            <SystemStats report={report} />
            <CleanupPlan plan={cleanupPlan} onExecute={executeCleanup} />
            <UserDuplicates report={report} />
        </div>
    );
};
```

### 🛡️ Phase 4: Safety Measures (Critical)

#### 1. Database Backup Automation:

```bash
#!/bin/bash
# Add to cron: 0 2 * * * /app/scripts/backup_before_cleanup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/app/backups"

# Backup SQLite database
cp /app/backend/data/webui.db "$BACKUP_DIR/webui_$DATE.db"

# Backup ChromaDB
tar -czf "$BACKUP_DIR/chroma_$DATE.tar.gz" /app/backend/data/chroma/

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
```

#### 2. Safety Checks in Code:

```python
def safe_delete_file(file_id: str) -> bool:
    # Verify file exists
    if not file_exists(file_id):
        return False
    
    # Check if it's actually a duplicate
    if not is_confirmed_duplicate(file_id):
        return False
    
    # Create backup entry before deletion
    create_deletion_log(file_id)
    
    # Proceed with deletion
    return delete_file_and_vectors(file_id)
```

#### 3. Rollback Capability:

```python
class DeletionLog:
    @staticmethod
    def log_deletion(file_id: str, file_data: dict):
        # Store deletion info for potential recovery
        deletion_record = {
            'timestamp': datetime.now().isoformat(),
            'file_id': file_id,
            'file_data': file_data,
            'vector_data': export_vector_collection(f'file-{file_id}')
        }
        
        with open(f'/app/logs/deletions/{file_id}.json', 'w') as f:
            json.dump(deletion_record, f)
    
    @staticmethod
    def restore_deleted_file(file_id: str):
        # Restore from deletion log if needed
        with open(f'/app/logs/deletions/{file_id}.json', 'r') as f:
            deletion_record = json.load(f)
        
        # Restore file and vector data
        restore_file_from_backup(deletion_record)
```

### ⚡ Phase 5: Performance Optimizations (Advanced)

#### 1. Batch Operations:

```python
class BatchDuplicateProcessor:
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.pending_operations = []
    
    def queue_duplicate_check(self, file_info: dict):
        self.pending_operations.append(file_info)
        
        if len(self.pending_operations) >= self.batch_size:
            self.process_batch()
    
    def process_batch(self):
        # Process multiple files efficiently
        file_hashes = [f['hash'] for f in self.pending_operations]
        
        # Single database query for all hashes
        duplicates = check_multiple_hashes(file_hashes)
        
        # Process results
        for file_info, duplicate_info in zip(self.pending_operations, duplicates):
            handle_duplicate_result(file_info, duplicate_info)
        
        self.pending_operations.clear()
```

#### 2. Caching Layer:

```python
class DuplicateCache:
    def __init__(self):
        self.hash_cache = {}  # hash -> file_info
        self.user_cache = {}  # user_id -> file_list
    
    def check_cache_first(self, user_id: str, file_hash: str):
        # Check cache before hitting database
        if file_hash in self.hash_cache:
            return self.hash_cache[file_hash]
        
        # Check user-specific cache
        user_files = self.user_cache.get(user_id, [])
        for file_info in user_files:
            if file_info['hash'] == file_hash:
                return file_info
        
        return None
```

#### 3. Async Processing:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncDuplicateManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def check_duplicates_async(self, file_infos: List[dict]):
        # Process multiple files concurrently
        tasks = [
            self.loop.run_in_executor(
                self.executor, 
                self.check_single_duplicate, 
                file_info
            )
            for file_info in file_infos
        ]
        
        results = await asyncio.gather(*tasks)
        return results
```

## ✅ Deployment Checklist

- [ ] 🔧 Database backup system implemented
- [ ] 🛡️ Safety checks and rollback capability added
- [ ] 📊 Admin dashboard for duplicate management
- [ ] 🔍 Smart RAG filtering to reduce duplicates
- [ ] ⚠️ User notification system for duplicates
- [ ] 📱 Frontend dialogs for user choice
- [ ] 🏃‍♂️ Performance optimizations (caching, batching)
- [ ] 📋 Monitoring and alerting for storage issues
- [ ] 🧪 Comprehensive testing of all scenarios
- [ ] 📚 Documentation and training for admins

## 🚀 Quick Start for Your System

### Immediate Actions for Your CV Duplicates:

#### 1. 🛡️ Backup First:
```bash
docker exec backend-openwebui cp /app/backend/data/webui.db /app/backend/data/webui_backup.db
```

#### 2. 🧹 Clean Up Existing Duplicates:
```bash
# Run the cleanup tool we created (uncomment deletion code first)
docker exec backend-openwebui python /tmp/tools/duplicate_cleanup_tool.py
```

#### 3. 🔍 Implement Smart RAG Filtering:
```bash
# Use the smart filter for better query results
docker exec backend-openwebui python /tmp/tools/smart_rag_filter.py
```

#### 4. 📊 Monitor with Admin Dashboard:
```bash
# Regular monitoring of duplicate status
docker exec backend-openwebui python /tmp/tools/admin_dashboard.py
```

### Current Status:
- ✅ Your CV is accessible through both collections
- ⚠️ Duplicate results may appear in RAG responses  
- 💾 Using 2x storage space (84 chunks instead of 42)
- 🎯 Ready to implement solutions above

### Next Steps:
1. Choose: Clean up existing duplicates OR implement prevention first
2. Test smart RAG filtering on your CV queries
3. Monitor system with admin dashboard
4. Plan full integration based on phases above

## 📍 File Locations After Organization

- **Scripts**: `/scripts/` - Document processing and analysis scripts
- **Tools**: `/tools/` - Management and admin tools
- **Utilities**: `/utilities/` - Analysis and testing utilities
- **Documentation**: `/docs/` - Complete guides and documentation
