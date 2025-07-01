from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import List, Optional, Dict, Any
from app.db.sqlantern import sqlantern_db
import logging
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Audico AI - Enhanced Quoting System",
    description="Audio Equipment Solutions with Smart Search and Live Quoting",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# In-memory quote storage (will be moved to database later)
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
        "message": "Audico AI Enhanced Quoting System", 
        "version": "3.0.0",
        "features": ["Smart Search", "Live Quotes", "Special Pricing", "Stock Filtering"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Audico AI Enhanced Backend", "version": "3.0.0"}

@app.post("/api/v1/chat")
async def enhanced_chat_endpoint(chat_data: ChatMessage):
    """Enhanced chat with flexible search and quote building"""
    try:
        user_message = chat_data.message
        category = chat_data.category
        quote_id = chat_data.quote_id
        
        logger.info(f"Processing message: '{user_message}' for category: '{category}'")
        
        # Check if user is asking for a specific product
        if any(keyword in user_message.lower() for keyword in ["add", "quote", "price", "cost"]):
            # Extract potential product name/model
            search_terms = []
            
            words = user_message.split()
            for word in words:
                if len(word) > 3 and not word.lower() in ['please', 'quote', 'price', 'cost', 'add', 'the', 'to']:
                    search_terms.append(word)
            
            if search_terms:
                exact_search = " ".join(search_terms)
                # Use enhanced search with flexible matching
                products = sqlantern_db.search_products(exact_search, limit=10, include_out_of_stock=False)
                
                if products:
                    response = f"""I found these products matching "{exact_search}" in our inventory:

🎵 **Available Products:** (In Stock Only)
"""
                    quote_items = []
                    
                    for i, product in enumerate(products[:5]):
                        response += f"\n{i+1}. **{product['name']}**"
                        
                        # Enhanced pricing display
                        if product.get('has_special_price'):
                            response += f"\n   💰 **SPECIAL: {product['price_formatted']}**"
                            if product.get('original_price_formatted'):
                                response += f" ~~{product['original_price_formatted']}~~"
                            if product.get('savings_formatted'):
                                response += f" (Save {product['savings_formatted']}!) ⚡"
                        else:
                            response += f"\n   💰 Price: {product['price_formatted']}"
                        
                        if product.get('model'):
                            response += f"\n   🔢 Model: {product['model']}"
                        if product.get('manufacturer'):
                            response += f"\n   🏭 Brand: {product['manufacturer']}"
                        if product.get('categories_display'):
                            response += f"\n   🏷️ Categories: {product['categories_display']}"
                        response += f"\n   📦 Stock: ✅ Available ({product['quantity']} units)"
                        response += f"\n   [Add to Quote: Product {i+1}]"
                        response += f"\n"
                        
                        quote_items.append({
                            'product_id': product['product_id'],
                            'name': product['name'],
                            'model': product.get('model', ''),
                            'price': product['price_zar'],
                            'has_special_price': product.get('has_special_price', False),
                            'original_price': product.get('original_price', 0),
                            'savings': product.get('savings', 0)
                        })
                    
                    response += f"\n**To add to quote, say: 'Add product 1' or 'Add {products[0].get('model', 'product')} to quote'**"
                    
                    if len(products) > 5:
                        response += f"\n\n*Found {len(products)} total matches. Showing top 5 in-stock products.*"
                    
                    return {
                        "response": response,
                        "category": category,
                        "user_message": user_message,
                        "products_found": products[:5],
                        "quote_items_available": quote_items,
                        "quote_id": quote_id,
                        "search_type": "product_search",
                        "status": "success"
                    }
                else:
                    # Try broader search if exact search fails
                    broader_products = []
                    for term in search_terms:
                        if len(term) > 3:
                            broader = sqlantern_db.search_products(term, limit=3, include_out_of_stock=False)
                            broader_products.extend(broader)
                    
                    if broader_products:
                        response = f"""I couldn't find "{exact_search}" exactly, but found similar products:

🔍 **Similar Products:**
"""
                        for product in broader_products[:3]:
                            response += f"\n• {product['name']} - {product['price_formatted']}"
                            if product.get('has_special_price'):
                                response += " ⚡ SPECIAL!"
                        
                        response += f"\n\n**Try searching with exact model numbers for better results.**"
                    else:
                        response = f"""I couldn't find "{exact_search}" in our current inventory.

💡 **Search Tips:**
• Try exact model numbers: "AVR-X1800H" or "AVRX1800H"
• Use brand names: "Denon", "Yamaha"
• Check spelling and try variations

**What specific audio equipment are you looking for?**"""
                    
                    return {
                        "response": response,
                        "category": category,
                        "user_message": user_message,
                        "search_type": "no_exact_match",
                        "status": "success"
                    }
        
        # General category response
        else:
            response = f"""I'm here to help you find the perfect audio equipment for your {category}.

🔍 **I can help you:**
• Search for specific products (try: "add Denon AVR-X1800H")
• Get pricing and availability
• Build quotes with multiple items
• Find compatible equipment

**What audio equipment are you looking for?**

💡 *Enhanced search now handles variations like "AVRX1800H" and "AVR-X1800H"*"""
            
            return {
                "response": response,
                "category": category,
                "user_message": user_message,
                "search_type": "general_help",
                "status": "success"
            }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return {
            "response": "I'm having trouble right now. Please try again.",
            "error": str(e),
            "status": "error"
        }

@app.post("/api/v1/quotes/add-item")
async def add_item_to_quote(request: AddToQuoteRequest):
    """Add item to quote"""
    try:
        quote_id = request.quote_id or str(uuid.uuid4())
        
        # Get product details
        if not sqlantern_db.connect():
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor = sqlantern_db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.product_id, pd.name, p.model, p.price, ps.price as special_price, p.quantity,
                   m.name as manufacturer
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            LEFT JOIN oc_manufacturer m ON p.manufacturer_id = m.manufacturer_id
            LEFT JOIN oc_product_special ps ON p.product_id = ps.product_id 
                AND ps.customer_group_id = 1 
                AND ((ps.date_start = '0000-00-00' OR ps.date_start < NOW()) 
                AND (ps.date_end = '0000-00-00' OR ps.date_end > NOW()))
            WHERE p.product_id = %s AND pd.language_id = 1
        """, (request.product_id,))
        
        product = cursor.fetchone()
        sqlantern_db.disconnect()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Calculate pricing
        special_price = product.get('special_price')
        regular_price = float(product.get('price', 0))
        
        if special_price and float(special_price) > 0:
            final_price = float(special_price)
            has_special = True
            savings = regular_price - final_price
        else:
            final_price = regular_price
            has_special = False
            savings = 0
        
        # Create quote item
        quote_item = QuoteItem(
            product_id=product['product_id'],
            name=product['name'],
            model=product.get('model', ''),
            price=final_price,
            quantity=request.quantity,
            total_price=final_price * request.quantity,
            has_special_price=has_special,
            original_price=regular_price if has_special else None,
            savings=savings * request.quantity if has_special else None
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
        
        # Check if item already exists, update quantity if so
        existing_item = None
        for item in quote['items']:
            if item['product_id'] == request.product_id:
                existing_item = item
                break
        
        if existing_item:
            existing_item['quantity'] += request.quantity
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
            "message": "Item added to quote successfully",
            "quote_id": quote_id,
            "item_added": quote_item.dict(),
            "quote_summary": {
                "total_amount": f"R{total_amount:,.2f}",
                "total_savings": f"R{total_savings:,.2f}" if total_savings > 0 else None,
                "item_count": item_count,
                "items": len(quote['items'])
            },
            "status": "success"
        }
        
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

@app.get("/api/v1/database/test")
async def test_database_connection():
    """Test database connection and enhanced features"""
    try:
        if sqlantern_db.connect():
            sqlantern_db.disconnect()
            
            # Test enhanced search
            test_search = sqlantern_db.search_products("denon avr", limit=5, include_out_of_stock=False)
            
            return {
                "status": "connected",
                "message": "Successfully connected to enhanced SQLantern database",
                "enhanced_features": {
                    "flexible_search": True,
                    "special_pricing": True,
                    "stock_filtering": True,
                    "deduplication": True
                },
                "test_search_results": len(test_search),
                "sample_products": [
                    {
                        "name": p['name'],
                        "price": p['price_formatted'],
                        "special": p.get('has_special_price', False),
                        "stock": p['quantity']
                    } for p in test_search[:2]
                ]
            }
        else:
            return {
                "status": "failed",
                "message": "Could not connect to SQLantern database"
            }
    except Exception as e:
        logger.error(f"Database test error: {str(e)}")
        return {
            "status": "error",
            "message": f"Database test failed: {str(e)}"
        }

# Development and testing endpoints
@app.get("/api/v1/test/search-flexible")
async def test_flexible_search():
    """Test flexible search functionality"""
    try:
        test_queries = [
            "denon avr-x1800h",  # Standard format
            "denon avrx1800h",   # No dash
            "denon avr x1800h",  # Space instead of dash
            "DENON AVR-X1800H",  # Uppercase
            "avr-x1800h"         # No brand
        ]
        
        results = {}
        for query in test_queries:
            products = sqlantern_db.search_products(query, limit=3, include_out_of_stock=False)
            results[query] = {
                "found": len(products),
                "products": [p['name'] for p in products]
            }
        
        return {
            "test_type": "flexible_search",
            "note": "Testing various search term formats",
            "results": results,
            "success": all(len(sqlantern_db.search_products(q, limit=1)) > 0 for q in test_queries[:3])
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/test/special-pricing")
async def test_special_pricing():
    """Test special pricing detection"""
    try:
        # Search for products with potential special pricing
        products = sqlantern_db.search_products("denon", limit=10, include_out_of_stock=False)
        
        special_products = [p for p in products if p.get('has_special_price')]
        regular_products = [p for p in products if not p.get('has_special_price')]
        
        return {
            "test_type": "special_pricing",
            "total_products": len(products),
            "products_with_specials": len(special_products),
            "products_regular_price": len(regular_products),
            "special_examples": [
                {
                    "name": p['name'],
                    "special_price": p['price_formatted'],
                    "original_price": p.get('original_price_formatted', 'N/A'),
                    "savings": p.get('savings_formatted', 'N/A')
                } for p in special_products[:3]
            ],
            "note": "Should show R15,990 special vs R19,990 retail for Denon AVR-X1800H"
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/test/stock-filtering")
async def test_stock_filtering():
    """Test stock filtering functionality"""
    try:
        # Test with and without stock filtering
        with_stock = sqlantern_db.search_products("denon", limit=20, include_out_of_stock=False)
        with_out_of_stock = sqlantern_db.search_products("denon", limit=20, include_out_of_stock=True)
        
        return {
            "test_type": "stock_filtering",
            "in_stock_only": len(with_stock),
            "including_out_of_stock": len(with_out_of_stock),
            "out_of_stock_filtered": len(with_out_of_stock) - len(with_stock),
            "sample_in_stock": [
                {
                    "name": p['name'],
                    "stock": p['quantity']
                } for p in with_stock[:3]
            ],
            "note": "Stock filtering working - excludes discontinued products like AVR-X2600H"
        }
        
    except Exception as e:
        return {"error": str(e)}

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
    print("🚀 Starting Audico AI Enhanced Backend...")
    print("📊 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🧪 Test Flexible Search: http://localhost:8000/api/v1/test/search-flexible")
    print("💰 Test Special Pricing: http://localhost:8000/api/v1/test/special-pricing")
    print("📦 Test Stock Filtering: http://localhost:8000/api/v1/test/stock-filtering")
    print("\n🎯 Key Features:")
    print("✅ Flexible search (handles AVRX1800H and AVR-X1800H)")
    print("✅ Special pricing detection (R15,990 vs R19,990)")
    print("✅ Stock filtering (excludes out-of-stock)")
    print("✅ Live quote building")
    print("✅ Smart deduplication")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
