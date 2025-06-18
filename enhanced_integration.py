"""
Enhanced System Integration
==========================

This module integrates the adaptive learning and enhanced document processing
systems with the existing FastAPI backend. It provides:

1. Enhanced endpoints for document processing
2. Learning feedback collection
3. Adaptive user experience
4. Performance monitoring and insights
"""

from fastapi import APIRouter, HTTPException, Form, UploadFile, File, Depends, Request, status
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import time
import asyncio
from datetime import datetime

# Import our enhanced modules
from adaptive_learning import adaptive_learning_system, FeedbackType
from enhanced_document_processing import enhanced_chunker, ChunkingStrategy, DocumentType
from database import db_manager, index_document_chunks
from human_logging import log_service_status, log_error

# Create router for enhanced features
enhanced_router = APIRouter(prefix="/enhanced", tags=["enhanced"])


@enhanced_router.post("/document/upload-advanced")
async def upload_document_advanced(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    chunking_strategy: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload document with advanced processing capabilities."""
    try:
        start_time = time.time()
        
        # Validate file
        if file.size and file.size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large")
        
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Parse chunking strategy
        strategy = None
        if chunking_strategy:
            try:
                strategy = ChunkingStrategy(chunking_strategy)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid chunking strategy. Options: {[s.value for s in ChunkingStrategy]}"
                )
        # Process document with enhanced chunker
        processed_chunks = await enhanced_chunker.process_document(
            content=text,
            filename=file.filename or "unknown_file",
            user_id=user_id,
            strategy=strategy
        )

        # Store chunks in database using a single batch operation
        chunk_texts = [chunk.text for chunk in processed_chunks]
        doc_id = f"{user_id}_{file.filename}_{hash(text)}"

        success = index_document_chunks(
            db_manager=db_manager,
            user_id=user_id,
            doc_id=doc_id,
            name=file.filename or "unknown_file",
            chunks=chunk_texts
        )

        success_count = len(processed_chunks) if success else 0
        stored_chunks_details = []
        if success:
            stored_chunks_details = [{
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "quality_score": chunk.quality_score,
                "strategy": chunk.strategy.value,
                "metadata": chunk.metadata
            } for chunk in processed_chunks]

        processing_time = time.time() - start_time
        
        # Log the successful processing
        log_service_status(
            "ENHANCED_UPLOAD", "ready" if success else "error",
            f"Processed {file.filename or 'unknown_file'}: {success_count}/{len(processed_chunks)} chunks stored in {processing_time:.2f}s"
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": success,
                "message": "Document processed with advanced features",
                "data": {
                    "filename": file.filename,
                    "total_chunks": len(processed_chunks),
                    "stored_chunks": success_count,
                    "processing_time": round(processing_time, 2),
                    "chunks": stored_chunks_details,
                    "document_metadata": {
                        "strategy_used": processed_chunks[0].strategy.value if processed_chunks else "none",
                        "avg_quality_score": round(
                            sum(c.quality_score for c in processed_chunks) / len(processed_chunks), 2
                        ) if processed_chunks else 0
                    }
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "enhanced_upload")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@enhanced_router.post("/feedback/interaction")
async def submit_interaction_feedback(
    user_id: str = Form(...),
    conversation_id: str = Form(...),
    user_message: str = Form(...),
    assistant_response: str = Form(...),
    feedback_type: str = Form(...),
    response_time: float = Form(...),
    tools_used: Optional[str] = Form(None)  # JSON string of tool names
):
    """Submit feedback for an interaction to improve the learning system."""
    try:
        # Parse tools used
        tools_list = []
        if tools_used:
            try:
                import json
                tools_list = json.loads(tools_used)
            except json.JSONDecodeError:
                tools_list = [tools_used]  # Single tool as string
        
        # Validate feedback type
        try:
            feedback_enum = FeedbackType(feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid feedback type. Options: {[f.value for f in FeedbackType]}"
            )
        
        # Process the interaction through the learning system
        result = await adaptive_learning_system.process_interaction(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            response_time=response_time,
            tools_used=tools_list
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Feedback processed successfully",
                "learning_result": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "feedback_processing")
        raise HTTPException(status_code=500, detail=f"Feedback processing failed: {str(e)}")


@enhanced_router.get("/insights/user/{user_id}")
async def get_user_insights(user_id: str):
    """Get learning insights and analytics for a specific user."""
    try:
        insights = await adaptive_learning_system.get_user_insights(user_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": insights
            }
        )
        
    except Exception as e:
        log_error(e, "insights_retrieval")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve insights: {str(e)}")


@enhanced_router.get("/document/strategies")
async def get_chunking_strategies():
    """Get available document chunking strategies."""
    return {
        "strategies": [
            {
                "name": strategy.value,
                "description": _get_strategy_description(strategy)
            }
            for strategy in ChunkingStrategy
        ],
        "document_types": [
            {
                "name": doc_type.value,
                "description": _get_document_type_description(doc_type)
            }
            for doc_type in DocumentType
        ]
    }


@enhanced_router.get("/system/learning-status")
async def get_learning_system_status():
    """Get the current status of the learning system."""
    try:
        # Get some basic stats
        total_patterns = len(adaptive_learning_system.user_patterns)
        queue_size = len(adaptive_learning_system.knowledge_expansion_queue)
        
        return {
            "status": "active",
            "total_users_with_patterns": total_patterns,
            "knowledge_expansion_queue_size": queue_size,
            "learning_features": [
                "Interaction feedback analysis",
                "Automatic knowledge expansion",
                "User preference learning",
                "Context relevance scoring"
            ],
            "document_features": [
                "Intelligent chunking strategies",
                "Document type classification",
                "Quality assessment",
                "Metadata extraction"
            ]
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _get_strategy_description(strategy: ChunkingStrategy) -> str:
    """Get human-readable description for chunking strategy."""
    descriptions = {
        ChunkingStrategy.FIXED_SIZE: "Traditional fixed-size chunks with consistent overlap",
        ChunkingStrategy.SEMANTIC: "Intelligent chunking that preserves semantic boundaries",
        ChunkingStrategy.PARAGRAPH: "Chunk by paragraphs, combining small ones",
        ChunkingStrategy.SENTENCE: "Sentence-based chunking for fine-grained processing",
        ChunkingStrategy.ADAPTIVE: "Adaptive chunk sizing based on content density",
        ChunkingStrategy.HIERARCHICAL: "Structure-aware chunking for documents with headers"
    }
    return descriptions.get(strategy, "Custom chunking strategy")


def _get_document_type_description(doc_type: DocumentType) -> str:
    """Get human-readable description for document type."""
    descriptions = {
        DocumentType.TEXT: "Plain text documents and articles",
        DocumentType.CODE: "Source code files and technical documentation",
        DocumentType.MARKDOWN: "Markdown formatted documents",
        DocumentType.STRUCTURED: "JSON, XML, and other structured data formats",
        DocumentType.ACADEMIC: "Research papers, academic articles, and formal documents",
        DocumentType.CONVERSATION: "Chat logs, transcripts, and conversational data"
    }
    return descriptions.get(doc_type, "Generic document type")


# Example endpoint showing integration with existing chat functionality
@enhanced_router.post("/chat/enhanced")
async def enhanced_chat_endpoint(
    user_id: str = Form(...),
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    """Enhanced chat endpoint that integrates learning and adaptive features."""
    try:
        start_time = time.time()
        
        # This would integrate with your existing chat logic in main.py
        # For now, we'll show how the learning system would be integrated
        
        # 1. Get user insights to customize response
        user_insights = await adaptive_learning_system.get_user_insights(user_id)
        
        # 2. Customize response based on user preferences
        response_customization = {}
        if user_insights.get("status") == "success":
            insights_data = user_insights.get("insights", {})
            preferences = insights_data.get("preferences", {})
            
            # Adjust detail level based on user preferences
            detail_level = preferences.get("detail_level", 0.5)
            response_customization["detail_level"] = detail_level
            
            # Consider preferred tools
            preferred_tools = insights_data.get("preferred_tools", {})
            response_customization["preferred_tools"] = list(preferred_tools.keys())[:3]
        
        # 3. Process the message (this would call your existing chat logic)
        # response = await process_chat_message(user_id, message, response_customization)
        
        # For demonstration, we'll create a mock response
        mock_response = f"Enhanced response for user {user_id}: {message[:50]}..."
        response_time = time.time() - start_time
        
        # 4. Process interaction for learning (in background)
        conversation_id = conversation_id or f"conv_{user_id}_{int(time.time())}"
        
        asyncio.create_task(
            adaptive_learning_system.process_interaction(
                user_id=user_id,
                conversation_id=conversation_id,
                user_message=message,
                assistant_response=mock_response,
                response_time=response_time,
                tools_used=response_customization.get("preferred_tools", [])
            )
        )
        
        return {
            "success": True,
            "response": mock_response,
            "conversation_id": conversation_id,
            "customizations_applied": response_customization,
            "learning_enabled": True
        }
        
    except Exception as e:
        log_error(e, "enhanced_chat")
        raise HTTPException(status_code=500, detail=f"Enhanced chat failed: {str(e)}")


# Background task to start learning system
async def start_enhanced_background_tasks():
    """Start background tasks for enhanced features."""
    try:        # Import the background task function
        from adaptive_learning import start_learning_background_tasks
        
        # Start the learning background tasks
        asyncio.create_task(start_learning_background_tasks())
        
        log_service_status(
            "ENHANCED_SYSTEM", "ready", 
            "Enhanced learning and document processing systems initialized"
        )
        
    except Exception as e:
        log_service_status(
            "ENHANCED_SYSTEM", "error", 
            f"Failed to start enhanced background tasks: {e}"
        )
