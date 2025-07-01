# enhanced_chat_ai.py - Intelligent Chat System
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EnhancedChatAI:
    """Advanced AI chat system with intent recognition and context memory"""
    
    def __init__(self):
        self.conversation_memory = {}
        self.intents = {
            'add_to_quote': ['add', 'quote', 'get price', 'how much'],
            'product_search': ['find', 'search', 'looking for', 'need', 'want'],
            'compatibility': ['compatible', 'work with', 'match', 'pair'],
            'specifications': ['specs', 'specification', 'watts', 'channels', 'power'],
            'comparison': ['compare', 'difference', 'better', 'vs', 'versus'],
            'recommendation': ['recommend', 'suggest', 'best', 'good', 'advice']
        }
        
        # Audio equipment patterns
        self.product_patterns = {
            'receiver': r'(?:avr|receiver|amp|amplifier)[-\s]*[xd]?[-\s]*(\d+\w*)',
            'speaker': r'(?:speaker|bookshelf|tower|subwoofer|sub)[-\s]*(\w+)',
            'brand': r'(denon|yamaha|marantz|onkyo|pioneer|sony|bose|jbl|polk|klipsch)',
            'model': r'([a-z]+[-\s]*[xd]?[-\s]*\d+\w*)',
        }
    
    def process_message(self, user_message: str, user_id: str = "default", category: str = "home") -> Dict[str, Any]:
        """Process user message with enhanced AI understanding"""
        try:
            # Store conversation context
            if user_id not in self.conversation_memory:
                self.conversation_memory[user_id] = {
                    'messages': [],
                    'products_discussed': [],
                    'category': category,
                    'session_start': datetime.now().isoformat()
                }
            
            # Classify intent
            intent = self.classify_intent(user_message)
            
            # Extract entities
            entities = self.extract_entities(user_message)
            
            # Generate intelligent response
            response_data = self.generate_smart_response(
                user_message, intent, entities, user_id, category
            )
            
            # Store in memory
            self.conversation_memory[user_id]['messages'].append({
                'message': user_message,
                'intent': intent,
                'entities': entities,
                'timestamp': datetime.now().isoformat()
            })
            
            return response_data
            
        except Exception as e:
            logger.error(f"Enhanced chat processing error: {e}")
            return {
                "response": "I'm having trouble understanding. Could you rephrase that?",
                "intent": "error",
                "entities": {},
                "status": "error"
            }
    
    def classify_intent(self, message: str) -> str:
        """Classify user intent with improved accuracy"""
        message_lower = message.lower()
        
        # Score each intent
        intent_scores = {}
        for intent, keywords in self.intents.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Special handling for specific patterns
        if re.search(r'add.*to.*quote|quote.*for', message_lower):
            intent_scores['add_to_quote'] = intent_scores.get('add_to_quote', 0) + 3
        
        if re.search(r'what.*cost|how much|price of', message_lower):
            intent_scores['add_to_quote'] = intent_scores.get('add_to_quote', 0) + 2
        
        if re.search(r'compatible|work together|match', message_lower):
            intent_scores['compatibility'] = intent_scores.get('compatibility', 0) + 2
        
        # Return highest scoring intent
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'product_search'  # Default intent
    
    def extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extract audio equipment entities from message"""
        entities = {
            'brands': [],
            'models': [],
            'product_types': [],
            'specifications': []
        }
        
        message_lower = message.lower()
        
        # Extract brands
        for pattern_name, pattern in self.product_patterns.items():
            matches = re.findall(pattern, message_lower, re.IGNORECASE)
            if pattern_name == 'brand':
                entities['brands'].extend(matches)
            elif pattern_name == 'model':
                entities['models'].extend(matches)
        
        # Extract product types
        product_types = ['receiver', 'amplifier', 'speaker', 'subwoofer', 'turntable', 'cd player']
        for ptype in product_types:
            if ptype in message_lower:
                entities['product_types'].append(ptype)
        
        # Extract specifications
        spec_patterns = {
            'channels': r'(\d+)[-\s]*(?:channel|ch)',
            'watts': r'(\d+)[-\s]*(?:watt|w)',
            'frequency': r'(\d+)[-\s]*(?:hz|khz)'
        }
        
        for spec_type, pattern in spec_patterns.items():
            matches = re.findall(pattern, message_lower)
            if matches:
                entities['specifications'].extend([f"{spec_type}:{match}" for match in matches])
        
        return entities
    
    def generate_smart_response(self, message: str, intent: str, entities: Dict, user_id: str, category: str) -> Dict[str, Any]:
        """Generate intelligent response based on intent and entities"""
        
        # Import here to avoid circular imports
        from app.db.sqlantern import sqlantern_db
        
        if intent == 'add_to_quote':
            return self.handle_add_to_quote(message, entities)
        
        elif intent == 'product_search':
            return self.handle_product_search(message, entities, category)
        
        elif intent == 'compatibility':
            return self.handle_compatibility_check(message, entities)
        
        elif intent == 'specifications':
            return self.handle_specifications(message, entities)
        
        elif intent == 'recommendation':
            return self.handle_recommendations(message, category, entities)
        
        else:
            return self.handle_general_query(message, category)
    
    def handle_add_to_quote(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle add to quote requests with smart product matching"""
        from app.db.sqlantern import sqlantern_db
        
        # Extract search terms
        search_terms = []
        if entities['brands']:
            search_terms.extend(entities['brands'])
        if entities['models']:
            search_terms.extend(entities['models'])
        
        # If no specific entities, extract from message
        if not search_terms:
            # Remove common words and extract potential product names
            words = message.lower().split()
            exclude_words = ['add', 'to', 'quote', 'please', 'i', 'want', 'need', 'the', 'a', 'an']
            search_terms = [word for word in words if word not in exclude_words and len(word) > 2]
        
        if search_terms:
            search_query = ' '.join(search_terms)
            products = sqlantern_db.search_products(search_query, limit=5, include_out_of_stock=False)
            
            if products:
                response = f"🎵 **Found these products for '{search_query}':**\n\n"
                
                for i, product in enumerate(products, 1):
                    response += f"**{i}. {product['name']}**\n"
                    
                    if product.get('has_special_price'):
                        response += f"   💰 **SPECIAL: {product['price_formatted']}** "
                        if product.get('original_price_formatted'):
                            response += f"~~{product['original_price_formatted']}~~ "
                        if product.get('savings_formatted'):
                            response += f"(Save {product['savings_formatted']}!) ⚡"
                    else:
                        response += f"   💰 Price: {product['price_formatted']}"
                    
                    response += f"\n   📦 Stock: {'✅ Available' if product['quantity'] > 0 else '❌ Out of Stock'}"
                    response += f"\n   [Click to add: Product {i}]\n\n"
                
                response += "**Which product would you like to add to your quote?**"
                
                return {
                    "response": response,
                    "intent": "add_to_quote",
                    "products_found": products,
                    "search_type": "smart_product_match",
                    "status": "success"
                }
            else:
                return {
                    "response": f"I couldn't find '{search_query}' in our inventory. Try using exact model numbers like 'AVR-X1800H' or browse by category.",
                    "intent": "add_to_quote",
                    "search_type": "no_match",
                    "status": "no_results"
                }
        else:
            return {
                "response": "What specific product would you like to add to your quote? Try: 'Add Denon AVR-X1800H' or 'Quote for Yamaha speakers'",
                "intent": "add_to_quote",
                "search_type": "needs_clarification",
                "status": "needs_input"
            }
    
    def handle_product_search(self, message: str, entities: Dict, category: str) -> Dict[str, Any]:
        """Handle general product search with category context"""
        # Implementation similar to add_to_quote but with browsing focus
        response = f"I can help you find audio equipment for your **{category}** setup.\n\n"
        response += "**Popular categories:**\n"
        response += "• AV Receivers (like Denon AVR-X1800H)\n"
        response += "• Speakers & Subwoofers\n"
        response += "• Amplifiers & Pre-amps\n\n"
        response += "**Try asking:** 'Show me Denon receivers' or 'Find bookshelf speakers'"
        
        return {
            "response": response,
            "intent": "product_search",
            "category": category,
            "status": "guidance"
        }
    
    def handle_compatibility_check(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle compatibility questions"""
        response = "🔗 **Compatibility Check**\n\n"
        response += "I can help ensure your components work together perfectly!\n\n"
        response += "**For best results, tell me:**\n"
        response += "• Your current receiver model\n"
        response += "• Speaker impedance (4Ω, 6Ω, 8Ω)\n"
        response += "• Room size and listening preferences\n\n"
        response += "**Example:** 'Will Polk XT60 speakers work with Denon AVR-X1800H?'"
        
        return {
            "response": response,
            "intent": "compatibility",
            "status": "guidance"
        }
    
    def handle_specifications(self, message: str, entities: Dict) -> Dict[str, Any]:
        """Handle technical specification requests"""
        response = "📊 **Technical Specifications**\n\n"
        response += "I can provide detailed specs for any product in our catalog.\n\n"
        response += "**Available specs:**\n"
        response += "• Power output (watts per channel)\n"
        response += "• Channel configuration\n"
        response += "• Frequency response\n"
        response += "• THD, SNR, and other technical details\n\n"
        response += "**Try:** 'Specs for Denon AVR-X1800H' or 'Power output of Yamaha RX-V6A'"
        
        return {
            "response": response,
            "intent": "specifications",
            "status": "guidance"
        }
    
    def handle_recommendations(self, message: str, category: str, entities: Dict) -> Dict[str, Any]:
        """Provide intelligent recommendations based on category and requirements"""
        from app.db.sqlantern import sqlantern_db
        
        # Get category-specific recommendations
        recommendations = sqlantern_db.get_product_recommendations(category, message)
        
        if recommendations:
            response = f"🎯 **Recommended for {category.title()}:**\n\n"
            
            for i, product in enumerate(recommendations[:3], 1):
                response += f"**{i}. {product['name']}**\n"
                response += f"   💰 {product['price_formatted']}"
                if product.get('has_special_price'):
                    response += " ⚡ SPECIAL PRICE!"
                response += f"\n   📦 {product['categories_display']}\n\n"
            
            response += "**Want details on any of these? Just ask!**"
        else:
            response = f"Let me help you find the perfect setup for your **{category}**!\n\n"
            response += "**Tell me about:**\n"
            response += "• Your budget range\n"
            response += "• Room size\n"
            response += "• Preferred brands\n"
            response += "• Specific requirements\n\n"
            response += "I'll recommend the best combination for your needs."
        
        return {
            "response": response,
            "intent": "recommendation",
            "category": category,
            "products": recommendations[:3] if recommendations else [],
            "status": "success" if recommendations else "needs_input"
        }
    
    def handle_general_query(self, message: str, category: str) -> Dict[str, Any]:
        """Handle general queries with helpful guidance"""
        response = f"👋 **Welcome to Audico AI!**\n\n"
        response += f"I'm here to help you build the perfect **{category}** audio system.\n\n"
        response += "**I can help you:**\n"
        response += "• Find specific products (try: 'Denon AVR-X1800H')\n"
        response += "• Get pricing and availability\n"
        response += "• Build and manage quotes\n"
        response += "• Check compatibility\n"
        response += "• Provide recommendations\n\n"
        response += "**What audio equipment are you looking for?**"
        
        return {
            "response": response,
            "intent": "general",
            "category": category,
            "status": "welcome"
        }

# Global instance
enhanced_chat_ai = EnhancedChatAI()
