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
        
        # Safely extract data with null checks
        ids = all_docs.get('ids', []) if all_docs else []
        metadatas = all_docs.get('metadatas', []) if all_docs else []
        documents = all_docs.get('documents', []) if all_docs else []
        
        print(f"📝 Retrieved {len(ids)} documents:")
        
        for i, doc_id in enumerate(ids):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            document = documents[i] if documents and i < len(documents) else ''
            
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
        
        if not db_manager.chroma_collection:
            print("❌ ChromaDB collection not available")
            return
            
        results = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5
        )
        
        # Safely handle query results
        documents = results.get('documents', [[]]) if results else [[]]
        distances = results.get('distances', [[]]) if results else [[]]
        
        if documents and documents[0]:
            print(f"Results found: {len(documents[0])}")
            for i, doc in enumerate(documents[0]):
                distance = distances[0][i] if distances and distances[0] and i < len(distances[0]) else 'N/A'
                print(f"   {i+1}. Distance: {distance}")
                print(f"      Content: {doc[:100]}...")
        else:
            print("No results found")
        
        # Search with user filter
        print("\n🔍 Search with user filter:")
        results_filtered = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=5,
            where={"user_id": "search_test_user"}
        )
        
        # Safely handle filtered query results
        filtered_documents = results_filtered.get('documents', [[]]) if results_filtered else [[]]
        filtered_distances = results_filtered.get('distances', [[]]) if results_filtered else [[]]
        filtered_metadatas = results_filtered.get('metadatas', [[]]) if results_filtered else [[]]
        
        if filtered_documents and filtered_documents[0]:
            print(f"Filtered results found: {len(filtered_documents[0])}")
            for i, doc in enumerate(filtered_documents[0]):
                distance = filtered_distances[0][i] if filtered_distances and filtered_distances[0] and i < len(filtered_distances[0]) else 'N/A'
                metadata = filtered_metadatas[0][i] if filtered_metadatas and filtered_metadatas[0] and i < len(filtered_metadatas[0]) else {}
                print(f"   {i+1}. Distance: {distance}")
                print(f"      User ID: {metadata.get('user_id', 'N/A') if isinstance(metadata, dict) else 'N/A'}")
                print(f"      Content: {doc[:100]}...")
        else:
            print("No filtered results found")
        
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
