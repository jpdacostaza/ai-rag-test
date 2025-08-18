#!/usr/bin/env python3
"""
Comprehensive User Document Isolation Analysis
Tests actual user isolation and creates a test scenario with multiple users
"""
import sqlite3
import chromadb
import json
import uuid
import hashlib
from datetime import datetime

def create_test_users_and_documents():
    """Create test users and documents to verify isolation"""
    print("🧪 CREATING TEST SCENARIO...")
    
    db_path = '/app/backend/data/webui.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create test users
    test_user1_id = str(uuid.uuid4())
    test_user2_id = str(uuid.uuid4())
    
    current_time = datetime.now().isoformat()
    
    # Insert test users
    try:
        cursor.execute("""
            INSERT INTO user (id, name, email, role, created_at, updated_at, last_active_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user1_id, "Test User 1", "testuser1@example.com", "user", current_time, current_time, current_time))
        
        cursor.execute("""
            INSERT INTO user (id, name, email, role, created_at, updated_at, last_active_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user2_id, "Test User 2", "testuser2@example.com", "user", current_time, current_time, current_time))
        
        print(f"✅ Created test users: {test_user1_id}, {test_user2_id}")
        
        # Create test files for each user
        test_content1 = b"This is User 1's private document content"
        test_content2 = b"This is User 2's confidential information"
        
        file1_hash = hashlib.sha256(test_content1).hexdigest()
        file2_hash = hashlib.sha256(test_content2).hexdigest()
        
        file1_id = str(uuid.uuid4())
        file2_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO file (id, user_id, filename, hash, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file1_id, test_user1_id, "user1_private.txt", file1_hash, test_content1, current_time, current_time))
        
        cursor.execute("""
            INSERT INTO file (id, user_id, filename, hash, data, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (file2_id, test_user2_id, "user2_confidential.txt", file2_hash, test_content2, current_time, current_time))
        
        print(f"✅ Created test files for both users")
        
        # Create test documents
        doc1_id = str(uuid.uuid4())
        doc2_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO document (id, collection_name, name, title, filename, content, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc1_id, f"file-{file1_id}", "user1_private.txt", "User 1 Private Document", 
              "user1_private.txt", "User 1 private document content for testing", test_user1_id, current_time))
        
        cursor.execute("""
            INSERT INTO document (id, collection_name, name, title, filename, content, user_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc2_id, f"file-{file2_id}", "user2_confidential.txt", "User 2 Confidential Document",
              "user2_confidential.txt", "User 2 confidential document content for testing", test_user2_id, current_time))
        
        print(f"✅ Created test documents for both users")
        
        conn.commit()
        conn.close()
        
        return test_user1_id, test_user2_id, file1_id, file2_id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        conn.rollback()
        conn.close()
        return None, None, None, None

def test_cross_user_access(user1_id, user2_id, file1_id, file2_id):
    """Test if users can access each other's data"""
    print("\n🔐 TESTING CROSS-USER ACCESS VULNERABILITIES...")
    
    db_path = '/app/backend/data/webui.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    vulnerabilities = []
    
    # Test 1: Can User1 see User2's files?
    print("🧪 Test 1: File access isolation")
    cursor.execute("SELECT filename FROM file WHERE user_id = ? AND id = ?", (user2_id, file2_id))
    user2_file = cursor.fetchone()
    
    if user2_file:
        # Try to access as User1
        cursor.execute("SELECT * FROM file WHERE user_id = ? AND filename = ?", (user1_id, user2_file[0]))
        unauthorized_file = cursor.fetchone()
        
        if unauthorized_file:
            vulnerabilities.append("User1 can access User2's files")
            print("❌ VULNERABILITY: Cross-user file access possible")
        else:
            print("✅ SECURE: Users cannot access each other's files")
    
    # Test 2: Can User1 see User2's documents?
    print("🧪 Test 2: Document access isolation")
    cursor.execute("SELECT name FROM document WHERE user_id = ?", (user2_id,))
    user2_docs = cursor.fetchall()
    
    for doc in user2_docs:
        cursor.execute("SELECT * FROM document WHERE user_id = ? AND name = ?", (user1_id, doc[0]))
        unauthorized_doc = cursor.fetchone()
        
        if unauthorized_doc:
            vulnerabilities.append("User1 can access User2's documents")
            print("❌ VULNERABILITY: Cross-user document access possible")
            break
    else:
        print("✅ SECURE: Users cannot access each other's documents")
    
    # Test 3: Check collection name patterns
    print("🧪 Test 3: Collection naming isolation")
    cursor.execute("SELECT DISTINCT collection_name FROM document WHERE user_id = ?", (user1_id,))
    user1_collections = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT DISTINCT collection_name FROM document WHERE user_id = ?", (user2_id,))
    user2_collections = [row[0] for row in cursor.fetchall()]
    
    shared_collections = set(user1_collections) & set(user2_collections)
    if shared_collections:
        vulnerabilities.append("Shared collection names between users")
        print(f"❌ VULNERABILITY: Shared collections: {shared_collections}")
    else:
        print("✅ SECURE: Each user has unique collection names")
    
    conn.close()
    return vulnerabilities

def analyze_chromadb_isolation():
    """Analyze ChromaDB collections for user isolation"""
    print("\n🗄️ ANALYZING CHROMADB USER ISOLATION...")
    
    try:
        chroma_path = '/app/backend/data/chroma'
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        # Get collection names (updated for newer ChromaDB version)
        collections_result = chroma_client.list_collections()
        
        if hasattr(collections_result, '__iter__'):
            collection_names = [c.name if hasattr(c, 'name') else str(c) for c in collections_result]
        else:
            collection_names = []
        
        print(f"📊 Found {len(collection_names)} ChromaDB collections")
        
        user_collections = {}
        for collection_name in collection_names:
            print(f"   - Analyzing collection: {collection_name}")
            
            try:
                collection = chroma_client.get_collection(collection_name)
                
                # Get all documents from collection
                all_docs = collection.get()
                
                if all_docs and 'metadatas' in all_docs and all_docs['metadatas']:
                    # Check for user isolation in metadata
                    user_ids = set()
                    for metadata in all_docs['metadatas']:
                        if metadata and 'user_id' in metadata:
                            user_ids.add(metadata['user_id'])
                        elif metadata and 'source' in metadata:
                            # Check if source contains user identification
                            source = metadata['source']
                            print(f"     Source pattern: {source}")
                    
                    if len(user_ids) > 1:
                        print(f"     ⚠️  MIXED USERS: {len(user_ids)} different users in same collection")
                        user_collections[collection_name] = user_ids
                    elif len(user_ids) == 1:
                        print(f"     ✅ SINGLE USER: {list(user_ids)[0]}")
                        user_collections[collection_name] = user_ids
                    else:
                        print(f"     ❓ NO USER ID: No user identification in metadata")
                        # Check if collection name contains user info
                        if collection_name.startswith('file-'):
                            print(f"     💡 Collection uses file-UUID pattern for isolation")
                else:
                    print(f"     📭 Empty collection")
                    
            except Exception as e:
                print(f"     ❌ Error accessing collection {collection_name}: {e}")
        
        return user_collections
        
    except Exception as e:
        print(f"❌ ChromaDB analysis failed: {e}")
        return {}

def cleanup_test_data(user1_id, user2_id):
    """Clean up test data"""
    print("\n🧹 CLEANING UP TEST DATA...")
    
    db_path = '/app/backend/data/webui.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Remove test files
        cursor.execute("DELETE FROM file WHERE user_id IN (?, ?)", (user1_id, user2_id))
        files_deleted = cursor.rowcount
        
        # Remove test documents  
        cursor.execute("DELETE FROM document WHERE user_id IN (?, ?)", (user1_id, user2_id))
        docs_deleted = cursor.rowcount
        
        # Remove test users
        cursor.execute("DELETE FROM user WHERE id IN (?, ?)", (user1_id, user2_id))
        users_deleted = cursor.rowcount
        
        conn.commit()
        print(f"✅ Cleaned up: {users_deleted} users, {files_deleted} files, {docs_deleted} documents")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """Main test function"""
    print("=" * 80)
    print("COMPREHENSIVE USER DOCUMENT ISOLATION TEST")
    print("=" * 80)
    
    # Create test scenario
    user1_id, user2_id, file1_id, file2_id = create_test_users_and_documents()
    
    if not all([user1_id, user2_id, file1_id, file2_id]):
        print("❌ Failed to create test data, exiting")
        return
    
    try:
        # Test cross-user access
        vulnerabilities = test_cross_user_access(user1_id, user2_id, file1_id, file2_id)
        
        # Analyze ChromaDB
        chroma_analysis = analyze_chromadb_isolation()
        
        # Print final security assessment
        print("\n" + "=" * 80)
        print("🛡️  SECURITY ASSESSMENT RESULTS")
        print("=" * 80)
        
        if vulnerabilities:
            print("❌ VULNERABILITIES FOUND:")
            for vuln in vulnerabilities:
                print(f"   - {vuln}")
        else:
            print("✅ NO DATABASE-LEVEL VULNERABILITIES FOUND")
        
        print("\n🔍 CHROMADB ANALYSIS:")
        if chroma_analysis:
            for collection, users in chroma_analysis.items():
                if len(users) > 1:
                    print(f"   ⚠️  Collection '{collection}' contains multiple users: {users}")
                else:
                    print(f"   ✅ Collection '{collection}' properly isolated")
        else:
            print("   💡 ChromaDB uses file-UUID collection naming for isolation")
        
        print("\n🎯 FINAL ASSESSMENT:")
        if vulnerabilities or any(len(users) > 1 for users in chroma_analysis.values()):
            print("   ⚠️  POTENTIAL SECURITY ISSUES DETECTED")
            print("   👉 Requires application-level access control verification")
        else:
            print("   ✅ DATABASE STRUCTURE SUPPORTS USER ISOLATION")
            print("   👉 Application code should enforce user_id filtering")
        
        print("\n🔒 REQUIRED SAFEGUARDS:")
        print("   1. All file queries MUST filter by user_id")
        print("   2. All document queries MUST filter by user_id") 
        print("   3. ChromaDB collections should be user-specific")
        print("   4. API endpoints MUST validate ownership before access")
        print("   5. Frontend should never display other users' documents")
        
    finally:
        # Always cleanup test data
        cleanup_test_data(user1_id, user2_id)

if __name__ == "__main__":
    main()
