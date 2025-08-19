#!/usr/bin/env python3
"""
Document Duplicate Analysis for OpenWebUI
"""

import sqlite3
from collections import Counter
import hashlib

def analyze_duplicates():
    conn = sqlite3.connect('/app/backend/data/webui.db')
    cursor = conn.cursor()

    print('🔬 DOCUMENT DUPLICATE ANALYSIS')
    print('=' * 40)

    # Get all documents with content
    cursor.execute('SELECT id, filename, title, content, timestamp FROM document ORDER BY timestamp')
    docs = cursor.fetchall()

    print(f'📊 Total documents: {len(docs)}')
    print()

    # Check filename duplicates
    filenames = [doc[1] for doc in docs if doc[1]]
    filename_counts = Counter(filenames)

    print('📁 FILENAME ANALYSIS:')
    for filename, count in filename_counts.items():
        if count > 1:
            print(f'   ⚠️  DUPLICATE: "{filename}" appears {count} times')
        else:
            print(f'   ✅ UNIQUE: "{filename}"')

    print()

    # Check content hash duplicates
    print('🔍 CONTENT HASH ANALYSIS:')
    content_hashes = {}
    for doc in docs:
        doc_id, filename, title, content, timestamp = doc
        if content:
            content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
            if content_hash in content_hashes:
                print(f'   ⚠️  DUPLICATE CONTENT DETECTED!')
                print(f'      Hash: {content_hash}')
                print(f'      Original: ID {content_hashes[content_hash]}')
                print(f'      Duplicate: ID {doc_id}')
            else:
                content_hashes[content_hash] = doc_id
                print(f'   ✅ UNIQUE CONTENT: ID {doc_id} - {content_hash}')
        else:
            print(f'   ❌ NO CONTENT: ID {doc_id}')

    print()
    print('📋 DETAILED DOCUMENT LIST:')
    for doc in docs:
        doc_id, filename, title, content, timestamp = doc
        content_size = len(content) if content else 0
        print(f'   ID: {doc_id}')
        print(f'   File: {filename}')
        print(f'   Title: {title}')
        print(f'   Content size: {content_size} chars')
        print(f'   Timestamp: {timestamp}')
        print(f'   ---')

    conn.close()

if __name__ == "__main__":
    analyze_duplicates()
