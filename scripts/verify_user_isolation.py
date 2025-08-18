#!/usr/bin/env python3
"""
User Document Isolation Verification
Verify that existing documents are properly isolated per user
"""
import sqlite3
import chromadb
import json

def verify_user_isolation():
    """
    Verify that document access is properly isolated per user
    """
    print("=" * 80)
    print("USER DOCUMENT ISOLATION VERIFICATION")
    print("=" * 80)
    
    db_path = '/app/backend/data/webui.db'
    chroma_path = '/app/backend/data/chroma'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id, email, name FROM user")
        users = cursor.fetchall()
        print(f"\n👥 USERS IN SYSTEM: {len(users)}")
        for user in users:
            print(f"   - {user[1]} ({user[2]}) - ID: {user[0]}")
        
        # Check file ownership
        print(f"\n📄 FILE OWNERSHIP ANALYSIS:")
        cursor.execute("""
            SELECT f.user_id, u.email, COUNT(*) as file_count 
            FROM file f 
            JOIN user u ON f.user_id = u.id 
            GROUP BY f.user_id, u.email
        """)
        file_stats = cursor.fetchall()
        
        for user_id, email, count in file_stats:
            print(f"   - {email}: {count} files")
            
            # Show sample files for this user
            cursor.execute("SELECT filename, hash FROM file WHERE user_id = ? LIMIT 3", (user_id,))
            sample_files = cursor.fetchall()
            for filename, file_hash in sample_files:
                print(f"     • {filename[:40]}... (hash: {file_hash[:8]}...)")
        
        # Check document ownership
        print(f"\n📋 DOCUMENT OWNERSHIP ANALYSIS:")
        cursor.execute("""
            SELECT d.user_id, u.email, COUNT(*) as doc_count 
            FROM document d 
            JOIN user u ON d.user_id = u.id 
            GROUP BY d.user_id, u.email
        """)
        doc_stats = cursor.fetchall()
        
        for user_id, email, count in doc_stats:
            print(f"   - {email}: {count} documents")
            
            # Show sample documents and their collections
            cursor.execute("SELECT name, collection_name FROM document WHERE user_id = ? LIMIT 3", (user_id,))
            sample_docs = cursor.fetchall()
            for doc_name, collection in sample_docs:
                print(f"     • {doc_name[:40]}... → Collection: {collection}")
        
        # Check for collection name uniqueness
        print(f"\n🗂️ COLLECTION ANALYSIS:")
        cursor.execute("SELECT collection_name, COUNT(DISTINCT user_id) as user_count FROM document GROUP BY collection_name")
        collection_stats = cursor.fetchall()
        
        shared_collections = 0
        isolated_collections = 0
        
        for collection, user_count in collection_stats:
            if user_count > 1:
                shared_collections += 1
                print(f"   ⚠️  SHARED: {collection} (used by {user_count} users)")
            else:
                isolated_collections += 1
                print(f"   ✅ ISOLATED: {collection} (single user)")
        
        print(f"\n📊 COLLECTION SUMMARY:")
        print(f"   - Isolated collections: {isolated_collections}")
        print(f"   - Shared collections: {shared_collections}")
        
        # Test ChromaDB collections
        print(f"\n🗄️ CHROMADB COLLECTIONS:")
        try:
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            collections = chroma_client.list_collections()
            
            print(f"   Found {len(collections)} collections:")
            
            for collection in collections:
                collection_name = collection.name if hasattr(collection, 'name') else str(collection)
                print(f"   - {collection_name}")
                
                try:
                    coll_obj = chroma_client.get_collection(collection_name)
                    doc_count = coll_obj.count()
                    print(f"     └─ {doc_count} documents")
                    
                    # Check if this collection matches any document collection
                    cursor.execute("SELECT DISTINCT user_id FROM document WHERE collection_name = ?", (collection_name,))
                    owners = cursor.fetchall()
                    if owners:
                        if len(owners) == 1:
                            print(f"     └─ ✅ Owned by single user: {owners[0][0]}")
                        else:
                            print(f"     └─ ⚠️  Multiple owners: {len(owners)} users")
                    else:
                        print(f"     └─ ❓ No matching document records")
                        
                except Exception as e:
                    print(f"     └─ ❌ Error accessing: {e}")
                    
        except Exception as e:
            print(f"   ❌ ChromaDB error: {e}")
        
        # Test actual access patterns
        print(f"\n🔐 ACCESS PATTERN VERIFICATION:")
        
        if len(users) >= 1:
            test_user = users[0]
            user_id, email, name = test_user
            
            print(f"   Testing access for user: {email}")
            
            # Get this user's files
            cursor.execute("SELECT filename FROM file WHERE user_id = ?", (user_id,))
            user_files = cursor.fetchall()
            print(f"   - User can see {len(user_files)} of their own files")
            
            # Check if user can see other users' files (this should be controlled by application)
            cursor.execute("SELECT filename FROM file WHERE user_id != ?", (user_id,))
            other_files = cursor.fetchall()
            print(f"   - Database contains {len(other_files)} files from other users")
            
            # Get this user's documents
            cursor.execute("SELECT name FROM document WHERE user_id = ?", (user_id,))
            user_docs = cursor.fetchall()
            print(f"   - User can see {len(user_docs)} of their own documents")
            
            # Check other users' documents
            cursor.execute("SELECT name FROM document WHERE user_id != ?", (user_id,))
            other_docs = cursor.fetchall()
            print(f"   - Database contains {len(other_docs)} documents from other users")
            
            if other_files or other_docs:
                print(f"   ⚠️  Application MUST filter by user_id to prevent cross-user access!")
            else:
                print(f"   ✅ Only single user data exists - no cross-access risk")
        
        conn.close()
        
        # Final assessment
        print(f"\n" + "=" * 80)
        print("🛡️  ISOLATION ASSESSMENT")
        print("=" * 80)
        
        if shared_collections > 0:
            print("❌ SECURITY CONCERN: Some collections are shared between users")
            print("   👉 This could lead to cross-user document access")
        else:
            print("✅ GOOD: All collections are user-specific")
        
        print("\n🔒 REQUIRED SAFEGUARDS (MUST BE IMPLEMENTED IN APPLICATION):")
        print("   1. File API endpoints MUST filter: WHERE user_id = current_user_id")
        print("   2. Document API endpoints MUST filter: WHERE user_id = current_user_id")
        print("   3. ChromaDB queries MUST use user-specific collection names")
        print("   4. Upload endpoints MUST set user_id = current_user_id")
        print("   5. RAG queries MUST only search user's own collections")
        
        print("\n💡 VERIFICATION CHECKLIST:")
        print("   □ Check /api/files endpoints for user_id filtering")
        print("   □ Check /api/documents endpoints for user_id filtering")
        print("   □ Check ChromaDB collection naming patterns")
        print("   □ Check RAG query functions for user isolation")
        print("   □ Check file upload workflow for proper user assignment")
        
        return {
            'users_count': len(users),
            'shared_collections': shared_collections,
            'isolated_collections': isolated_collections,
            'total_files': sum(count for _, _, count in file_stats),
            'total_documents': sum(count for _, _, count in doc_stats)
        }
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = verify_user_isolation()
    if result:
        print(f"\n📈 SYSTEM STATS:")
        print(f"   - Users: {result['users_count']}")
        print(f"   - Total files: {result['total_files']}")
        print(f"   - Total documents: {result['total_documents']}")
        print(f"   - Isolated collections: {result['isolated_collections']}")
        print(f"   - Shared collections: {result['shared_collections']}")
        
        if result['shared_collections'] == 0:
            print("\n✅ DATABASE STRUCTURE: SUPPORTS USER ISOLATION")
        else:
            print("\n⚠️  DATABASE STRUCTURE: REQUIRES CAREFUL APPLICATION IMPLEMENTATION")
