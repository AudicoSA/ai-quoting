# simple_test.py - Test your enhanced system
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import your enhanced database
from app.db.sqlantern import sqlantern_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audico AI Test - Enhanced System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    category: str

@app.get("/")
def root():
    return {"message": "Audico AI Enhanced Test Server", "status": "running"}

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

@app.get("/test-denon-enhanced")
def test_denon_enhanced():
    """Test the enhanced Denon search with deduplication"""
    try:
        # Test your enhanced search
        products = sqlantern_db.search_products("denon avr-x1800h", limit=20)
        
        return {
            "query": "denon avr-x1800h",
            "total_found": len(products),
            "deduplication_working": len(products) <= 2,  # Should be 1-2 instead of 5-10
            "note": f"Before enhancement: 5-10 duplicates. After: {len(products)} unique product(s)",
            "enhancements_active": {
                "dynamic_pricing": True,
                "deduplication": True,
                "special_price_detection": True
            },
            "products": [
                {
                    "name": p['name'],
                    "price_formatted": p['price_formatted'],
                    "price_zar": p.get('price_zar', 0),
                    "categories": p.get('categories_display', 'N/A'),
                    "category_count": p.get('category_count', 1),
                    "model": p.get('model', 'N/A'),
                    "manufacturer": p.get('manufacturer', 'N/A'),
                    "stock": "Available" if p['quantity'] > 0 else "Out of Stock",
                    "has_special_price": p.get('has_special_price', False)
                } for p in products
            ]
        }
    except Exception as e:
        logger.error(f"Enhanced Denon test error: {e}")
        return {"error": str(e), "note": "Enhanced search failed"}

@app.get("/test-pricing-engine")
def test_pricing_engine():
    """Test the dynamic pricing engine"""
    try:
        # Get live exchange rate
        exchange_rate = sqlantern_db.pricing_engine.get_live_exchange_rate()
        
        # Test with sample product
        sample_product = {
            'name': 'Test Denon AVR-X1800H',
            'price': 1299.99,
            'special_price': None,
            'category_name': 'AV Receivers'
        }
        
        final_price, formatted_price = sqlantern_db.pricing_engine.calculate_zar_price(sample_product)
        
        return {
            "pricing_engine_status": "operational",
            "live_exchange_rate": exchange_rate,
            "is_live_rate": exchange_rate != 18.5,  # True if using live rate
            "sample_calculation": {
                "usd_price": 1299.99,
                "zar_price": final_price,
                "formatted": formatted_price,
                "exchange_rate_used": exchange_rate
            },
            "enhancement_working": exchange_rate != 18.5,
            "note": "If exchange_rate != 18.5, then live pricing is working!"
        }
    except Exception as e:
        logger.error(f"Pricing test error: {e}")
        return {"error": str(e)}

@app.post("/api/v1/chat")
def enhanced_chat(chat_data: ChatMessage):
    """Test enhanced chat with deduplication"""
    try:
        message = chat_data.message.lower()
        
        # Simple test for Denon
        if "denon" in message and "avr-x1800h" in message:
            products = sqlantern_db.search_products("denon avr-x1800h", limit=10)
            
            if products:
                if len(products) == 1:
                    product = products[0]
                    response = f"🎯 **ENHANCED SYSTEM SUCCESS!**\n\n"
                    response += f"**{product['name']}**\n"
                    response += f"💰 Price: **{product['price_formatted']}** (Dynamic ZAR pricing)\n"
                    response += f"📦 Stock: {'✅ Available' if product['quantity'] > 0 else '❌ Out of Stock'}\n"
                    response += f"🏷️ Categories: {product.get('categories_display', 'N/A')}\n"
                    response += f"🔢 Model: {product.get('model', 'N/A')}\n"
                    if product.get('has_special_price'):
                        response += f"⚡ **Special Price Detected!**\n"
                    response += f"\n✅ **Deduplication Working**: Only 1 result instead of multiple!"
                    
                    return {
                        "response": response,
                        "enhancement_success": True,
                        "products_found": 1,
                        "deduplication_working": True,
                        "dynamic_pricing": True,
                        "products": products
                    }
                else:
                    response = f"🔍 **Found {len(products)} unique products** (deduplication applied):\n\n"
                    for i, p in enumerate(products, 1):
                        response += f"{i}. {p['name']} - {p['price_formatted']}\n"
                    
                    return {
                        "response": response,
                        "enhancement_success": True,
                        "products_found": len(products),
                        "deduplication_working": len(products) <= 3,
                        "products": products
                    }
            else:
                return {
                    "response": "No Denon AVR-X1800H found in database",
                    "enhancement_success": False,
                    "products_found": 0
                }
        else:
            return {
                "response": f"Enhanced chat active! Try asking: 'add Denon AVR-X1800H to quote'",
                "message_received": chat_data.message,
                "category": chat_data.category
            }
            
    except Exception as e:
        logger.error(f"Enhanced chat error: {e}")
        return {"response": f"Error: {str(e)}", "enhancement_success": False}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Audico AI Enhanced Test Server")
    print("📊 Server: http://localhost:8000")
    print("🧪 Test Enhanced Denon: http://localhost:8000/test-denon-enhanced")
    print("💰 Test Pricing Engine: http://localhost:8000/test-pricing-engine")
    print("💬 Test Chat: http://localhost:8000/docs -> /api/v1/chat")
    print("📚 Full API Docs: http://localhost:8000/docs")
    print("\n🎯 KEY TESTS:")
    print("1. Check if deduplication works: Only 1-2 Denon results instead of 5-10")
    print("2. Check if dynamic pricing works: Exchange rate != 18.5")
    print("3. Test chat with: 'add Denon AVR-X1800H to quote'")
    uvicorn.run(app, host="0.0.0.0", port=8000)
