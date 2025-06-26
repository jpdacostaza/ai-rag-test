"""
Enhanced Document Processing System for RAG Pipeline
===================================================

This module provides advanced document processing capabilities including:
- Intelligent chunking strategies
- Semantic chunking based on content structure
- Multi-format document support
- Document quality assessment
- Adaptive chunk sizing
- Content summarization and metadata extraction
"""

import hashlib
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from langchain.text_splitter import RecursiveCharacterTextSplitter

from error_handler import MemoryErrorHandler
from human_logging import log_service_status


class ChunkingStrategy(Enum):
    """Different strategies for document chunking."""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    ADAPTIVE = "adaptive"
    HIERARCHICAL = "hierarchical"


class DocumentType(Enum):
    """Supported document types."""

    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"  # JSON, XML, etc.
    ACADEMIC = "academic"  # Research papers, articles
    CONVERSATION = "conversation"  # Chat logs, transcripts


@dataclass
class DocumentMetadata:
    """Metadata extracted from documents."""

    filename: str
    file_type: str
    size_bytes: int
    language: Optional[str] = None
    estimated_reading_time: Optional[int] = None  # in minutes
    topics: Optional[List[str]] = None
    complexity_score: float = 0.0  # 0-1 scale
    structure_score: float = 0.0  # How well-structured the document is
    quality_score: float = 0.0  # Overall quality assessment
    key_entities: Optional[List[str]] = None
    summary: Optional[str] = None


@dataclass
class ProcessedChunk:
    """A processed document chunk with enhanced metadata."""

    chunk_id: str
    text: str
    chunk_index: int
    strategy: ChunkingStrategy
    metadata: Dict[str, Any]
    embedding_preview: Optional[List[float]] = None
    quality_score: float = 0.0
    relationships: Optional[List[str]] = None  # IDs of related chunks


class DocumentAnalyzer:
    """Analyzes documents to determine optimal processing strategy."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.code_extensions = {".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml"}
        self.markdown_extensions = {".md", ".markdown", ".rst"}

        # Language detection patterns (simple heuristics)
        self.language_patterns = {
            "python": [r"def\s+\w+\(", r"import\s+\w+", r"from\s+\w+\s+import", r"class\s+\w+:"],
            "javascript": [r"function\s+\w+\(", r"const\s+\w+\s*=", r"var\s+\w+\s*=", r"=>"],
            "json": [r"^\s*\{", r"^\s*\[", r'"\w+":\s*'],
            "markdown": [r"^#+\s", r"\*\*\w+\*\*", r"\[.*\]\(.*\)", r"```"],
        }

    async def analyze_document(self, content: str, filename: str) -> Tuple[DocumentType, DocumentMetadata]:
        """Analyze document to determine type and extract metadata."""
        try:
            file_ext = os.path.splitext(filename)[1].lower()

            # Determine document type
            doc_type = self._classify_document_type(content, file_ext)

            # Extract metadata
            metadata = await self._extract_metadata(content, filename, doc_type)

            return doc_type, metadata

        except Exception:
            log_service_status("DOC_ANALYSIS", "error", "Document analysis failed: {e}")
            # Return default values
            return DocumentType.TEXT, DocumentMetadata(
                filename=filename, file_type="unknown", size_bytes=len(content.encode("utf-8"))
            )

    def _classify_document_type(self, content: str, file_ext: str) -> DocumentType:
        """Classify document type based on content and extension."""
        if file_ext in self.code_extensions:
            return DocumentType.CODE
        elif file_ext in self.markdown_extensions:
            return DocumentType.MARKDOWN

        # Content-based detection
        content_lower = content.lower()

        # Check for academic patterns
        academic_indicators = [
            "abstract",
            "introduction",
            "methodology",
            "results",
            "conclusion",
            "references",
        ]
        if sum(1 for indicator in academic_indicators if indicator in content_lower) >= 3:
            return DocumentType.ACADEMIC

        # Check for structured data
        if content.strip().startswith(("{", "[", "<")):
            return DocumentType.STRUCTURED

        # Check for conversation patterns
        conversation_indicators = ["user:", "assistant:", "human:", "ai:", "q:", "a:"]
        if sum(1 for indicator in conversation_indicators if indicator in content_lower) >= 2:
            return DocumentType.CONVERSATION

        return DocumentType.TEXT

    async def _extract_metadata(self, content: str, filename: str, doc_type: DocumentType) -> DocumentMetadata:
        """Extract comprehensive metadata from document."""
        size_bytes = len(content.encode("utf-8"))

        # Detect language
        language = self._detect_language(content)

        # Estimate reading time (average 200 words per minute)
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)

        # Calculate complexity score
        complexity = self._calculate_complexity(content)

        # Calculate structure score
        structure = self._calculate_structure_score(content, doc_type)

        # Extract topics (simple keyword-based)
        topics = await self._extract_topics(content)

        # Extract key entities (simple approach)
        entities = self._extract_entities(content)

        # Generate summary for longer documents
        summary = await self._generate_summary(content) if len(content) > 1000 else None

        # Calculate overall quality score
        quality = (complexity + structure) / 2

        return DocumentMetadata(
            filename=filename,
            file_type=doc_type.value,
            size_bytes=size_bytes,
            language=language,
            estimated_reading_time=reading_time,
            topics=topics,
            complexity_score=complexity,
            structure_score=structure,
            quality_score=quality,
            key_entities=entities,
            summary=summary,
        )

    def _detect_language(self, content: str) -> Optional[str]:
        """Detect programming/markup language based on patterns."""
        for language, patterns in self.language_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, content, re.MULTILINE))
            if matches >= 2:
                return language
        return None

    def _calculate_complexity(self, content: str) -> float:
        """Calculate content complexity score (0-1)."""
        # Factors: sentence length, vocabulary diversity, technical terms
        sentences = re.split(r"[.!?]+", content)
        if not sentences:
            return 0.0

        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Vocabulary diversity (unique words / total words)
        words = content.lower().split()
        vocab_diversity = len(set(words)) / max(len(words), 1)

        # Technical term indicators
        technical_indicators = [
            "api",
            "database",
            "algorithm",
            "function",
            "parameter",
            "implementation",
        ]
        tech_score = sum(1 for term in technical_indicators if term in content.lower()) / len(technical_indicators)

        # Normalize and combine scores
        length_score = min(avg_sentence_length / 20, 1.0)  # Normalize by 20 words

        return (length_score + vocab_diversity + tech_score) / 3

    def _calculate_structure_score(self, content: str, doc_type: DocumentType) -> float:
        """Calculate how well-structured the document is."""
        if doc_type == DocumentType.MARKDOWN:
            # Count headers, lists, code blocks
            headers = len(re.findall(r"^#+\s", content, re.MULTILINE))
            lists = len(re.findall(r"^\s*[-*+]\s", content, re.MULTILINE))
            code_blocks = len(re.findall(r"```", content))

            structure_elements = headers + lists + (code_blocks // 2)  # Code blocks come in pairs
            return min(structure_elements / 10, 1.0)  # Normalize

        elif doc_type == DocumentType.CODE:
            # Count functions, classes, comments
            functions = len(re.findall(r"def\s+\w+|function\s+\w+", content))
            classes = len(re.findall(r"class\s+\w+", content))
            comments = len(re.findall(r"#.*|//.*|/\*.*\*/", content))

            structure_elements = functions + classes + (comments // 5)  # Comments are less significant
            return min(structure_elements / 10, 1.0)

        else:
            # For other types, look for paragraph structure
            paragraphs = len(re.split(r"\n\s*\n", content.strip()))
            return min(paragraphs / 20, 1.0)

    async def _extract_topics(self, content: str) -> List[str]:
        """Extract topics from content using keyword analysis."""
        # This is a simplified version - in production, use NLP models
        topic_keywords = {
            "programming": ["code", "function", "variable", "algorithm", "programming", "software"],
            "data_science": [
                "data",
                "analysis",
                "model",
                "dataset",
                "machine learning",
                "statistics",
            ],
            "web_development": ["html", "css", "javascript", "frontend", "backend", "api"],
            "business": ["market", "strategy", "revenue", "customer", "business", "management"],
            "science": ["research", "study", "experiment", "hypothesis", "methodology", "results"],
            "technology": ["system", "network", "database", "server", "cloud", "infrastructure"],
        }

        content_lower = content.lower()
        found_topics = []

        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score >= 2:  # Threshold for topic relevance
                found_topics.append(topic)

        return found_topics[:5]  # Return top 5 topics

    def _extract_entities(self, content: str) -> List[str]:
        """Extract key entities (simplified approach)."""
        # Look for capitalized words that might be entities
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", content)

        # Filter out common words
        common_words = {
            "The",
            "This",
            "That",
            "And",
            "But",
            "For",
            "With",
            "From",
            "Into",
            "During",
        }
        entities = [e for e in entities if e not in common_words]

        # Return unique entities, limited to top 10
        return list(set(entities))[:10]

    async def _generate_summary(self, content: str) -> Optional[str]:
        """Generate a brief summary of the document."""
        # Simple extractive summarization - take first few sentences
        sentences = re.split(r"[.!?]+", content)
        if len(sentences) < 3:
            return None

        # Take first 2-3 sentences as summary
        summary_sentences = sentences[:3]
        summary = ". ".join(s.strip() for s in summary_sentences if s.strip())

        return summary[:300] + "..." if len(summary) > 300 else summary


class EnhancedChunker:
    """Advanced document chunking with multiple strategies."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.analyzer = DocumentAnalyzer()

        # Initialize different splitters
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        self.semantic_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ". ", " "],
        )

        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\nclass ", "\n\ndef ", "\n\nfunction ", "\n\n", "\n", " "],
        )

    async def process_document(
        self, content: str, filename: str, user_id: str, strategy: Optional[ChunkingStrategy] = None
    ) -> List[ProcessedChunk]:
        """Process document with enhanced chunking and metadata extraction."""
        try:
            # Analyze document
            doc_type, metadata = await self.analyzer.analyze_document(content, filename)

            # Determine chunking strategy
            if strategy is None:
                strategy = self._select_optimal_strategy(doc_type, len(content))

            # Chunk the document
            chunks = await self._chunk_document(content, strategy, doc_type)

            # Process each chunk
            processed_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk = await self._create_processed_chunk(chunk_text, i, strategy, metadata, filename, user_id)
                processed_chunks.append(chunk)

            log_service_status(
                "DOC_PROCESSING",
                "ready",
                "Processed {filename}: {len(processed_chunks)} chunks using {strategy.value} strategy",
            )

            return processed_chunks

        except Exception as e:
            log_service_status("DOC_PROCESSING", "error", f"Error in enhanced chunking for {filename}: {e}")
            MemoryErrorHandler.handle_memory_error(e, "enhanced_chunking", user_id)
            # Fallback to simple chunking
            return await self._fallback_processing(content, filename, user_id)

    def _select_optimal_strategy(self, doc_type: DocumentType, content_length: int) -> ChunkingStrategy:
        """Select optimal chunking strategy based on document characteristics."""
        if doc_type == DocumentType.CODE:
            return ChunkingStrategy.SEMANTIC if content_length > 5000 else ChunkingStrategy.FIXED_SIZE

        elif doc_type == DocumentType.ACADEMIC:
            return ChunkingStrategy.HIERARCHICAL

        elif doc_type == DocumentType.CONVERSATION:
            return ChunkingStrategy.PARAGRAPH

        elif doc_type == DocumentType.MARKDOWN:
            return ChunkingStrategy.SEMANTIC

        elif content_length > 10000:
            return ChunkingStrategy.ADAPTIVE

        else:
            return ChunkingStrategy.FIXED_SIZE

    async def _chunk_document(self, content: str, strategy: ChunkingStrategy, doc_type: DocumentType) -> List[str]:
        """Chunk document using specified strategy."""
        if strategy == ChunkingStrategy.SEMANTIC:
            return await self._semantic_chunking(content, doc_type)

        elif strategy == ChunkingStrategy.PARAGRAPH:
            return self._paragraph_chunking(content)

        elif strategy == ChunkingStrategy.HIERARCHICAL:
            return await self._hierarchical_chunking(content)

        elif strategy == ChunkingStrategy.ADAPTIVE:
            return await self._adaptive_chunking(content)

        else:  # FIXED_SIZE
            return self._fixed_size_chunking(content, doc_type)

    def _fixed_size_chunking(self, content: str, doc_type: DocumentType) -> List[str]:
        """Traditional fixed-size chunking with document-aware separators."""
        if doc_type == DocumentType.CODE:
            return self.code_splitter.split_text(content)
        else:
            return self.recursive_splitter.split_text(content)

    async def _semantic_chunking(self, content: str, doc_type: DocumentType) -> List[str]:
        """Semantic chunking that preserves meaning boundaries."""
        # First, split into potential chunks
        initial_chunks = self.semantic_splitter.split_text(content)

        # For code, try to keep functions/classes together
        if doc_type == DocumentType.CODE:
            return self._code_aware_chunking(initial_chunks)

        # For other types, combine related chunks
        return await self._combine_related_chunks(initial_chunks)

    def _paragraph_chunking(self, content: str) -> List[str]:
        """Chunk by paragraphs, combining small ones."""
        paragraphs = re.split(r"\n\s*\n", content.strip())
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph would make chunk too large, start new
            # chunk
            if len(current_chunk) + len(para) > 1000 and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    async def _hierarchical_chunking(self, content: str) -> List[str]:
        """Hierarchical chunking for structured documents."""
        # Look for section headers
        sections = re.split(r"\n(?=#{1,3}\s)", content)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # If section is too large, sub-chunk it
            if len(section) > 1500:
                sub_chunks = self.recursive_splitter.split_text(section)
                chunks.extend(sub_chunks)
            else:
                chunks.append(section)

        return chunks

    async def _adaptive_chunking(self, content: str) -> List[str]:
        """Adaptive chunking that adjusts size based on content density."""
        # Analyze content density (sentences per paragraph, etc.)
        paragraphs = re.split(r"\n\s*\n", content.strip())

        chunks = []
        current_chunk = ""
        target_size = 1000

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Adjust target size based on paragraph complexity
            sentences = len(re.split(r"[.!?]+", para))
            if sentences > 5:  # Dense paragraph
                target_size = 800
            else:  # Simple paragraph
                target_size = 1200

            if len(current_chunk) + len(para) > target_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _code_aware_chunking(self, chunks: List[str]) -> List[str]:
        """Refine chunks to keep code structures intact."""
        refined_chunks = []

        for chunk in chunks:
            # Check if chunk breaks in the middle of a function/class
            if self._breaks_code_structure(chunk):
                # Try to extend or split at better boundaries
                adjusted = self._adjust_code_boundaries(chunk)
                refined_chunks.extend(adjusted)
            else:
                refined_chunks.append(chunk)

        return refined_chunks

    def _breaks_code_structure(self, chunk: str) -> bool:
        """Check if chunk breaks code structure."""
        # Simple heuristics
        open_braces = chunk.count("{")
        close_braces = chunk.count("}")

        # If braces don't match, likely breaks structure
        return abs(open_braces - close_braces) > 1

    def _adjust_code_boundaries(self, chunk: str) -> List[str]:
        """Adjust chunk boundaries to preserve code structure."""
        # Find function/class boundaries
        boundaries = []

        for i, line in enumerate(chunk.split("\n")):
            if re.match(r"^\s*(def|class|function)\s", line):
                boundaries.append(i)

        if boundaries:
            # Split at function boundaries
            lines = chunk.split("\n")
            chunks = []
            start = 0

            for boundary in boundaries[1:]:  # Skip first boundary
                chunks.append("\n".join(lines[start:boundary]))
                start = boundary

            chunks.append("\n".join(lines[start:]))  # Last chunk
            return [c for c in chunks if c.strip()]

        return [chunk]  # Return original if no good boundaries found

    async def _combine_related_chunks(self, chunks: List[str]) -> List[str]:
        """Combine semantically related chunks."""
        if len(chunks) <= 1:
            return chunks

        combined = []
        current_group = [chunks[0]]

        for i in range(1, len(chunks)):
            # Simple relatedness check based on keyword overlap
            similarity = self._calculate_chunk_similarity(chunks[i - 1], chunks[i])

            if similarity > 0.3 and len("\n".join(current_group + [chunks[i]])) < 1200:
                current_group.append(chunks[i])
            else:
                combined.append("\n\n".join(current_group))
                current_group = [chunks[i]]

        if current_group:
            combined.append("\n\n".join(current_group))

        return combined

    def _calculate_chunk_similarity(self, chunk1: str, chunk2: str) -> float:
        """Calculate simple similarity between chunks."""
        words1 = set(chunk1.lower().split())
        words2 = set(chunk2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    async def _create_processed_chunk(
        self,
        text: str,
        index: int,
        strategy: ChunkingStrategy,
        doc_metadata: DocumentMetadata,
        filename: str,
        user_id: str,
    ) -> ProcessedChunk:
        """Create a ProcessedChunk with full metadata."""
        chunk_id = f"{user_id}_{hashlib.md5((filename + str(index)).encode()).hexdigest()[:8]}"

        # Calculate chunk quality score
        quality = self._assess_chunk_quality(text, strategy)

        # Extract chunk-specific metadata
        chunk_metadata = {
            "source_document": filename,
            "document_type": doc_metadata.file_type,
            "language": doc_metadata.language,
            "topics": doc_metadata.topics,
            "word_count": len(text.split()),
            "character_count": len(text),
            "estimated_reading_time": max(1, len(text.split()) // 200),
            "chunk_strategy": strategy.value,
            "creation_timestamp": datetime.now().isoformat(),
        }

        return ProcessedChunk(
            chunk_id=chunk_id,
            text=text,
            chunk_index=index,
            strategy=strategy,
            metadata=chunk_metadata,
            quality_score=quality,
        )

    def _assess_chunk_quality(self, text: str, strategy: ChunkingStrategy) -> float:
        """Assess the quality of a chunk."""
        # Factors: completeness, coherence, information density

        # Completeness: Does it end with proper punctuation?
        completeness = 1.0 if text.strip().endswith((".", "!", "?", "```", "}", ")", "]")) else 0.7

        # Information density: ratio of meaningful words to total words
        words = text.split()
        meaningful_words = [
            w for w in words if len(w) > 3 and not w.lower() in {"the", "and", "that", "this", "with", "from"}
        ]
        density = len(meaningful_words) / max(len(words), 1)

        # Length appropriateness
        length_score = 1.0
        if len(text) < 100:
            length_score = 0.6  # Too short
        elif len(text) > 2000:
            length_score = 0.8  # Too long

        return (completeness + density + length_score) / 3

    async def _fallback_processing(self, content: str, filename: str, user_id: str) -> List[ProcessedChunk]:
        """Fallback to simple processing if enhanced processing fails."""
        chunks = self.recursive_splitter.split_text(content)

        processed_chunks = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{user_id}_{hashlib.md5((filename + str(i)).encode()).hexdigest()[:8]}"

            processed_chunk = ProcessedChunk(
                chunk_id=chunk_id,
                text=chunk_text,
                chunk_index=i,
                strategy=ChunkingStrategy.FIXED_SIZE,
                metadata={
                    "source_document": filename,
                    "word_count": len(chunk_text.split()),
                    "fallback_processing": True,
                },
                quality_score=0.5,
            )
            processed_chunks.append(processed_chunk)

        return processed_chunks


# Global enhanced chunker instance
enhanced_chunker = EnhancedChunker()
