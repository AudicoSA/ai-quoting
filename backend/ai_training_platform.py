# ai_training_platform.py - AI Training Platform for Audico AI
import os
import json
import hashlib
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Advanced document processing for AI training"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
        
    async def process_uploaded_file(self, file: UploadFile, document_type: str, uploaded_by: str = "system") -> Dict[str, Any]:
        """Process uploaded file and extract training data"""
        try:
            # Save file
            file_path = self.upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Calculate file hash
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Extract content based on file type
            extracted_content = await self.extract_content(file_path, file.content_type)
            
            # Save to database
            document_id = await self.save_document_to_db(
                document_name=file.filename,
                document_type=document_type,
                file_path=str(file_path),
                file_size=len(content),
                file_hash=file_hash,
                content_text=extracted_content['text'],
                metadata=extracted_content['metadata'],
                uploaded_by=uploaded_by
            )
            
            # Process content for AI training
            await self.process_content_for_ai(document_id, extracted_content)
            
            return {
                "document_id": document_id,
                "filename": file.filename,
                "size": len(content),
                "content_preview": extracted_content['text'][:500] + "..." if len(extracted_content['text']) > 500 else extracted_content['text'],
                "metadata": extracted_content['metadata'],
                "status": "processed"
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")
    
    async def extract_content(self, file_path: Path, content_type: str) -> Dict[str, Any]:
        """Extract content from different file types"""
        try:
            if content_type == "application/pdf":
                return await self.extract_pdf_content(file_path)
            elif content_type in ["application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
                return await self.extract_excel_content(file_path)
            elif content_type == "text/csv":
                return await self.extract_csv_content(file_path)
            elif content_type == "text/plain":
                return await self.extract_text_content(file_path)
            else:
                raise ValueError(f"Unsupported file type: {content_type}")
                
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def extract_pdf_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF files"""
        try:
            import PyPDF2
            
            text_content = []
            metadata = {"pages": 0, "type": "pdf"}
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{text}")
            
            return {
                "text": "\n\n".join(text_content),
                "metadata": metadata
            }
            
        except ImportError:
            logger.warning("PyPDF2 not installed, using basic text extraction")
            return {"text": "PDF processing requires PyPDF2 package", "metadata": {"error": "missing_dependency"}}
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def extract_excel_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from Excel files"""
        try:
            # Read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            
            content_parts = []
            metadata = {"sheets": list(excel_data.keys()), "type": "excel"}
            
            for sheet_name, df in excel_data.items():
                content_parts.append(f"[Sheet: {sheet_name}]")
                
                # Extract headers
                headers = df.columns.tolist()
                content_parts.append(f"Columns: {', '.join(map(str, headers))}")
                
                # Extract sample data
                if not df.empty:
                    # Convert to string representation that preserves structure
                    for idx, row in df.head(10).iterrows():  # First 10 rows
                        row_data = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                        content_parts.append(row_data)
                
                content_parts.append("")  # Empty line between sheets
            
            metadata["total_rows"] = sum(len(df) for df in excel_data.values())
            metadata["total_columns"] = sum(len(df.columns) for df in excel_data.values())
            
            return {
                "text": "\n".join(content_parts),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Excel extraction error: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def extract_csv_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from CSV files"""
        try:
            df = pd.read_csv(file_path)
            
            content_parts = []
            content_parts.append(f"Columns: {', '.join(df.columns)}")
            
            # Extract sample data
            for idx, row in df.head(20).iterrows():  # First 20 rows
                row_data = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                content_parts.append(row_data)
            
            metadata = {
                "type": "csv",
                "rows": len(df),
                "columns": list(df.columns)
            }
            
            return {
                "text": "\n".join(content_parts),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"CSV extraction error: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def extract_text_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            metadata = {
                "type": "text",
                "char_count": len(content),
                "line_count": content.count('\n') + 1
            }
            
            return {
                "text": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def save_document_to_db(self, **kwargs) -> int:
        """Save document information to database"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            insert_sql = """
            INSERT INTO ai_training_documents 
            (document_name, document_type, file_path, file_size, file_hash, 
             content_text, metadata, uploaded_by, processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'completed')
            """
            
            values = (
                kwargs['document_name'],
                kwargs['document_type'],
                kwargs['file_path'],
                kwargs['file_size'],
                kwargs['file_hash'],
                kwargs['content_text'],
                json.dumps(kwargs['metadata']),
                kwargs['uploaded_by']
            )
            
            cursor.execute(insert_sql, values)
            document_id = cursor.lastrowid
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return document_id
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
            raise
    
    async def process_content_for_ai(self, document_id: int, content: Dict[str, Any]):
        """Process content into chunks for AI training"""
        try:
            text = content['text']
            
            # Split into chunks (simple implementation)
            chunk_size = 1000  # characters
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            for idx, chunk_text in enumerate(chunks):
                if chunk_text.strip():  # Only save non-empty chunks
                    insert_sql = """
                    INSERT INTO ai_training_chunks 
                    (document_id, chunk_index, chunk_text, chunk_metadata, token_count)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    
                    chunk_metadata = {
                        "document_type": content['metadata'].get('type', 'unknown'),
                        "chunk_size": len(chunk_text),
                        "has_product_data": self.detect_product_data(chunk_text)
                    }
                    
                    values = (
                        document_id,
                        idx,
                        chunk_text,
                        json.dumps(chunk_metadata),
                        len(chunk_text.split())  # Simple word count
                    )
                    
                    cursor.execute(insert_sql, values)
            
            connection.commit()
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"Content processing error: {e}")
            raise
    
    def detect_product_data(self, text: str) -> bool:
        """Detect if text contains product-related information"""
        product_indicators = [
            'model', 'price', 'specification', 'watt', 'frequency', 'impedance',
            'amplifier', 'speaker', 'receiver', 'subwoofer', 'tweeter', 'driver',
            'channel', 'stereo', 'surround', 'thd', 'snr', 'rms'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in product_indicators)

class AITrainingManager:
    """Manage AI training processes"""
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.document_processor = DocumentProcessor(db_config)
    
    async def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Get training progress
            cursor.execute("SELECT * FROM ai_training_progress ORDER BY created_at DESC")
            training_progress = cursor.fetchall()
            
            # Get document statistics
            cursor.execute("""
                SELECT 
                    document_type,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM ai_training_documents 
                WHERE processing_status = 'completed'
                GROUP BY document_type
            """)
            document_stats = cursor.fetchall()
            
            # Get chunk statistics
            cursor.execute("SELECT COUNT(*) as total_chunks FROM ai_training_chunks")
            chunk_stats = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return {
                "training_progress": training_progress,
                "document_statistics": document_stats,
                "chunk_statistics": chunk_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting training status: {e}")
            return {"error": str(e)}
    
    async def get_documents(self, limit: int = 50) -> List[Dict]:
        """Get list of training documents"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    id, document_name, document_type, file_size,
                    processing_status, uploaded_by, upload_date,
                    (SELECT COUNT(*) FROM ai_training_chunks WHERE document_id = ai_training_documents.id) as chunk_count
                FROM ai_training_documents 
                ORDER BY upload_date DESC 
                LIMIT %s
            """, (limit,))
            
            documents = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []

# Global instances
db_config = {
    'host': 'dedi159.cpt4.host-h.net',
    'database': 'audicdmyde_db__359',
    'user': 'audicdmyde_314',
    'password': '4hG4xcGS3tSgX76o5FSv',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True
}

ai_training_manager = AITrainingManager(db_config)
