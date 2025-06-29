from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import List, Optional
from app.db.sqlantern import sqlantern_db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance - THIS WAS MISSING!
app = FastAPI(
    title="Audico AI - Complete Data Integration",
    description="Audio Equipment Solutions with Real Product Database",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Request models
class ChatMessage(BaseModel):
    message: str
    category: str

class ProductSearch(BaseModel):
    query: str
    category: Optional[str] = None
    limit: Optional[int] = 20

@app.get("/")
async def root():
    return {"message": "Audico AI Complete Data Integration System is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Audico AI Backend", "version": "2.0.0"}

@app.post("/api/v1/chat")
async def enhanced_chat_endpoint(chat_data: ChatMessage):
    """Enhanced chat with precise product matching"""
    try:
        user_message = chat_data.message
        category = chat_data.category
        
        logger.info(f"Processing message: '{user_message}' for category: '{category}'")
        
        # Check if user is asking for a specific product
        if any(keyword in user_message.lower() for keyword in ["add", "quote", "price", "cost"]):
            # Extract potential product name/model
            search_terms = []
            
            # Look for specific model numbers or brand names
            words = user_message.split()
            for word in words:
                if len(word) > 3 and not word.lower() in ['please', 'quote', 'price', 'cost', 'add', 'the', 'to']:
                    search_terms.append(word)
            
            if search_terms:
                # Search for exact product matches
                exact_search = " ".join(search_terms)
                products = sqlantern_db.search_products(exact_search, limit=10)
                
                if products:
                    # Show exact matches found
                    response = f"""I found these products matching "{exact_search}" in our inventory:

🎵 **Available Products:**
"""
                    quote_items = []
                    
                    for i, product in enumerate(products[:5]):
                        if product.get('price_zar'):
                            response += f"\n{i+1}. **{product['name']}**"
                            response += f"\n   Price: {product['price_formatted']}"
                            if product.get('model'):
                                response += f"\n   Model: {product['model']}"
                            if product.get('category_name'):
                                response += f"\n   Category: {product['category_name']}"
                            response += f"\n   Stock: {'✅ Available' if product['quantity'] > 0 else '❌ Out of Stock'}\n"
                            
                            quote_items.append({
                                'id': product['product_id'],
                                'name': product['name'],
                                'price': product['price_zar'],
                                'model': product.get('model', ''),
                                'category': product.get('category_name', 'Audio Equipment'),
                                'in_stock': product['quantity'] > 0
                            })
                    
                    response += f"\n**Which specific item would you like me to add to your quote?** Just tell me the number (1, 2, 3, etc.) or the exact name."
                    
                    if len(products) > 5:
                        response += f"\n\n*Found {len(products)} total matches. Showing top 5.*"
                    
                    return {
                        "response": response,
                        "category": category,
                        "user_message": user_message,
                        "exact_matches": products[:5],
                        "quote_items": quote_items,
                        "search_type": "exact_product",
                        "status": "success"
                    }
                else:
                    response = f"""I couldn't find "{exact_search}" in our current inventory. 

🔍 **Let me search for similar products:**"""
                    
                    # Try broader search
                    similar_products = []
                    for term in search_terms:
                        if len(term) > 3:
                            similar = sqlantern_db.search_products(term, limit=5)
                            similar_products.extend(similar)
                    
                    # Remove duplicates
                    seen_ids = set()
                    unique_products = []
                    for product in similar_products:
                        if product['product_id'] not in seen_ids:
                            seen_ids.add(product['product_id'])
                            unique_products.append(product)
                    
                    if unique_products:
                        response += f"\n\nSimilar products I found:"
                        for product in unique_products[:3]:
                            response += f"\n• {product['name']} - {product['price_formatted']}"
                    else:
                        response += f"\n\nNo similar products found. Could you:"
                        response += f"\n• Check the spelling of the model/brand name?"
                        response += f"\n• Try a broader search term?"
                        response += f"\n• Tell me what type of equipment you're looking for?"
                    
                    return {
                        "response": response,
                        "category": category,
                        "user_message": user_message,
                        "exact_matches": [],
                        "similar_products": unique_products[:3],
                        "search_type": "no_match",
                        "status": "success"
                    }
        
        # If not asking for specific product, provide general category recommendations
        else:
            # Simple fallback response for now
            response = f"""I understand you need {category} audio solutions. You mentioned: "{user_message}".

🔍 **I can help you find:**
• Specific products by model number (e.g., "Denon AVR-X1800H")
• Products by brand (e.g., "Yamaha speakers")
• Products by type (e.g., "ceiling speakers", "amplifiers")

**What specific audio equipment are you looking for?**"""
            
            return {
                "response": response,
                "category": category,
                "user_message": user_message,
                "recommendations": [],
                "search_type": "general_help",
                "status": "success"
            }
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {str(e)}")
        # Return a simple fallback response instead of raising an exception
        return {
            "response": f"I'm having trouble processing your request right now. Could you try asking again?",
            "category": category,
            "user_message": user_message,
            "error": str(e),
            "status": "error"
        }

@app.get("/api/v1/categories")
async def get_categories():
    """Get categories"""
    try:
        # Static solution categories for now
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
        
        return {
            "solution_categories": solution_categories,
            "product_categories": []
        }
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        return {"solution_categories": [], "product_categories": []}

@app.get("/api/v1/database/test")
async def test_database_connection():
    """Test connection to SQLantern database"""
    try:
        if sqlantern_db.connect():
            sqlantern_db.disconnect()
            return {
                "status": "connected",
                "message": "Successfully connected to SQLantern database"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
