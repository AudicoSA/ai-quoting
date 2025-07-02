# Load environment variables first - MUST be at the top
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Now import everything else
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import List, Optional, Dict, Any
from app.db.sqlantern import sqlantern_db
import logging
from datetime import datetime
import uuid

# AI training imports - CORRECTED STRATEGY
try:
    import ai_training_engine
    ai_training_available = True
    print("✅ AI training engine imported successfully")
except ImportError as e:
    ai_training_engine = None
    ai_training_available = False
    print(f"⚠️ AI training engine not available: {e}")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Audico AI - Auto-Add Enhanced Quoting System with AI Training",
    description="Audio Equipment Solutions with Smart Auto-Add, Live Quoting, and AI Training",
    version="5.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Initialize AI training on startup - CORRECTED
@app.on_event("startup")
async def startup_event():
    """Initialize AI training on startup"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key and ai_training_available:
        try:
            result = ai_training_engine.initialize_ai_training(openai_api_key)
            if result:
                logger.info("🧠 AI Training System initialized successfully")
                # Debug verification
                print(f"DEBUG: document_intelligence = {ai_training_engine.document_intelligence is not None}")
                print(f"DEBUG: audio_consultant_ai = {ai_training_engine.audio_consultant_ai is not None}")
            else:
                logger.error("❌ AI Training System failed to initialize")
        except Exception as e:
            logger.error(f"AI Training initialization failed: {e}")
    else:
        if not openai_api_key:
            logger.warning("⚠️ OPENAI_API_KEY not set - AI training disabled")
        if not ai_training_available:
            logger.warning("⚠️ AI training engine not available")

# In-memory quote storage
active_quotes = {}

# Request models
class ChatMessage(BaseModel):
    message: str
    category: str
    quote_id: Optional[str] = None

class AddToQuoteRequest(BaseModel):
    product_id: int
    quantity: int = 1
    quote_id: Optional[str] = None

class QuoteItem(BaseModel):
    product_id: int
    name: str
    model: str
    price: float
    quantity: int
    total_price: float
    has_special_price: bool = False
    original_price: Optional[float] = None
    savings: Optional[float] = None

class Quote(BaseModel):
    quote_id: str
    items: List[QuoteItem]
    total_amount: float
    total_savings: float
    item_count: int
    created_at: str
    updated_at: str

@app.get("/")
async def root():
    return {
        "message": "Audico AI Auto-Add Enhanced Quoting System with AI Training", 
        "version": "5.0.0",
        "features": ["🎯 Smart Auto-Add", "💰 Fixed Special Pricing", "🔍 Working Search", "📦 Live Quotes", "🧠 AI Training"],
        "ai_training_available": ai_training_available
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Audico AI Auto-Add Backend with AI Training", 
        "version": "5.0.0",
        "ai_training_status": "available" if ai_training_available else "unavailable"
    }

async def auto_add_to_quote(product: Dict, quote_id: str, quantity: int = 1) -> Dict:
    """Automatically add product to quote"""
    try:
        if not quote_id:
            quote_id = str(uuid.uuid4())
        
        # Get full product details with pricing
        full_product = sqlantern_db.get_product_by_id(product['product_id'])
        
        if not full_product:
            return {"error": "Product not found"}
        
        # Create quote item with correct pricing
        final_price = full_product['price_zar']
        has_special = full_product.get('has_special_price', False)
        
        quote_item = QuoteItem(
            product_id=full_product['product_id'],
            name=full_product['name'],
            model=full_product.get('model', ''),
            price=final_price,
            quantity=quantity,
            total_price=final_price * quantity,
            has_special_price=has_special,
            original_price=full_product.get('original_price') if has_special else None,
            savings=full_product.get('savings', 0) * quantity if has_special else None
        )
        
        # Add to quote
        if quote_id not in active_quotes:
            active_quotes[quote_id] = {
                'quote_id': quote_id,
                'items': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        quote = active_quotes[quote_id]
        
        # Check if item already exists
        existing_item = None
        for item in quote['items']:
            if item['product_id'] == product['product_id']:
                existing_item = item
                break
        
        if existing_item:
            existing_item['quantity'] += quantity
            existing_item['total_price'] = existing_item['price'] * existing_item['quantity']
            if existing_item.get('savings'):
                existing_item['savings'] = (existing_item['original_price'] - existing_item['price']) * existing_item['quantity']
        else:
            quote['items'].append(quote_item.dict())
        
        quote['updated_at'] = datetime.now().isoformat()
        
        # Calculate totals
        total_amount = sum(item['total_price'] for item in quote['items'])
        total_savings = sum(item.get('savings', 0) or 0 for item in quote['items'])
        item_count = sum(item['quantity'] for item in quote['items'])
        
        return {
            "success": True,
            "quote_id": quote_id,
            "item_added": quote_item.dict(),
            "quote_summary": {
                "total_amount": total_amount,
                "total_savings": total_savings,
                "item_count": item_count,
                "items": len(quote['items'])
            }
        }
        
    except Exception as e:
        logger.error(f"Auto-add error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/chat")
async def enhanced_ai_chat_endpoint(chat_data: ChatMessage):
    """🧠 ENHANCED AI CHAT with training knowledge"""
    try:
        user_message = chat_data.message
        category = chat_data.category
        quote_id = chat_data.quote_id
        
        logger.info(f"🧠 AI ENHANCED CHAT: '{user_message}' for category: '{category}'")
        
        # Check if user wants to add a product
        if any(keyword in user_message.lower() for keyword in ["add", "quote", "price", "cost"]):
            # Extract search terms
            search_terms = []
            words = user_message.split()
            
            for word in words:
                if (len(word) > 2 and 
                    not word.lower() in ['please', 'pleasse', 'quote', 'price', 'cost', 'add', 'the', 'to', 'a', 'you', 'would', 'like', 'i', 'want', 'need']):
                    search_terms.append(word)
            
            if search_terms:
                exact_search = " ".join(search_terms)
                products = sqlantern_db.search_products(exact_search, limit=10, include_out_of_stock=False)
                
                if products:
                    best_match = products[0]
                    add_result = await auto_add_to_quote(best_match, quote_id)
                    
                    if add_result.get('success'):
                        # 🧠 ENHANCED: Use AI for professional response if available
                        response = None
                        if ai_training_available and ai_training_engine.audio_consultant_ai:
                            try:
                                response = await ai_training_engine.audio_consultant_ai.generate_professional_response(
                                    user_message, products, {"quote_added": True}, category
                                )
                            except Exception as e:
                                logger.error(f"AI response generation failed: {e}")
                                response = None
                        
                        # Fallback to original response if AI not available
                        if not response:
                            response = f"✅ **Added to Quote: {best_match['name']}**\n\n"
                            
                            if best_match.get('has_special_price'):
                                response += f"💰 **SPECIAL PRICE: {best_match['price_formatted']}** "
                                if best_match.get('original_price_formatted'):
                                    response += f"~~{best_match['original_price_formatted']}~~ "
                                if best_match.get('savings_formatted'):
                                    response += f"(Save {best_match['savings_formatted']}!) ⚡"
                                response += "\n"
                            else:
                                response += f"💰 Price: {best_match['price_formatted']}\n"
                            
                            response += f"📦 Quantity: 1\n"
                            response += f"🔢 Model: {best_match.get('model', 'N/A')}\n\n"
                            
                            # Quote summary
                            summary = add_result['quote_summary']
                            response += f"**Quote Total: R{summary['total_amount']:,.2f}**"
                            if summary['total_savings'] > 0:
                                response += f" (Save R{summary['total_savings']:,.2f}!)"
                            response += f"\n"
                            response += f"Items in quote: {summary['items']}\n\n"
                            response += "**Would you like to add anything else to complete your audio system?**"
                        
                        return {
                            "response": response,
                            "category": category,
                            "user_message": user_message,
                            "quote_id": add_result['quote_id'],
                            "item_added": add_result['item_added'],
                            "quote_summary": add_result['quote_summary'],
                            "auto_added": True,
                            "ai_enhanced": ai_training_available and ai_training_engine.audio_consultant_ai is not None,
                            "status": "success"
                        }
                    else:
                        return {
                            "response": f"❌ Sorry, I couldn't add '{best_match['name']}' to your quote right now. Please try again.",
                            "error": add_result.get('error'),
                            "status": "error"
                        }
                
                else:
                    # No products found - try broader search
                    broader_products = []
                    for term in search_terms:
                        if len(term) > 3:
                            broader = sqlantern_db.search_products(term, limit=3, include_out_of_stock=False)
                            broader_products.extend(broader)
                    
                    if broader_products:
                        response = f"❌ I couldn't find '{exact_search}' exactly, but found similar products:\n\n🔍 **Similar Products:**\n"
                        for product in broader_products[:3]:
                            response += f"\n• {product['name']} - {product['price_formatted']}"
                            if product.get('has_special_price'):
                                response += " ⚡ SPECIAL!"
                        response += f"\n\n💡 **Try searching with exact model numbers for better results.**"
                    else:
                        response = f"❌ I couldn't find '{exact_search}' in our current inventory.\n\n💡 **Search Tips:**\n• Try exact model numbers: 'AVR-X1800H' or 'AVRX1800H'\n• Use brand names: 'Denon', 'Yamaha'\n• Check spelling and try variations\n\n**What specific audio equipment are you looking for?**"
                    
                    return {
                        "response": response,
                        "category": category,
                        "user_message": user_message,
                        "search_type": "no_exact_match",
                        "auto_added": False,
                        "status": "no_results"
                    }
        
        # 🧠 ENHANCED: General queries use AI consultant if available
        else:
            response = None
            if ai_training_available and ai_training_engine.audio_consultant_ai:
                try:
                    response = await ai_training_engine.audio_consultant_ai.generate_professional_response(
                        user_message, [], {}, category
                    )
                except Exception as e:
                    logger.error(f"AI response generation failed: {e}")
            
            # Fallback to original response if AI not available
            if not response:
                response = f"👋 **Welcome to Audico AI for {category.title()}!**\n\n"
                response += "I'm here to help you build the perfect audio system with our latest inventory.\n\n"
                response += "🎯 **I can help you:**\n"
                response += "• Find and add products instantly (try: 'add Denon AVR-X1800H')\n"
                response += "• Get accurate pricing with special offers\n"
                response += "• Build and manage live quotes\n"
                response += "• Recommend complete audio solutions\n\n"
                response += "**What audio equipment are you looking for today?**\n\n"
                response += "💡 *Just say 'add [product name]' and I'll automatically add it to your quote!*"
            
            return {
                "response": response,
                "category": category,
                "user_message": user_message,
                "search_type": "ai_enhanced_welcome",
                "ai_enhanced": ai_training_available and ai_training_engine.audio_consultant_ai is not None,
                "status": "success"
            }
        
    except Exception as e:
        logger.error(f"Enhanced AI chat error: {str(e)}")
        return {
            "response": "I'm having trouble right now. Please try again.",
            "error": str(e),
            "status": "error"
        }

# CORRECTED training endpoints
@app.post("/api/v1/training/upload-document")
async def upload_training_document(file: UploadFile = File(...)):
    """Upload document for AI training"""
    if not ai_training_available:
        raise HTTPException(status_code=503, detail="AI training engine not available")
    
    if not ai_training_engine.document_intelligence:
        raise HTTPException(status_code=503, detail="AI training not initialized - missing OpenAI API key")
    
    try:
        result = await ai_training_engine.document_intelligence.process_document(file)
        
        # Update AI knowledge
        if ai_training_engine.audio_consultant_ai and result.get('categories') and result.get('relationships'):
            ai_training_engine.audio_consultant_ai.update_knowledge_base(
                result['categories'], 
                result['relationships']
            )
        
        return {
            "message": f"Document {file.filename} processed successfully",
            "result": result,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/training/knowledge-base")
async def get_knowledge_base():
    """Get current AI knowledge base"""
    if not ai_training_available:
        raise HTTPException(status_code=503, detail="AI training engine not available")
    
    if not ai_training_engine.audio_consultant_ai:
        raise HTTPException(status_code=503, detail="AI training not initialized - missing OpenAI API key")
    
    return {
        "knowledge_base": ai_training_engine.audio_consultant_ai.knowledge_base,
        "categories": list(ai_training_engine.audio_consultant_ai.knowledge_base.keys()),
        "total_items": sum(len(items) for items in ai_training_engine.audio_consultant_ai.knowledge_base.values()),
        "status": "success"
    }

@app.post("/api/v1/quotes/add-item")
async def add_item_to_quote(request: AddToQuoteRequest):
    """Manual add item to quote (for API calls)"""
    try:
        quote_id = request.quote_id or str(uuid.uuid4())
        
        # Get product details
        product = sqlantern_db.get_product_by_id(request.product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Use the auto-add function
        result = await auto_add_to_quote(product, quote_id, request.quantity)
        
        if result.get('success'):
            return {
                "message": "✅ Item added to quote successfully!",
                "quote_id": result['quote_id'],
                "item_added": result['item_added'],
                "quote_summary": {
                    "total_amount": f"R{result['quote_summary']['total_amount']:,.2f}",
                    "total_savings": f"R{result['quote_summary']['total_savings']:,.2f}" if result['quote_summary']['total_savings'] > 0 else None,
                    "item_count": result['quote_summary']['item_count'],
                    "items": result['quote_summary']['items']
                },
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to add item'))
        
    except Exception as e:
        logger.error(f"Error adding item to quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/quotes/{quote_id}")
async def get_quote(quote_id: str):
    """Get quote details"""
    try:
        if quote_id not in active_quotes:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote = active_quotes[quote_id]
        
        # Calculate totals
        total_amount = sum(item['total_price'] for item in quote['items'])
        total_savings = sum(item.get('savings', 0) or 0 for item in quote['items'])
        item_count = sum(item['quantity'] for item in quote['items'])
        
        return Quote(
            quote_id=quote_id,
            items=[QuoteItem(**item) for item in quote['items']],
            total_amount=total_amount,
            total_savings=total_savings,
            item_count=item_count,
            created_at=quote['created_at'],
            updated_at=quote['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/quotes/{quote_id}/items/{product_id}")
async def remove_item_from_quote(quote_id: str, product_id: int):
    """Remove item from quote"""
    try:
        if quote_id not in active_quotes:
            raise HTTPException(status_code=404, detail="Quote not found")
        
        quote = active_quotes[quote_id]
        
        # Find and remove item
        item_found = False
        for i, item in enumerate(quote['items']):
            if item['product_id'] == product_id:
                removed_item = quote['items'].pop(i)
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(status_code=404, detail="Item not found in quote")
        
        quote['updated_at'] = datetime.now().isoformat()
        
        # Calculate new totals
        total_amount = sum(item['total_price'] for item in quote['items'])
        total_savings = sum(item.get('savings', 0) or 0 for item in quote['items'])
        item_count = sum(item['quantity'] for item in quote['items'])
        
        return {
            "message": "Item removed from quote successfully",
            "removed_item": removed_item,
            "quote_summary": {
                "total_amount": f"R{total_amount:,.2f}",
                "total_savings": f"R{total_savings:,.2f}" if total_savings > 0 else None,
                "item_count": item_count,
                "items": len(quote['items'])
            },
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing item from quote: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/categories")
async def get_categories():
    """Get categories"""
    try:
        solution_categories = [
            {"id": "restaurants", "name": "Restaurants", "description": "Background music, zone control, dining atmosphere"},
            {"id": "home", "name": "Home", "description": "Home theater, music systems, hi-fi setups"},
            {"id": "office", "name": "Office", "description": "Conference rooms, background music, PA systems"},
            {"id": "gym", "name": "Gym", "description": "Fitness center audio, zone control, background music"},
            {"id": "worship", "name": "Place of Worship", "description": "Church sound systems, microphones, mixing"},
            {"id": "schools", "name": "Schools", "description": "Classroom audio, PA systems, sports facilities"},
            {"id": "educational", "name": "Educational", "description": "Lecture halls, university campus, training centers"},
            {"id": "tenders", "name": "Tenders", "description": "Large projects, commercial installations"}
        ]
        
        return {"solution_categories": solution_categories, "product_categories": []}
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return {"solution_categories": solution_categories, "product_categories": []}

@app.get("/api/v1/quotes")
async def list_quotes():
    """List all active quotes"""
    try:
        quotes_summary = []
        for quote_id, quote in active_quotes.items():
            total_amount = sum(item['total_price'] for item in quote['items'])
            total_savings = sum(item.get('savings', 0) or 0 for item in quote['items'])
            item_count = sum(item['quantity'] for item in quote['items'])
            
            quotes_summary.append({
                "quote_id": quote_id,
                "total_amount": f"R{total_amount:,.2f}",
                "total_savings": f"R{total_savings:,.2f}" if total_savings > 0 else None,
                "item_count": item_count,
                "items": len(quote['items']),
                "created_at": quote['created_at'],
                "updated_at": quote['updated_at']
            })
        
        return {
            "quotes": quotes_summary,
            "total_quotes": len(active_quotes),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error listing quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Audico AI AUTO-ADD Enhanced Backend with AI Training...")
    print("📊 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n🎯 FEATURES:")
    print("✅ SMART AUTO-ADD: Just say 'add denon avrx1800h' - no more choosing!")
    print("✅ FIXED PRICING: R15,990 special price displays correctly")
    print("✅ BETTER UX: Instant add to quote with confirmation")
    print("✅ CLEAN SEARCH: No more 'pleasse' or 'product' confusion")
    print("🧠 AI TRAINING: Upload documents and enhance AI responses")
    print("\n💬 Try these:")
    print("• 'add denon avrx1800h'")
    print("• 'add yamaha rx-v6a'")
    print("• 'add polk speakers'")
    print("\n🧠 AI Training Endpoints:")
    print("• POST /api/v1/training/upload-document")
    print("• GET /api/v1/training/knowledge-base")
    print("\n🎉 Your customers will love the AI-enhanced experience!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)