"""
Resume text extraction service
Supports PDF, DOCX, and plain text
"""
from typing import Optional, Union
from pathlib import Path
import io
from app.core import logger


class ResumeParserService:
    """Service for extracting text from resume files."""
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_bytes: PDF file content as bytes
        
        Returns:
            Extracted text
        
        Raises:
            ValueError: If text extraction fails or PDF is scanned/image-only
        """
        try:
            from PyPDF2 import PdfReader
            
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
            
            if not text_parts:
                raise ValueError("No text could be extracted from PDF. It may be a scanned/image-only document.")
            
            return "\n\n".join(text_parts)
        
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @staticmethod
    def extract_from_docx(file_bytes: bytes) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_bytes: DOCX file content as bytes
        
        Returns:
            Extracted text
        
        Raises:
            ValueError: If text extraction fails
        """
        try:
            from docx import Document
            
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            
            if not paragraphs:
                raise ValueError("No text could be extracted from DOCX file.")
            
            return "\n\n".join(paragraphs)
        
        except Exception as e:
            logger.error(f"DOCX extraction failed: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    
    @staticmethod
    def extract_from_text(file_bytes: bytes) -> str:
        """
        Extract text from plain text file.
        
        Args:
            file_bytes: Text file content as bytes
        
        Returns:
            Decoded text
        """
        try:
            # Try UTF-8 first, fall back to other encodings
            try:
                return file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return file_bytes.decode('latin-1')
        
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise ValueError(f"Failed to read text file: {str(e)}")
    
    @classmethod
    def extract_resume(
        cls, 
        file_bytes: bytes, 
        filename: str,
        file_content_type: Optional[str] = None
    ) -> str:
        """
        Extract text from resume file based on file type.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            file_content_type: MIME type (optional, used for validation)
        
        Returns:
            Extracted text
        
        Raises:
            ValueError: If file type is unsupported or extraction fails
        """
        # Determine file type from extension
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.pdf':
            return cls.extract_from_pdf(file_bytes)
        elif file_ext in ['.docx', '.doc']:
            if file_ext == '.doc':
                logger.warning("DOC format (not DOCX) may have limited support")
            return cls.extract_from_docx(file_bytes)
        elif file_ext in ['.txt', '.md']:
            return cls.extract_from_text(file_bytes)
        else:
            raise ValueError(
                f"Unsupported file type: {file_ext}. "
                "Supported formats: PDF, DOCX, TXT, MD"
            )
    
    @classmethod
    def validate_file(cls, file_bytes: bytes, filename: str, max_size_mb: int = 10) -> bool:
        """
        Validate uploaded file.
        
        Args:
            file_bytes: File content
            filename: Original filename
            max_size_mb: Maximum file size in MB
        
        Returns:
            True if valid
        
        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > max_size_mb:
            raise ValueError(f"File too large: {size_mb:.2f}MB (max: {max_size_mb}MB)")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in ['.pdf', '.docx', '.doc', '.txt', '.md']:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Basic magic number check for PDF
        if file_ext == '.pdf' and not file_bytes.startswith(b'%PDF'):
            raise ValueError("Invalid PDF file")
        
        return True


# Singleton instance
_resume_parser_service: Optional[ResumeParserService] = None


def get_resume_parser_service() -> ResumeParserService:
    """Get or create ResumeParserService singleton."""
    global _resume_parser_service
    if _resume_parser_service is None:
        _resume_parser_service = ResumeParserService()
    return _resume_parser_service
