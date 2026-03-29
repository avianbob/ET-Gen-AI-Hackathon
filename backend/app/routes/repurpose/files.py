"""
File Upload API Routes - Upload and process internal documents.

Supports PDF upload, text extraction, ChromaDB ingestion, and summarization.
"""

import uuid
import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List

from app.schemas.repurpose_api import FileUploadResponse
from app.services.repurpose.llm.llm_factory import LLMFactory
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("api.files")
router = APIRouter()

# In-memory file registry (for demo purposes)
_uploaded_files: Dict[str, Dict[str, Any]] = {}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)) -> FileUploadResponse:
    """
    Upload a PDF document for the Internal Knowledge Agent.

    The file is processed: text extracted, chunked, and stored in ChromaDB
    for retrieval by the Internal Knowledge Agent.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Read file content
        content = await file.read()
        size = len(content)

        if size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")

        if size == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        file_id = f"file-{uuid.uuid4().hex[:12]}"
        logger.info(f"Uploading file: {file.filename} ({size} bytes) -> {file_id}")

        # Extract text from PDF
        text = _extract_pdf_text(content)

        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. File may be scanned/image-based.")

        # Chunk the text
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        logger.info(f"Extracted {len(chunks)} chunks from {file.filename}")

        # Store in ChromaDB
        chunks_stored = await _store_in_chromadb(file_id, file.filename, chunks)

        # Generate summary
        summary = await _generate_summary(text[:3000], file.filename)

        # Register file
        _uploaded_files[file_id] = {
            "filename": file.filename,
            "size_bytes": size,
            "chunks": chunks_stored,
            "summary": summary,
            "text_length": len(text),
        }

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size_bytes=size,
            status="processed",
            chunks=chunks_stored,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.get("/files")
async def list_files() -> List[Dict[str, Any]]:
    """List all uploaded files."""
    return [
        {
            "file_id": fid,
            "filename": info["filename"],
            "size_bytes": info["size_bytes"],
            "chunks": info["chunks"],
            "summary": info.get("summary", "")[:200],
        }
        for fid, info in _uploaded_files.items()
    ]


@router.get("/files/{file_id}/summary")
async def get_file_summary(file_id: str) -> Dict[str, Any]:
    """Get summary of an uploaded file."""
    if file_id not in _uploaded_files:
        raise HTTPException(status_code=404, detail="File not found")

    info = _uploaded_files[file_id]
    return {
        "file_id": file_id,
        "filename": info["filename"],
        "summary": info.get("summary", "No summary available"),
        "chunks": info["chunks"],
        "text_length": info.get("text_length", 0),
    }


def _extract_pdf_text(content: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2."""
    try:
        import io
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            logger.warning("PyPDF2 not installed, attempting pdfplumber")
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    return "\n\n".join(text_parts)
            except ImportError:
                logger.error("Neither PyPDF2 nor pdfplumber installed")
                return ""

        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n\n".join(text_parts)

    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return ""


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap

    return chunks


async def _store_in_chromadb(file_id: str, filename: str, chunks: List[str]) -> int:
    """Store text chunks in ChromaDB for RAG retrieval."""
    try:
        from app.services.repurpose.vector_store import get_knowledge_base
        kb = get_knowledge_base()

        ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"source": f"upload:{filename}", "file_id": file_id, "chunk_index": str(i), "type": "internal_document"}
            for i in range(len(chunks))
        ]

        success = kb.add_documents("repurposing_cases", documents=chunks, metadatas=metadatas, ids=ids)
        stored = len(chunks) if success else 0
        logger.info(f"Stored {stored}/{len(chunks)} chunks in ChromaDB for {filename}")
        return stored

    except Exception as e:
        logger.warning(f"ChromaDB storage failed: {e}")
        return 0


async def _generate_summary(text: str, filename: str) -> str:
    """Generate a summary of the document using LLM."""
    llm = LLMFactory.get_llm()
    if llm is None:
        # Return a basic extractive summary
        sentences = text.replace("\n", " ").split(".")
        key_sentences = [s.strip() for s in sentences[:5] if len(s.strip()) > 20]
        return ". ".join(key_sentences) + "." if key_sentences else "Document uploaded successfully."

    try:
        prompt = f"""Summarize the following pharmaceutical document in 3-5 bullet points.
Focus on: key findings, drug names, indications, strategic recommendations, and data highlights.

Document: {filename}

Content (first 3000 chars):
{text[:3000]}

Provide a concise summary with bullet points:"""

        summary = await llm.generate(prompt)
        return summary

    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return "Document uploaded and indexed successfully. Use the chat to ask questions about its content."
