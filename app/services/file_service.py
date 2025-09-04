"""
File Service for NeuraMatrix Local AI Kit
Handles file uploads, processing, and management
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from werkzeug.datastructures import FileStorage
import PyPDF2
from docx import Document
from app.models import db, FileUpload
from app.services.security_service import SecurityService

logger = logging.getLogger(__name__)


class FileServiceError(Exception):
    """Custom exception for file service errors"""
    pass


class FileService:
    """Service class for file operations"""
    
    def __init__(self, config):
        self.upload_folder = Path(config['UPLOAD_FOLDER'])
        self.max_file_size = config['MAX_CONTENT_LENGTH']
        self.allowed_extensions = config['ALLOWED_EXTENSIONS']
        
        # Ensure upload folder exists
        self.upload_folder.mkdir(parents=True, exist_ok=True)
    
    def process_upload(self, file: FileStorage, profile_id: int) -> Dict[str, Any]:
        """Process file upload"""
        try:
            # Validate filename
            is_valid, result = SecurityService.validate_filename(file.filename)
            if not is_valid:
                raise FileServiceError(result)
            
            secured_filename = result
            
            # Generate unique filename
            file_extension = secured_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = self.upload_folder / unique_filename
            
            # Save file
            file.save(str(file_path))
            
            # Validate file content
            is_valid, validation_result = SecurityService.validate_file_content(
                file_path, self.allowed_extensions
            )
            if not is_valid:
                # Delete invalid file
                file_path.unlink(missing_ok=True)
                raise FileServiceError(validation_result)
            
            # Get file info
            file_size = file_path.stat().st_size
            file_hash = SecurityService.hash_file(file_path)
            
            # Extract content
            content = self._extract_content(file_path, file_extension)
            
            # Create database record
            file_upload = FileUpload(
                profile_id=profile_id,
                original_filename=secured_filename,
                stored_filename=unique_filename,
                file_size=file_size,
                file_type=file_extension,
                file_hash=file_hash,
                processed=False
            )
            
            db.session.add(file_upload)
            db.session.commit()
            
            return {
                'file_id': file_upload.id,
                'filename': secured_filename,
                'stored_filename': unique_filename,
                'file_size': file_size,
                'file_type': file_extension,
                'file_hash': file_hash,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"File upload processing failed: {e}")
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink(missing_ok=True)
            raise FileServiceError(f"Upload processing failed: {str(e)}")
    
    def _extract_content(self, file_path: Path, file_extension: str) -> str:
        """Extract text content from uploaded file"""
        try:
            if file_extension == 'txt' or file_extension == 'md':
                return self._extract_text_content(file_path)
            elif file_extension == 'pdf':
                return self._extract_pdf_content(file_path)
            elif file_extension == 'docx':
                return self._extract_docx_content(file_path)
            else:
                logger.warning(f"Unsupported file type for content extraction: {file_extension}")
                return "Content extraction not supported for this file type."
                
        except Exception as e:
            logger.error(f"Content extraction failed for {file_path}: {e}")
            return f"Content extraction failed: {str(e)}"
    
    def _extract_text_content(self, file_path: Path) -> str:
        """Extract content from text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Limit content size
            if len(content) > 50000:  # 50KB limit
                content = content[:50000] + "\n\n[Content truncated due to size limit]"
            
            return content
            
        except UnicodeDecodeError:
            try:
                # Try with latin-1 encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                return content[:50000] if len(content) > 50000 else content
            except Exception as e:
                raise FileServiceError(f"Failed to read text file: {str(e)}")
    
    def _extract_pdf_content(self, file_path: Path) -> str:
        """Extract content from PDF files"""
        try:
            content = ""
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Limit to first 20 pages
                max_pages = min(len(pdf_reader.pages), 20)
                
                for page_num in range(max_pages):
                    try:
                        page = pdf_reader.pages[page_num]
                        content += page.extract_text() + "\n"
                        
                        # Stop if content gets too large
                        if len(content) > 50000:
                            content = content[:50000] + "\n\n[Content truncated due to size limit]"
                            break
                            
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num}: {e}")
                        continue
            
            return content.strip() if content else "No text content found in PDF"
            
        except Exception as e:
            raise FileServiceError(f"Failed to extract PDF content: {str(e)}")
    
    def _extract_docx_content(self, file_path: Path) -> str:
        """Extract content from DOCX files"""
        try:
            doc = Document(file_path)
            content = ""
            
            for paragraph in doc.paragraphs:
                content += paragraph.text + "\n"
                
                # Stop if content gets too large
                if len(content) > 50000:
                    content = content[:50000] + "\n\n[Content truncated due to size limit]"
                    break
            
            return content.strip() if content else "No text content found in document"
            
        except Exception as e:
            raise FileServiceError(f"Failed to extract DOCX content: {str(e)}")
    
    def get_file_path(self, stored_filename: str) -> Path:
        """Get full path to stored file"""
        return self.upload_folder / stored_filename
    
    def delete_file(self, stored_filename: str) -> bool:
        """Delete a stored file"""
        try:
            file_path = self.get_file_path(stored_filename)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {stored_filename}")
                return True
            else:
                logger.warning(f"File not found for deletion: {stored_filename}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {stored_filename}: {e}")
            return False
    
    def get_file_info(self, file_id: int, profile_id: int) -> Optional[Dict[str, Any]]:
        """Get file information"""
        try:
            file_upload = FileUpload.query.filter_by(
                id=file_id, 
                profile_id=profile_id
            ).first()
            
            if not file_upload:
                return None
            
            file_path = self.get_file_path(file_upload.stored_filename)
            
            return {
                'id': file_upload.id,
                'original_filename': file_upload.original_filename,
                'file_size': file_upload.file_size,
                'file_type': file_upload.file_type,
                'upload_timestamp': file_upload.upload_timestamp,
                'processed': file_upload.processed,
                'summary': file_upload.summary,
                'exists': file_path.exists()
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def cleanup_orphaned_files(self) -> Dict[str, Any]:
        """Clean up files that exist on disk but not in database"""
        try:
            # Get all stored filenames from database
            db_files = set()
            file_uploads = FileUpload.query.all()
            for upload in file_uploads:
                db_files.add(upload.stored_filename)
            
            # Get all files on disk
            disk_files = set()
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    disk_files.add(file_path.name)
            
            # Find orphaned files
            orphaned_files = disk_files - db_files
            
            # Delete orphaned files
            deleted_count = 0
            for filename in orphaned_files:
                try:
                    file_path = self.upload_folder / filename
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted orphaned file: {filename}")
                except Exception as e:
                    logger.error(f"Failed to delete orphaned file {filename}: {e}")
            
            return {
                'orphaned_found': len(orphaned_files),
                'deleted': deleted_count,
                'total_db_files': len(db_files),
                'total_disk_files': len(disk_files)
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {'error': str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.upload_folder.iterdir():
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            # Get database stats
            db_files = FileUpload.query.count()
            processed_files = FileUpload.query.filter_by(processed=True).count()
            
            return {
                'total_files_disk': total_files,
                'total_files_db': db_files,
                'processed_files': processed_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'upload_folder': str(self.upload_folder)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {'error': str(e)}