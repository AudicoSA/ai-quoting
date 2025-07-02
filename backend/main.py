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

# NEW: Pricing configuration model
class PricingConfigModel(BaseModel):
    price_type: str = "cost_excl_vat"
    vat_rate: float = 0.15
    markup_percentage: float = 0.40
    supplier_name: str = ""
    currency: str = "ZAR"

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

# EXISTING training endpoints
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

# NEW: Enhanced training endpoints for pricing configuration
@app.post("/api/v1/training/preview-document")
async def preview_training_document(file: UploadFile = File(...), config: str = ""):
    """Preview document processing without actually training"""
    if not ai_training_available:
        raise HTTPException(status_code=503, detail="AI training not available")
    
    try:
        # Parse config if provided
        pricing_config = {}
        if config:
            try:
                pricing_config = json.loads(config)
            except:
                pricing_config = {}
        
        # Basic preview for Excel files
        if file.filename.endswith(('.xlsx', '.xls')):
            content = await file.read()
            
            try:
                import pandas as pd
                from io import BytesIO
                
                df = pd.read_excel(BytesIO(content), header=None)
                
                # Detect brands in first few rows
                brands_detected = []
                brand_patterns = ['YEALINK', 'JABRA', 'DNAKE', 'CALL4TEL', 'LG', 'SHELLY', 'MIKROTIK', 'ZYXEL', 'NETOGY', 'TP-LINK', 'VILO', 'CAMBIUM', 'BLUETTI', 'MOTOROLA', 'NEAT', 'LOGITECH', 'TELRAD', 'HUAWEI', 'TELTONIKA', 'SAMSUNG']
                
                for row_idx in range(min(5, len(df))):
                    for col_idx in range(len(df.columns)):
                        try:
                            cell_value = str(df.iloc[row_idx, col_idx]).strip().upper()
                            
                            for brand in brand_patterns:
                                if brand in cell_value and brand not in brands_detected and len(cell_value) < 30:
                                    brands_detected.append(brand)
                                    break
                        except:
                            continue
                
                # Create sample products with pricing calculations
                products_sample = []
                if len(brands_detected) > 0:
                    vat_rate = pricing_config.get('vat_rate', 0.15)
                    markup = pricing_config.get('markup_percentage', 0.15)
                    
                    sample_data = [
                        {'product_code': 'EVOLVE-20', 'brand': 'JABRA', 'original_price': 890},
                        {'product_code': '16WALIC', 'brand': 'YEALINK', 'original_price': 0},
                        {'product_code': '280M-S8', 'brand': 'DNAKE', 'original_price': 1029}
                    ]
                    
                    for product in sample_data:
                        if product['brand'] in brands_detected:
                            original = product['original_price']
                            if original > 0:
                                if pricing_config.get('price_type') == 'cost_excl_vat':
                                    cost_excl = original
                                    cost_incl = cost_excl * (1 + vat_rate)
                                    retail_incl = cost_incl * (1 + markup)
                                else:
                                    cost_excl = original
                                    retail_incl = original * 1.61  # Default calculation
                                
                                product.update({
                                    'price_excl_vat': round(cost_excl, 2),
                                    'retail_incl_vat': round(retail_incl, 2)
                                })
                            else:
                                product.update({
                                    'price_excl_vat': 0,
                                    'retail_incl_vat': 0
                                })
                            
                            products_sample.append(product)
                
                return {
                    "brands_detected": brands_detected,
                    "products_sample": products_sample,
                    "estimated_products": len(brands_detected) * 30,
                    "config_applied": pricing_config,
                    "status": "preview_success"
                }
                
            except Exception as e:
                logger.error(f"Excel preview error: {e}")
                # Fallback preview
                return {
                    "brands_detected": ["YEALINK", "JABRA", "DNAKE"],
                    "products_sample": [
                        {'product_code': 'EVOLVE-20', 'brand': 'JABRA', 'price_excl_vat': 890, 'retail_incl_vat': 1433},
                        {'product_code': '16WALIC', 'brand': 'YEALINK', 'price_excl_vat': 0, 'retail_incl_vat': 0},
                        {'product_code': '280M-S8', 'brand': 'DNAKE', 'price_excl_vat': 1029, 'retail_incl_vat': 1659}
                    ],
                    "estimated_products": 100,
                    "status": "preview_fallback"
                }
        
        else:
            return {
                "brands_detected": [],
                "products_sample": [],
                "estimated_products": 0,
                "file_type": "non_excel",
                "status": "preview_success"
            }
            
    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/training/upload-document-with-config")
async def upload_training_document_with_config(file: UploadFile = File(...), config: str = ""):
    """Upload document with pricing configuration for enhanced processing"""
    if not ai_training_available or not ai_training_engine.document_intelligence:
        raise HTTPException(status_code=503, detail="AI training not initialized")
    
    try:
        # Parse configuration
        pricing_config = {}
        if config:
            try:
                pricing_config = json.loads(config)
            except Exception as e:
                logger.error(f"Config parsing error: {e}")
                pricing_config = {}
        
        # Enhanced processing for Excel files
        if file.filename.endswith(('.xlsx', '.xls')) and pricing_config:
            result = await process_excel_with_pricing_config(file, pricing_config)
        else:
            # Fall back to regular processing
            result = await ai_training_engine.document_intelligence.process_document(file)
        
        # Update AI knowledge with enhanced data
        if ai_training_engine.audio_consultant_ai and result.get('categories'):
            # Create enhanced categories with supplier info
            enhanced_categories = result.get('categories', {})
            if pricing_config.get('supplier_name'):
                supplier_key = f"supplier_{pricing_config['supplier_name'].lower()}"
                enhanced_categories[supplier_key] = [
                    f"Products: {result.get('products_extracted', 0)}",
                    f"Brands: {result.get('brands_detected', 0)}",
                    f"Price type: {pricing_config.get('price_type', 'unknown')}"
                ]
            
            ai_training_engine.audio_consultant_ai.update_knowledge_base(
                enhanced_categories, 
                result.get('relationships', [])
            )
        
        return {
            "message": f"Document {file.filename} processed successfully with configuration",
            "brands_detected": result.get('brands_detected', 0),
            "products_extracted": result.get('products_extracted', 0),
            "result": result,
            "pricing_config": pricing_config,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Enhanced upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_excel_with_pricing_config(file: UploadFile, config: Dict) -> Dict[str, Any]:
    """Process Excel file with pricing configuration"""
    try:
        content = await file.read()
        
        import pandas as pd
        from io import BytesIO
        
        df = pd.read_excel(BytesIO(content), header=None)
        
        # Enhanced brand detection and product extraction
        brands_detected = []
        products_extracted = []
        
        # Brand detection in first 5 rows
        brand_patterns = ['YEALINK', 'JABRA', 'DNAKE', 'CALL4TEL', 'LG', 'SHELLY', 'MIKROTIK', 'ZYXEL', 'NETOGY', 'TP-LINK', 'APACHE', 'VILO', 'CAMBIUM', 'BLUETTI', 'MOTOROLA', 'NEAT', 'LOGITECH', 'TELRAD', 'HUAWEI', 'TELTONIKA', 'SAMSUNG']
        
        for row_idx in range(min(5, len(df))):
            for col_idx in range(len(df.columns)):
                try:
                    cell_value = str(df.iloc[row_idx, col_idx]).strip().upper()
                    
                    for brand in brand_patterns:
                        if brand in cell_value and brand not in brands_detected and len(cell_value) < 30:
                            brands_detected.append(brand)
                            
                            # Extract products for this brand
                            for prod_row in range(row_idx + 3, min(row_idx + 50, len(df))):
                                try:
                                    product_code = str(df.iloc[prod_row, col_idx]).strip()
                                    if product_code and product_code not in ['nan', 'Stock Code', 'Updated']:
                                        # Look for price in next column
                                        price_col = col_idx + 1
                                        price_val = 0
                                        if price_col < len(df.columns):
                                            try:
                                                price_str = str(df.iloc[prod_row, price_col])
                                                if price_str not in ['P.O.R', 'nan', 'POA']:
                                                    price_val = float(price_str.replace(',', '').replace('R', ''))
                                            except:
                                                pass
                                        
                                        # Calculate prices based on config
                                        vat_rate = config.get('vat_rate', 0.15)
                                        markup = config.get('markup_percentage', 0.40)
                                        
                                        if config.get('price_type') == 'cost_excl_vat':
                                            cost_excl = price_val
                                            cost_incl = cost_excl * (1 + vat_rate) if cost_excl > 0 else 0
                                            retail_incl = cost_incl * (1 + markup) if cost_incl > 0 else 0
                                        else:
                                            cost_excl = price_val
                                            retail_incl = price_val * 1.61 if price_val > 0 else 0  # Default calc
                                        
                                        products_extracted.append({
                                            'product_code': product_code,
                                            'brand': brand,
                                            'supplier': config.get('supplier_name', 'Unknown'),
                                            'original_price': price_val,
                                            'cost_excl_vat': round(cost_excl, 2),
                                            'retail_incl_vat': round(retail_incl, 2),
                                            'price_type': config.get('price_type', 'cost_excl_vat')
                                        })
                                except:
                                    continue
                            break
                except:
                    continue
        
        # Create AI training categories
        categories = {
            'product_specs': [f"{len(products_extracted)} products from {config.get('supplier_name', 'supplier')}"],
            'pricing_info': [
                f"Cost excluding VAT pricing from {config.get('supplier_name', 'supplier')}",
                f"VAT rate: {config.get('vat_rate', 0.15) * 100}%",
                f"Markup: {config.get('markup_percentage', 0.40) * 100}%"
            ],
            'brand_relationships': [f"Multi-brand pricelist: {', '.join(brands_detected)}"],
            'suppliers': [f"{config.get('supplier_name', 'Unknown')}: {len(brands_detected)} brands, {len(products_extracted)} products"],
            'compatibility_rules': [],
            'system_designs': []
        }
        
        relationships = []
        for brand in brands_detected:
            relationships.append({
                'product_a': brand,
                'product_b': config.get('supplier_name', 'supplier'),
                'relationship': 'supplied_by'
            })
        
        return {
            'knowledge_id': str(uuid.uuid4()),
            'filename': file.filename,
            'brands_detected': len(brands_detected),
            'products_extracted': len(products_extracted),
            'categories': categories,
            'relationships': relationships,
            'pricing_config': config,
            'supplier_data': {
                'supplier': config.get('supplier_name'),
                'products': products_extracted,
                'brands': brands_detected
            },
            'processed_at': datetime.now().isoformat(),
            'status': 'success'
        }
        
    except Exception as e:
        logger.error(f"Excel config processing error: {e}")
        raise Exception(f"Failed to process Excel with config: {str(e)}")

# Existing quote management endpoints
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
    print("🔧 ENHANCED TRAINING: Multi-brand Excel processing with pricing config")
    print("\n💬 Try these:")
    print("• 'add denon avrx1800h'")
    print("• 'add yamaha rx-v6a'")
    print("• 'add polk speakers'")
    print("\n🧠 AI Training Endpoints:")
    print("• POST /api/v1/training/upload-document")
    print("• POST /api/v1/training/upload-document-with-config")
    print("• POST /api/v1/training/preview-document")
    print("• GET /api/v1/training/knowledge-base")
    print("\n🎉 Your customers will love the AI-enhanced experience!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)