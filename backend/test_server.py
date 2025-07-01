# test_server.py - CORRECTED VERSION
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# Import your enhanced database
from app.db.sqlantern import EnhancedSQLanternDB, ProductMatcher
sqlantern_db = EnhancedSQLanternDB()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audico AI Test", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    category: str

@app.get("/")
def root():
    return {"message": "Audico AI Test Server - Core Functionality", "status": "running"}

@app.get("/health")
def health():
    try:
        if sqlantern_db.connect():
            sqlantern_db.disconnect()
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "degraded", "database": "disconnected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/v1/chat")
def test_chat(chat_data: ChatMessage):
    try:
        # Extract search term from message
        message = chat_data.message.lower()
        if "denon" in message and "avr-x1800h" in message:
            search_term = "denon avr-x1800h"
        elif "denon" in message:
            search_term = "denon"
        else:
            # Extract first meaningful word
            words = chat_data.message.split()
            search_term = words[1] if len(words) > 1 else "audio"
        
        # Use the correct method name
        products = sqlantern_db.smart_product_search(search_term, limit=10)
        
        if products:
            if len(products) == 1:
                product = products[0]
                response = f"🎯 **Perfect Match Found!**\n\n"
                response += f"**{product['name']}**\n"
                response += f"💰 Price: **{product['price_formatted']}**\n"
                response += f"📦 Stock: {'✅ Available' if product['quantity'] > 0 else '❌ Out of Stock'}\n"
                if product.get('categories_display'):
                    response += f"🏷️ Categories: {product['categories_display']}\n"
                if product.get('brand'):
                    response += f"🏭 Brand: {product['brand']}\n"
                response += f"\n**✅ Deduplication working! Only 1 result instead of multiple!**"
            else:
                response = f"🔍 **Found {len(products)} products matching '{search_term}'** (deduplication applied):\n\n"
                for i, p in enumerate(products[:5], 1):
                    response += f"**{i}. {p['name']}**\n"
                    response += f"   💰 {p['price_formatted']}\n"
                    if p.get('has_special_price'):
                        response += f"   ⚡ *Special Price!*\n"
                    response += f"   📦 {'✅ Available' if p['quantity'] > 0 else '❌ Out of Stock'}\n"
                    if p.get('category_count', 0) > 1:
                        response += f"   🏷️ Found in {p['category_count']} categories\n"
                    response += f"\n"
                
                if len(products) > 5:
                    response += f"*... and {len(products) - 5} more products*\n\n"
                
                response += "**Which item would you like to add?**"
        else:
            response = f"🤔 I couldn't find '{search_term}' in our inventory.\n\nTry searching for:\n• Brand names (Denon, Yamaha)\n• Product types (amplifier, speakers)\n• Model numbers"
        
        return {
            "response": response,
            "products_found": len(products),
            "search_term": search_term,
            "deduplication_active": True,
            "status": "success",
            "category": chat_data.category,
            "user_message": chat_data.message
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": f"Error: {str(e)}", "status": "error"}

@app.get("/test-denon")
def test_denon():
    """Direct test of Denon AVR-X1800H deduplication"""
    try:
        # Use the correct method name
        products = sqlantern_db.smart_product_search("denon avr-x1800h", limit=20)
        return {
            "query": "denon avr-x1800h",
            "total_found": len(products),
            "deduplication_applied": True,
            "note": "Before enhancement: would show 5-10 duplicates. After: should show 1 unique product.",
            "products": [
                {
                    "name": p['name'],
                    "price_formatted": p['price_formatted'],
                    "price_zar": p.get('price_zar', 0),
                    "categories": p.get('categories_display', 'N/A'),
                    "category_count": p.get('category_count', 1),
                    "brand": p.get('brand', 'N/A'),
                    "model": p.get('model', 'N/A'),
                    "stock": "Available" if p['quantity'] > 0 else "Out of Stock",
                    "has_special_price": p.get('has_special_price', False)
                } for p in products
            ]
        }
    except Exception as e:
        logger.error(f"Denon test error: {e}")
        return {"error": str(e), "details": "Database connection or search failed"}

@app.get("/test-pricing")
def test_pricing():
    """Test the dynamic pricing engine"""
    try:
        # Get exchange rate
        exchange_rate = sqlantern_db.pricing_engine.get_live_exchange_rate()
        
        # Test with sample product
        sample_product = {
            'name': 'Test Denon AVR-X1800H',
            'price': 1299.99,
            'special_price': None,
            'category_name': 'AV Receivers'
        }
        
        final_price, formatted_price, pricing_info = sqlantern_db.pricing_engine.calculate_zar_price(sample_product)
        
        return {
            "exchange_rate": exchange_rate,
            "sample_calculation": {
                "usd_price": 1299.99,
                "zar_price": final_price,
                "formatted": formatted_price,
                "pricing_info": pricing_info
            },
            "note": "This should show live USD/ZAR conversion, not hard-coded 18.5 rate"
        }
    except Exception as e:
        logger.error(f"Pricing test error: {e}")
        return {"error": str(e)}

@app.get("/database-test")
def database_test():
    """Test database connection and basic stats"""
    try:
        if not sqlantern_db.connect():
            return {"error": "Could not connect to database"}
        
        cursor = sqlantern_db.connection.cursor(dictionary=True)
        
        # Get basic stats
        cursor.execute("SELECT COUNT(*) as count FROM oc_product WHERE status = 1")
        total_products = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM oc_product WHERE status = 1 AND price > 0")
        products_with_prices = cursor.fetchone()['count']
        
        sqlantern_db.disconnect()
        
        return {
            "database_status": "connected",
            "total_products": total_products,
            "products_with_prices": products_with_prices,
            "note": "Database connection successful"
        }
        
    except Exception as e:
        logger.error(f"Database test error: {e}")
        return {"error": str(e)}

@app.get("/available-methods")
def available_methods():
    """Debug: Show available methods on sqlantern_db object"""
    try:
        methods = [method for method in dir(sqlantern_db) if not method.startswith('_')]
        return {
            "available_methods": methods,
            "object_type": type(sqlantern_db).__name__,
            "note": "This shows what methods are actually available"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Audico AI Test Server (CORRECTED VERSION)")
    print("📊 Server: http://localhost:8000")
    print("🧪 Test Denon: http://localhost:8000/test-denon")
    print("💰 Test Pricing: http://localhost:8000/test-pricing")
    print("🔗 Database Test: http://localhost:8000/database-test")
    print("🔍 Available Methods: http://localhost:8000/available-methods")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)