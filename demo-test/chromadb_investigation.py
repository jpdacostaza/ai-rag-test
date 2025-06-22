#!/usr/bin/env python3
"""
ChromaDB Direct Investigation
=============================
Directly check what's stored in ChromaDB and debug the search issue.
"""

import sys
sys.path.append('.')

from database_manager import db_manager
import requests

def check_chromadb_contents():
    """Check what's actually stored in ChromaDB."""
    print("🔍 Checking ChromaDB Contents...")
    
    try:
        if not db_manager.chroma_collection:
            print("❌ ChromaDB collection not available")
            return
        
        # Get total count
        count = db_manager.chroma_collection.count()
        print(f"📊 Total documents in ChromaDB: {count}")
        
        if count == 0:
            print("⚠️ No documents found in ChromaDB")
            return
        
        # Get all documents (limit to 10 for readability)
        all_docs = db_manager.chroma_collection.get(limit=10)
        
        print(f"📝 Retrieved {len(all_docs.get('ids', []))} documents:")
        
        for i, doc_id in enumerate(all_docs.get('ids', [])):
            metadata = all_docs.get('metadatas', [{}])[i] if i < len(all_docs.get('metadatas', [])) else {}
            document = all_docs.get('documents', [''])[i] if i < len(all_docs.get('documents', [])) else ''
            
            print(f"   {i+1}. ID: {doc_id}")
            print(f"      User: {metadata.get('user_id', 'N/A')}")
            print(f"      Source: {metadata.get('source', 'N/A')}")
            print(f"      Content: {document[:100]}...")
            print()
        
        return all_docs
        
    except Exception as e:
        print(f"❌ Error checking ChromaDB: {e}")
        return None

def test_search_functionality():
    """Test the search functionality directly."""
    print("🔍 Testing Search Functionality...")
    
    try:
        # Upload a test document first
        print("📤 Uploading test document...")
        files = {'file': ('test_search.txt', 'DataViz Pro uses matplotlib for visualization and pandas for data processing. Memory optimization tips include chunked processing.', 'text/plain')}
        data = {'user_id': 'search_test_user'}
        
        upload_response = requests.post(
            "http://localhost:8001/upload/document",
            files=files,
            data=data,
            headers={"Authorization": "Bearer f2b985dd-219f-45b1-a90e-170962cc7082"},
            timeout=20
        )
        
        print(f"Upload Status: {upload_response.status_code}")
        if upload_response.status_code != 200:
            print(f"Upload failed: {upload_response.text}")
            return
        
        import time
        time.sleep(3)  # Wait for processing
        
        # Check what was stored
        print("\n📊 After upload:")
        check_chromadb_contents()
        
        # Test direct ChromaDB search
        print("\n🔍 Testing direct ChromaDB search...")
        from database_manager import get_embedding
        
        query = "DataViz Pro memory tips"
        query_embedding = get_embedding(query)
        
        if query_embedding is None:
            print("❌ Could not generate query embedding")
            return
        
        print(f"✅ Generated query embedding (shape: {query_embedding.shape})")
        
        # Search without user filter first
        print("\n🔍 Search without user filter:")
        results = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        print(f"Results found: {len(results.get('documents', [[]])[0])}")
        for i, doc in enumerate(results.get('documents', [[]])[0]):
            distance = results.get('distances', [[]])[0][i] if results.get('distances') else 'N/A'
            print(f"   {i+1}. Distance: {distance}")
            print(f"      Content: {doc[:100]}...")
        
        # Search with user filter
        print("\n🔍 Search with user filter:")
        results_filtered = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5,
            where={"user_id": "search_test_user"}
        )
        
        print(f"Filtered results found: {len(results_filtered.get('documents', [[]])[0])}")
        for i, doc in enumerate(results_filtered.get('documents', [[]])[0]):
            distance = results_filtered.get('distances', [[]])[0][i] if results_filtered.get('distances') else 'N/A'
            metadata = results_filtered.get('metadatas', [[]])[0][i] if results_filtered.get('metadatas') else {}
            print(f"   {i+1}. Distance: {distance}")
            print(f"      User ID: {metadata.get('user_id', 'N/A')}")
            print(f"      Content: {doc[:100]}...")
        
    except Exception as e:
        print(f"❌ Error in search test: {e}")

def main():
    """Run ChromaDB investigation."""
    print("🚀 Starting ChromaDB Direct Investigation")
    print("=" * 50)
    
    # Initialize database manager
    try:
        if not db_manager.chroma_collection:
            print("❌ ChromaDB not available")
            return
        
        print("✅ ChromaDB connection established")
        
        # Check current contents
        check_chromadb_contents()
        
        # Test search functionality
        test_search_functionality()
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")

if __name__ == "__main__":
    main()
