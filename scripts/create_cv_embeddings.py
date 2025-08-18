#!/usr/bin/env python3
"""
Create vector embeddings for the CV document
"""
import sys
sys.path.append('/app')
import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

def create_vector_embeddings():
    """Create vector embeddings for the CV document"""
    try:
        print('🔄 Creating vector embeddings for CV...')
        
        # Get the document
        conn = sqlite3.connect('/app/backend/data/webui.db')
        cursor = conn.cursor()
        cursor.execute("SELECT collection_name, content FROM document WHERE name LIKE '%Da Costa%' LIMIT 1")
        doc = cursor.fetchone()
        
        if not doc:
            print('❌ No document found')
            return
            
        collection_name, content = doc
        print(f'📂 Collection: {collection_name}')
        print(f'📄 Content length: {len(content)} chars')
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path='/app/backend/data/chroma')
        
        # Check if collection already exists
        try:
            collection = client.get_collection(collection_name)
            print(f'📋 Collection exists with {collection.count()} documents')
        except:
            # Create new collection
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "Juan-Pierre Da Costa CV 2025"}
            )
            print(f'📋 Created new collection: {collection_name}')
        
        # Initialize embedding model
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print('🧠 Embedding model loaded')
        
        # Split content into chunks (simple approach)
        chunk_size = 500
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i+chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        
        print(f'📝 Created {len(chunks)} chunks')
        
        # Generate embeddings
        if chunks:
            embeddings = model.encode(chunks)
            print(f'🔢 Generated {len(embeddings)} embeddings')
            
            # Prepare data for ChromaDB
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            metadatas = [{"chunk_index": i, "source": "CV"} for i in range(len(chunks))]
            
            # Add to ChromaDB
            collection.add(
                documents=chunks,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            print(f'✅ Added {len(chunks)} chunks to ChromaDB')
            print(f'📊 Collection now has {collection.count()} documents')
            
            # Test query
            test_query = "Juan-Pierre Da Costa experience"
            query_embedding = model.encode([test_query])
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=3
            )
            
            print(f'\n🔍 Test Query: "{test_query}"')
            print(f'📊 Found {len(results["documents"][0])} results')
            for i, doc in enumerate(results["documents"][0][:2]):
                print(f'  Result {i+1}: {doc[:100]}...')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_vector_embeddings()
    if success:
        print('\n🎉 CV is now ready for RAG queries!')
    else:
        print('\n❌ Failed to create embeddings')
