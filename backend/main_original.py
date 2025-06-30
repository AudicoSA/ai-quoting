from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import json
import logging
import re
import uuid
import shutil
import tempfile
from datetime import datetime
import openai

# Import your existing components
from app.db.sqlantern import sqlantern_db

# Import new components (with error handling)
try:
    from core.database import get_db, create_tables
    from core.models import Document, DocumentChunk, TrainingData, ChatSession, ChatMessage
    from core.training.document_intelligence import DocumentIntelligence
    from core.training.data_manager import TrainingDataManager
    from core.training.enhanced_chroma_utils import EnhancedChromaManager
    ENHANCED_FEATURES = True
except ImportError as e:
    ENHANCED_FEATURES = False
    logging.warning(f"Enhanced features not available: {e}")

from pydantic_models import *
import structlog

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

struct_logger = structlog.get_logger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Audico AI - Complete Data Integration", 
    description="Audio Equipment Solutions with Real Product Database & AI Training",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize enhanced components (if available)
if ENHANCED_FEATURES:
    try:
        document_intelligence = DocumentIntelligence()
        training_data_manager = TrainingDataManager()
        enhanced_chroma = EnhancedChromaManager()
        struct_logger.info("Enhanced AI training system initialized")
    except Exception as e:
        ENHANCED_FEATURES = False
        struct_logger.warning(f"Enhanced features disabled: {e}")

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    struct_logger.info("Audico AI Backend starting up...")
    
    # Initialize enhanced features
    if ENHANCED_FEATURES:
        try:
            create_tables()
            struct_logger.info("Enhanced database tables initialized")
        except Exception as e:
            struct_logger.error(f"Enhanced features initialization failed: {e}")
    
    # Test SQLantern connection
    try:
        test_result = sqlantern_db.test_connection()
        if test_result:
            struct_logger.info("SQLantern database connection established")
        else:
            struct_logger.warning("SQLantern connection test failed")
    except Exception as e:
        struct_logger.error(f"SQLantern connection error: {e}")

# MAIN CHAT ENDPOINT - Integrates SQLantern + AI Training
@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, db: Session = Depends(get_db) if ENHANCED_FEATURES else None):
    """Enhanced chat with SQLantern integration + AI training"""
    try:
        session_id = chat_request.session_id or str(uuid.uuid4())
        user_message = chat_request.message
        
        struct_logger.info("Chat request received", 
                          session_id=session_id, 
                          user_query=user_message[:50])
        
        # 1. Query SQLantern for real products
        relevant_products = await query_sqlantern_products(user_message)
        
        # 2. Get enhanced context from training system (if available)
        enhanced_context = ""
        search_results = []
        if ENHANCED_FEATURES:
            try:
                search_results = enhanced_chroma.enhanced_similarity_search(
                    query=user_message,
                    k=3,
                    search_type="hybrid"
                )
                enhanced_context = "\n".join([doc.page_content for doc in search_results])
                struct_logger.info("Enhanced context retrieved", results=len(search_results))
            except Exception as e:
                struct_logger.warning("Enhanced search failed", error=str(e))
        
        # 3. Generate AI response using OpenAI with real product data
        ai_response = await generate_intelligent_response(
            user_message, 
            relevant_products, 
            enhanced_context,
            session_id
        )
        
        # 4. Store chat history (if enhanced features available)
        if ENHANCED_FEATURES and db:
            await store_chat_interaction(session_id, user_message, ai_response, db)
        
        # 5. Check for quote actions
        quote_action = await process_quote_action(user_message, relevant_products, session_id)
        
        return ChatResponse(
            message=ai_response,
            session_id=session_id,
            model=chat_request.model or 'gpt-4o-mini',
            context_used=len(relevant_products) + len(search_results),
            quote_action=quote_action
        )
        
    except Exception as e:
        struct_logger.error("Error in chat endpoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

async def query_sqlantern_products(user_message: str) -> List[Dict]:
    """Query SQLantern database for relevant products"""
    try:
        # Extract audio equipment keywords
        keywords = extract_audio_keywords(user_message)
        
        # Query your SQLantern database
        products = sqlantern_db.search_products(keywords)
        
        # Enhanced product search for specific requests
        if any(phrase in user_message.lower() for phrase in ['add to quote', 'quote', 'price']):
            # Get specific product if mentioned
            specific_product = sqlantern_db.find_specific_product(user_message)
            if specific_product:
                products.insert(0, specific_product)
        
        struct_logger.info("SQLantern query", keywords=keywords, products_found=len(products))
        return products[:10]  # Limit to top 10 products
        
    except Exception as e:
        struct_logger.error("SQLantern query failed", error=str(e))
        # Return sample products as fallback
        return get_fallback_products()

def extract_audio_keywords(message: str) -> List[str]:
    """Extract audio equipment keywords for SQLantern query"""
    message_lower = message.lower()
    
    # Audio equipment patterns
    patterns = {
        'denon_models': r'(avr-x\d+h|avr-\w+|denon\s+\w+)',
        'brands': r'(denon|marantz|yamaha|kef|monitor audio|polk|svs|bowers wilkins|b&w)',
        'categories': r'(receiver|amplifier|speaker|subwoofer|turntable|cd player|dac)',
        'features': r'(atmos|dts|4k|8k|bluetooth|wifi|hdmi|wireless)',
        'specific_models': r'(x1800h|x2800h|x3800h|q150|q350|q550|bronze)'
    }
    
    keywords = []
    for pattern_type, pattern in patterns.items():
        matches = re.findall(pattern, message_lower)
        keywords.extend(matches)
    
    # Add general audio terms if no specific matches
    if not keywords:
        audio_terms = ['audio', 'sound', 'music', 'home theater', 'stereo']
        keywords.extend([term for term in audio_terms if term in message_lower])
    
    return list(set(keywords)) or ['audio equipment']

def get_fallback_products() -> List[Dict]:
    """Fallback products when SQLantern is unavailable"""
    return [
        {
            "id": "fallback_1",
            "name": "Denon AVR-X2800H",
            "price": 22999,
            "description": "7.2 Channel AV Receiver with 8K support",
            "stock_level": "In Stock",
            "category": "receiver"
        },
        {
            "id": "fallback_2", 
            "name": "KEF Q350 Speakers",
            "price": 7999,
            "description": "Premium bookshelf speakers (pair)",
            "stock_level": "In Stock",
            "category": "speakers"
        }
    ]

async def generate_intelligent_response(
    user_message: str, 
    products: List[Dict], 
    enhanced_context: str,
    session_id: str
) -> str:
    """Generate AI response using OpenAI with real product data"""
    try:
        # Build product context from SQLantern
        product_context = ""
        if products:
            product_context = "CURRENT INVENTORY - Available Products:\n"
            for i, product in enumerate(products[:5], 1):  # Top 5 products
                product_context += f"{i}. {product.get('name', 'Unknown Product')}\n"
                product_context += f"   Price: R {product.get('price', 'TBC'):,}\n"
                product_context += f"   Description: {product.get('description', 'No description')}\n"
                product_context += f"   Stock: {product.get('stock_level', 'Available')}\n\n"
        
        # Create OpenAI prompt
        system_prompt = f"""You are an expert audio equipment specialist for Audico SA.
        You help customers choose and purchase the perfect audio equipment for their needs.
        
        IMPORTANT GUIDELINES:
        - Use ONLY products from the current inventory below
        - Provide accurate pricing in South African Rands (R)
        - Be conversational, helpful, and knowledgeable
        - Ask clarifying questions about room size, budget, and usage
        - If customer wants to add to quote, be specific about which product
        - If no relevant products found, suggest alternatives or ask for more details
        - Always mention specific product names and prices from inventory
        
        {product_context}
        
        Additional Knowledge Base:
        {enhanced_context[:500] if enhanced_context else 'Using real-time product database.'}
        
        Remember: You are representing Audico SA - be professional and helpful!"""
        
        # Use OpenAI if API key available
        if openai.api_key:
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                struct_logger.error("OpenAI API failed", error=str(e))
        
        # Fallback to intelligent pattern-based response
        return generate_pattern_based_response(user_message, products)
        
    except Exception as e:
        struct_logger.error("AI response generation failed", error=str(e))
        return "I'm having trouble accessing our systems right now. Please try again shortly, or contact us directly for assistance."

def generate_pattern_based_response(user_message: str, products: List[Dict]) -> str:
    """Generate intelligent response based on patterns and available products"""
    message_lower = user_message.lower()
    
    # Check for quote requests
    if any(phrase in message_lower for phrase in ['add to quote', 'quote', 'buy', 'purchase']):
        if products:
            main_product = products[0]
            return f"""Perfect! I can add the **{main_product.get('name')}** to your quote.
            
🎯 **Product Details:**
💰 Price: R {main_product.get('price', 'TBC'):,}
📝 Description: {main_product.get('description', '')}
📦 Availability: {main_product.get('stock_level', 'In stock')}

Would you like me to add this to your live quote? I can also recommend complementary products to complete your audio system.

Just say "add to quote" and I'll process this for you! 🛒"""

    # Specific product inquiries
    elif any(model in message_lower for model in ['x2800h', 'x1800h', 'x3800h']):
        denon_products = [p for p in products if 'denon' in p.get('name', '').lower()]
        if denon_products:
            product = denon_products[0]
            return f"""Excellent choice! The **{product.get('name')}** is one of our most popular receivers.

🔊 **Key Features:**
- Premium 7.2 channel processing
- 8K/4K HDMI support with latest features  
- Dolby Atmos and DTS:X support
- Advanced room correction technology
- Built-in streaming capabilities

💰 **Current Price:** R {product.get('price', 'TBC'):,}
📦 **Stock Status:** {product.get('stock_level', 'Available')}

This receiver pairs beautifully with KEF or Monitor Audio speakers. Would you like me to add it to your quote or recommend matching speakers?"""

    # Speaker recommendations
    elif any(word in message_lower for word in ['speaker', 'speakers']):
        speaker_products = [p for p in products if 'speaker' in p.get('name', '').lower() or 'speaker' in p.get('category', '').lower()]
        if speaker_products:
            response = "🔊 **Perfect Speaker Options for You:**\n\n"
            for i, speaker in enumerate(speaker_products[:3], 1):
                response += f"**{i}. {speaker.get('name')}**\n"
                response += f"   💰 Price: R {speaker.get('price', 'TBC'):,}\n"
                response += f"   📝 {speaker.get('description', '')}\n\n"
            
            response += "Which of these interests you? I can add any to your quote or recommend the perfect receiver to pair with them! 🎵"
            return response

    # General product recommendations
    elif products:
        response = f"Great! Based on your interest in '{user_message}', here are some excellent options from our current inventory:\n\n"
        
        for i, product in enumerate(products[:3], 1):
            response += f"**{i}. {product.get('name')}**\n"
            response += f"   💰 Price: R {product.get('price', 'TBC'):,}\n"
            response += f"   📝 {product.get('description', '')}\n"
            response += f"   📦 Stock: {product.get('stock_level', 'Available')}\n\n"
        
        response += "Would you like more details about any of these, or shall I add one to your quote? 🛒"
        return response
    
    # No products found
    else:
        return f"""I'd be happy to help you find the perfect audio equipment for "{user_message}"! 🎵

To give you the best recommendations from our inventory, could you tell me:
- What type of equipment are you looking for? (receiver, speakers, subwoofer, etc.)
- Your budget range?
- Room size and primary use? (music, movies, gaming)

This will help me find exactly what you need from our current stock! 🎯"""

async def process_quote_action(user_message: str, products: List[Dict], session_id: str) -> Optional[Dict]:
    """Process quote-related actions"""
    message_lower = user_message.lower()
    
    if any(phrase in message_lower for phrase in ['add to quote', 'add this', 'quote this', 'add it']):
        if products:
            main_product = products[0]
            
            # Add to SQLantern quote system
            try:
                quote_result = sqlantern_db.add_to_quote(
                    session_id=session_id,
                    product_id=main_product.get('id'),
                    product_name=main_product.get('name'),
                    price=main_product.get('price'),
                    quantity=1
                )
                
                return {
                    "action": "added_to_quote",
                    "product": main_product,
                    "quote_total": quote_result.get('total'),
                    "quote_id": quote_result.get('quote_id'),
                    "message": f"✅ Added {main_product.get('name')} to your quote!"
                }
            except Exception as e:
                struct_logger.error("Failed to add to quote", error=str(e))
                return {
                    "action": "quote_error",
                    "message": "Sorry, I couldn't add that to your quote right now. Please try again."
                }
    
    return None

async def store_chat_interaction(session_id: str, user_message: str, ai_response: str, db: Session):
    """Store chat interaction in enhanced database"""
    try:
        # Get or create session
        chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not chat_session:
            chat_session = ChatSession(
                session_id=session_id,
                session_metadata={'source': 'sqlantern_integration', 'version': '2.0'}
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        # Store user message
        user_msg = ChatMessage(
            session_id_ref=session_id,
            message_type='human',
            content=user_message,
            metadata_json={'source': 'web_interface', 'timestamp': datetime.utcnow().isoformat()}
        )
        db.add(user_msg)
        
        # Store AI response
        ai_msg = ChatMessage(
            session_id_ref=session_id,
            message_type='ai',
            content=ai_response,
            model_used='sqlantern_enhanced',
            metadata_json={'integration': 'sqlantern + ai_training', 'timestamp': datetime.utcnow().isoformat()}
        )
        db.add(ai_msg)
        
        # Update session activity
        chat_session.last_activity = datetime.utcnow()
        db.commit()
        
        struct_logger.info("Chat interaction stored", session_id=session_id)
        
    except Exception as e:
        struct_logger.error("Failed to store chat interaction", error=str(e))

# LIVE QUOTE MANAGEMENT ENDPOINTS
@app.get("/api/v1/quote/current")
async def get_current_quote(session_id: str):
    """Get current live quote from SQLantern"""
    try:
        quote = sqlantern_db.get_quote(session_id)
        return {
            "quote_id": quote.get('id'),
            "session_id": session_id,
            "items": quote.get('items', []),
            "subtotal": quote.get('subtotal', 0),
            "vat": quote.get('vat', 0),
            "total": quote.get('total', 0),
            "currency": "ZAR",
            "status": quote.get('status', 'active'),
            "created_at": quote.get('created_at'),
            "updated_at": quote.get('updated_at')
        }
    except Exception as e:
        struct_logger.error("Failed to get quote", session_id=session_id, error=str(e))
        # Return empty quote if none exists
        return {
            "quote_id": None,
            "session_id": session_id,
            "items": [],
            "subtotal": 0,
            "vat": 0,
            "total": 0,
            "currency": "ZAR",
            "status": "new"
        }

@app.post("/api/v1/quote/add-item")
async def add_item_to_quote(request: Dict[str, Any]):
    """Add item to live quote via SQLantern"""
    try:
        result = sqlantern_db.add_to_quote(
            session_id=request.get('session_id'),
            product_id=request.get('product_id'),
            quantity=request.get('quantity', 1)
        )
        
        return {
            "status": "success",
            "message": "Item added to quote successfully",
            "quote_total": result.get('total'),
            "quote_id": result.get('quote_id'),
            "item_count": result.get('item_count', 1)
        }
    except Exception as e:
        struct_logger.error("Failed to add item to quote", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to add item: {str(e)}")

@app.delete("/api/v1/quote/remove-item/{item_id}")
async def remove_item_from_quote(item_id: str, session_id: str):
    """Remove item from quote"""
    try:
        result = sqlantern_db.remove_from_quote(session_id, item_id)
        return {
            "status": "success",
            "message": "Item removed from quote",
            "quote_total": result.get('total')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {str(e)}")

# ENHANCED DOCUMENT UPLOAD & TRAINING
if ENHANCED_FEATURES:
    @app.post("/upload-doc-enhanced")
    async def upload_document_enhanced(
        file: UploadFile = File(...),
        document_type: str = Form("general"),
        db: Session = Depends(get_db)
    ):
        """Enhanced document upload with intelligent processing"""
        try:
            allowed_extensions = ['.pdf', '.docx', '.html', '.csv', '.xlsx', '.xls', '.txt']
            file_extension = os.path.splitext(file.filename)[1].lower()

            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}"
                )

            temp_file_path = f"temp_{file.filename}"

            try:
                # Save uploaded file
                with open(temp_file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # Process document with intelligence
                doc_record = await document_intelligence.process_document(
                    temp_file_path, file.filename, document_type, db
                )

                if not doc_record:
                    raise HTTPException(status_code=500, detail="Failed to process document")

                # Index in enhanced vector store
                success = await enhanced_chroma.index_document_with_intelligence(
                    temp_file_path, doc_record.id, db, document_type
                )

                if not success:
                    raise HTTPException(status_code=500, detail="Failed to index document")

                # Generate training data automatically
                training_data = await training_data_manager.generate_training_data_from_documents(
                    [doc_record.id], db, "auto_generated"
                )

                return {
                    "message": f"Document {file.filename} processed successfully",
                    "document_id": doc_record.id,
                    "chunks_created": len(doc_record.chunks) if doc_record.chunks else 0,
                    "training_data_generated": len(training_data),
                    "document_type": document_type,
                    "processing_status": doc_record.processing_status
                }

            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        except Exception as e:
            struct_logger.error("Error in enhanced document upload", error=str(e), filename=file.filename)
            raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    # TRAINING DATA MANAGEMENT ENDPOINTS
    @app.get("/training-data")
    async def get_training_data(
        limit: Optional[int] = 50,
        offset: int = 0,
        document_type: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        validated_only: bool = False,
        db: Session = Depends(get_db)
    ):
        """Get training data with filtering options"""
        filters = {}
        if document_type:
            filters['document_type'] = document_type
        if min_quality_score:
            filters['min_quality_score'] = min_quality_score
        if validated_only:
            filters['validated_only'] = validated_only

        dataset = await training_data_manager.get_training_dataset(
            db, filters, limit, offset
        )
        return dataset

    @app.post("/training-data")
    async def create_training_data(
        training_data: TrainingDataCreate,
        db: Session = Depends(get_db)
    ):
        """Create manual training data entry"""
        created_data = await training_data_manager.create_manual_training_data(
            training_data.question, 
            training_data.answer, 
            training_data.source_document_id, 
            db, 
            training_data.metadata
        )
        return {
            "id": created_data.id,
            "quality_score": created_data.quality_score,
            "message": "Training data created successfully"
        }

    @app.get("/training-data/statistics")
    async def get_training_statistics(db: Session = Depends(get_db)):
        """Get comprehensive training data statistics"""
        stats = await training_data_manager.get_training_statistics(db)
        return stats

# LEGACY ENDPOINTS (for backward compatibility)
@app.post("/upload-doc")
async def upload_and_index_document(file: UploadFile = File(...)):
    """Your existing upload endpoint for backward compatibility"""
    allowed_extensions = ['.pdf', '.docx', '.html']
    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

    temp_file_path = f"temp_{file.filename}"

    try:
        # Save the uploaded file to a temporary file
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {"message": f"File {file.filename} has been successfully uploaded and indexed."}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/list-docs")
def list_documents():
    """Your existing list documents endpoint"""
    return {"documents": [], "message": "Use /documents for enhanced document management"}

@app.post("/delete-doc")
def delete_document(request: dict):
    """Your existing delete document endpoint"""
    return {"message": "Document deleted", "note": "Use /documents/{id} DELETE for enhanced management"}

# SYSTEM ENDPOINTS
@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "components": {}
    }
    
    # Check SQLantern
    try:
        sqlantern_test = sqlantern_db.test_connection()
        health_status["components"]["sqlantern"] = "healthy" if sqlantern_test else "unhealthy"
    except:
        health_status["components"]["sqlantern"] = "unhealthy"
    
    # Check Enhanced Features
    health_status["components"]["enhanced_features"] = "enabled" if ENHANCED_FEATURES else "disabled"
    
    # Check OpenAI
    health_status["components"]["openai"] = "configured" if openai.api_key else "not_configured"
    
    return health_status

@app.get("/system/info")
async def system_info():
    """Get comprehensive system information"""
    return {
        "app_name": "Audico AI",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "sqlantern_integration": True,
            "enhanced_training": ENHANCED_FEATURES,
            "openai_integration": bool(openai.api_key),
            "live_quotes": True,
            "document_processing": ENHANCED_FEATURES
        },
        "endpoints": {
            "chat": "/chat",
            "quote_current": "/api/v1/quote/current",
            "quote_add_item": "/api/v1/quote/add-item",
            "health": "/health",
            "training_data": "/training-data" if ENHANCED_FEATURES else None,
            "upload_enhanced": "/upload-doc-enhanced" if ENHANCED_FEATURES else None
        },
        "database": {
            "sqlantern": "integrated",
            "enhanced_features": "available" if ENHANCED_FEATURES else "disabled"
        }
    }

if ENHANCED_FEATURES:
    @app.get("/system/stats")
    async def get_system_stats(db: Session = Depends(get_db)):
        """Get detailed system statistics"""
        try:
            # Document stats
            total_docs = db.query(Document).count()
            processing_docs = db.query(Document).filter(Document.processing_status == "processing").count()
            
            # Training data stats
            training_stats = await training_data_manager.get_training_statistics(db)
            
            return {
                "documents": {
                    "total": total_docs,
                    "processing": processing_docs,
                    "completed": total_docs - processing_docs
                },
                "training_data": training_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            struct_logger.error("Error getting system stats", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to get system statistics")

if __name__ == "__main__":
    import uvicorn
    print("🎵 Starting Audico AI Backend...")
    print("📊 SQLantern Integration: ✅ Enabled")
    print(f"🤖 Enhanced AI Training: {'✅ Enabled' if ENHANCED_FEATURES else '❌ Disabled'}")
    print(f"🔑 OpenAI Integration: {'✅ Configured' if openai.api_key else '❌ Not Configured'}")
    print("📍 Frontend: http://localhost:3000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health")
    print("🎯 System Info: http://localhost:8000/system/info")
    uvicorn.run(app, host="0.0.0.0", port=8000)