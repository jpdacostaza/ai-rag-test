#!/usr/bin/env python3
"""
Smart RAG Query Filter - Eliminates duplicate results from multiple collections
"""
import chromadb
import sqlite3
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict

class SmartRAGFilter:
    def __init__(self, db_path: str = '/app/backend/data/webui.db', 
                 chroma_path: str = '/app/backend/data/chroma',
                 similarity_threshold: float = 0.95):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.similarity_threshold = similarity_threshold
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
    def get_user_collections(self, user_id: str) -> List[str]:
        """Get all document collections for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT collection_name 
            FROM document 
            WHERE user_id = ?
        ''', (user_id,))
        
        collections = [row[0] for row in cursor.fetchall()]
        conn.close()
        return collections
    
    def query_all_collections(self, user_id: str, query: str, n_results: int = 10) -> List[Dict]:
        """
        Query all user collections and return deduplicated results
        """
        collections = self.get_user_collections(user_id)
        
        if not collections:
            return []
        
        print(f'🔍 Querying {len(collections)} collections for user {user_id[:8]}...')
        
        # Collect results from all collections
        all_results = []
        
        try:
            client = chromadb.PersistentClient(path=self.chroma_path)
            
            for collection_name in collections:
                try:
                    collection = client.get_collection(collection_name)
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results,
                        include=['documents', 'metadatas', 'distances']
                    )
                    
                    if results['documents'][0]:
                        for i, (doc, metadata, distance) in enumerate(zip(
                            results['documents'][0],
                            results['metadatas'][0],
                            results['distances'][0]
                        )):
                            all_results.append({
                                'content': doc,
                                'metadata': metadata,
                                'distance': distance,
                                'collection': collection_name,
                                'rank': i
                            })
                            
                except Exception as e:
                    print(f'⚠️  Error querying collection {collection_name}: {e}')
            
        except Exception as e:
            print(f'❌ ChromaDB error: {e}')
            return []
        
        # Apply smart filtering
        filtered_results = self._filter_duplicates(all_results)
        
        # Sort by relevance score
        filtered_results.sort(key=lambda x: x['distance'])
        
        return filtered_results[:n_results]
    
    def _filter_duplicates(self, results: List[Dict]) -> List[Dict]:
        """
        Filter out duplicate content using semantic similarity
        """
        if len(results) <= 1:
            return results
        
        print(f'📊 Filtering {len(results)} results for duplicates...')
        
        # Group by content similarity
        unique_results = []
        content_groups = defaultdict(list)
        
        # First pass: exact content matches
        seen_content = set()
        for result in results:
            content = result['content'].strip()
            if content not in seen_content:
                seen_content.add(content)
                content_groups['exact'].append(result)
            else:
                # This is an exact duplicate
                content_groups['duplicates'].append(result)
        
        # Second pass: semantic similarity for near-duplicates
        filtered_by_similarity = []
        
        for result in content_groups['exact']:
            is_duplicate = False
            
            for existing in filtered_by_similarity:
                similarity = self._calculate_similarity(
                    result['content'], 
                    existing['content']
                )
                
                if similarity > self.similarity_threshold:
                    # This is a semantic duplicate
                    is_duplicate = True
                    
                    # Keep the one with better distance score
                    if result['distance'] < existing['distance']:
                        # Replace existing with better result
                        idx = filtered_by_similarity.index(existing)
                        filtered_by_similarity[idx] = result
                        print(f'🔄 Replaced duplicate with better match (similarity: {similarity:.3f})')
                    else:
                        print(f'🗑️  Filtered duplicate (similarity: {similarity:.3f})')
                    break
            
            if not is_duplicate:
                filtered_by_similarity.append(result)
        
        # Add metadata about filtering
        for result in filtered_by_similarity:
            result['filtered'] = True
            result['duplicate_count'] = len([r for r in results if 
                                           self._calculate_similarity(r['content'], result['content']) > self.similarity_threshold])
        
        print(f'✅ Filtered {len(results)} → {len(filtered_by_similarity)} unique results')
        return filtered_by_similarity
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            embeddings = self.model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            
            return float(similarity)
        except:
            # Fallback to simple text comparison
            return 1.0 if text1.strip() == text2.strip() else 0.0
    
    def analyze_collection_overlap(self, user_id: str) -> Dict:
        """
        Analyze content overlap between user's collections
        """
        collections = self.get_user_collections(user_id)
        
        if len(collections) < 2:
            return {'overlap': 0, 'collections': len(collections)}
        
        print(f'🔍 Analyzing overlap between {len(collections)} collections...')
        
        # Sample content from each collection
        collection_samples = {}
        
        try:
            client = chromadb.PersistentClient(path=self.chroma_path)
            
            for collection_name in collections:
                try:
                    collection = client.get_collection(collection_name)
                    sample = collection.get(limit=10, include=['documents'])
                    
                    if sample['documents']:
                        collection_samples[collection_name] = sample['documents']
                        
                except Exception as e:
                    print(f'⚠️  Error sampling {collection_name}: {e}')
        
        except Exception as e:
            print(f'❌ ChromaDB error: {e}')
            return {'error': str(e)}
        
        # Calculate overlap
        total_comparisons = 0
        duplicate_count = 0
        
        collection_names = list(collection_samples.keys())
        for i in range(len(collection_names)):
            for j in range(i + 1, len(collection_names)):
                col1_name = collection_names[i]
                col2_name = collection_names[j]
                
                col1_docs = collection_samples[col1_name]
                col2_docs = collection_samples[col2_name]
                
                for doc1 in col1_docs:
                    for doc2 in col2_docs:
                        total_comparisons += 1
                        similarity = self._calculate_similarity(doc1, doc2)
                        
                        if similarity > self.similarity_threshold:
                            duplicate_count += 1
        
        overlap_percentage = (duplicate_count / total_comparisons * 100) if total_comparisons > 0 else 0
        
        return {
            'collections': len(collections),
            'total_comparisons': total_comparisons,
            'duplicates_found': duplicate_count,
            'overlap_percentage': overlap_percentage,
            'recommendation': self._get_overlap_recommendation(overlap_percentage)
        }
    
    def _get_overlap_recommendation(self, overlap_percentage: float) -> str:
        """Get recommendation based on overlap percentage"""
        if overlap_percentage > 80:
            return "High overlap detected - consider removing duplicate collections"
        elif overlap_percentage > 50:
            return "Moderate overlap - review for potential duplicates"
        elif overlap_percentage > 20:
            return "Some overlap detected - normal for related documents"
        else:
            return "Low overlap - collections contain unique content"

def demo_smart_rag_filtering():
    """Demonstrate the smart RAG filtering system"""
    print('🧠 SMART RAG FILTERING DEMO')
    print('=' * 35)
    
    rag_filter = SmartRAGFilter()
    user_id = "e7e39ee3-b886-4f92-8fb2-fbeb524fe5ce"
    
    print(f'👤 User: {user_id[:8]}...')
    print()
    
    # Test query
    query = "experience with systems administration"
    print(f'🔍 Query: "{query}"')
    print()
    
    # Get filtered results
    results = rag_filter.query_all_collections(user_id, query, n_results=5)
    
    print('🎯 FILTERED RESULTS:')
    for i, result in enumerate(results, 1):
        collection_short = result['collection'][-8:]
        duplicate_count = result.get('duplicate_count', 1)
        
        print(f'   {i}. Score: {result["distance"]:.4f} | Collection: {collection_short}')
        print(f'      Content: {result["content"][:80]}...')
        print(f'      Source: {result["metadata"].get("source", "Unknown")}')
        if duplicate_count > 1:
            print(f'      📊 Represents {duplicate_count} similar results')
        print()
    
    # Analyze collection overlap
    print('📊 COLLECTION OVERLAP ANALYSIS:')
    overlap_analysis = rag_filter.analyze_collection_overlap(user_id)
    
    if 'error' not in overlap_analysis:
        print(f'   Collections analyzed: {overlap_analysis["collections"]}')
        print(f'   Content comparisons: {overlap_analysis["total_comparisons"]}')
        print(f'   Duplicates found: {overlap_analysis["duplicates_found"]}')
        print(f'   Overlap percentage: {overlap_analysis["overlap_percentage"]:.1f}%')
        print(f'   💡 {overlap_analysis["recommendation"]}')

if __name__ == "__main__":
    demo_smart_rag_filtering()
