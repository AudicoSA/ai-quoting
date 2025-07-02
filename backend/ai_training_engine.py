from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import openai
import PyPDF2
import pandas as pd
import re
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class DocumentIntelligence:
    """AI-powered document processing and categorization"""
    
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.categories = {
            'product_specs': [],
            'compatibility_rules': [],
            'pricing_info': [],
            'system_designs': [],
            'brand_relationships': []
        }
    
    async def process_document(self, file: UploadFile) -> Dict[str, Any]:
        """Process uploaded document with AI intelligence"""
        try:
            # Extract content based on file type
            if file.filename.endswith('.pdf'):
                content = await self.extract_pdf_content(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                content = await self.extract_excel_content(file)
            else:
                content = await file.read()
                content = content.decode('utf-8')
            
            # AI-powered categorization
            categories = await self.ai_categorize_content(content)
            
            # Extract product relationships
            relationships = await self.extract_product_relationships(content)
            
            # Store in knowledge base
            knowledge_id = str(uuid.uuid4())
            
            return {
                'knowledge_id': knowledge_id,
                'filename': file.filename,
                'categories': categories,
                'relationships': relationships,
                'processed_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def extract_pdf_content(self, file: UploadFile) -> str:
        """Extract text from PDF"""
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(content)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    async def extract_excel_content(self, file: UploadFile) -> str:
        """Extract content from Excel files"""
        content = await file.read()
        df = pd.read_excel(content)
        return df.to_string()
    
    async def ai_categorize_content(self, content: str) -> Dict[str, List[str]]:
        """AI-powered content categorization"""
        prompt = f"""
        Analyze this audio equipment document and categorize the content into these categories:
        
        1. PRODUCT_SPECS: Technical specifications, power ratings, frequency response, etc.
        2. COMPATIBILITY_RULES: What products work together, impedance matching, etc.
        3. PRICING_INFO: Prices, discounts, special offers, pricing tiers
        4. SYSTEM_DESIGNS: Complete system recommendations, room setups
        5. BRAND_RELATIONSHIPS: Which brands work well together, partnerships
        
        Content: {content[:3000]}...
        
        Return JSON format:
        {{
            "product_specs": ["spec1", "spec2"],
            "compatibility_rules": ["rule1", "rule2"],
            "pricing_info": ["price1", "price2"],
            "system_designs": ["design1", "design2"],
            "brand_relationships": ["relationship1", "relationship2"]
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"AI categorization error: {e}")
            return {category: [] for category in self.categories.keys()}
    
    async def extract_product_relationships(self, content: str) -> List[Dict]:
        """Extract product compatibility relationships"""
        prompt = f"""
        Extract product relationships from this audio equipment content.
        Look for phrases like "works with", "compatible with", "pairs well with", "recommended for".
        
        Content: {content[:3000]}...
        
        Return JSON array of relationships:
        [
            {{"product_a": "Denon AVR-X1800H", "product_b": "Monitor Audio Bronze", "relationship": "pairs_well_with"}},
            {{"product_a": "8 ohm speakers", "product_b": "100W amplifier", "relationship": "compatible_with"}}
        ]
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Relationship extraction error: {e}")
            return []

class EnhancedAudioConsultantAI:
    """Professional audio consultant AI with training knowledge"""
    
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.knowledge_base = {}
        self.conversation_memory = {}
    
    async def generate_professional_response(self, 
                                           user_message: str, 
                                           products_found: List[Dict],
                                           conversation_context: Dict,
                                           category: str) -> str:
        """Generate professional audio consultant response"""
        
        # Build context from knowledge base
        relevant_knowledge = self.get_relevant_knowledge(user_message)
        
        system_prompt = f"""
        You are a professional audio consultant at Audico SA with deep expertise in audio systems.
        
        PERSONALITY:
        - Professional but conversational (not robotic)
        - Knowledgeable about audio equipment and compatibility
        - Helpful in suggesting complete systems
        - Enthusiastic about great audio experiences
        
        KNOWLEDGE BASE:
        {json.dumps(relevant_knowledge, indent=2)}
        
        CURRENT CONTEXT:
        - Customer category: {category}
        - Products found: {len(products_found)} items
        - Conversation context: {conversation_context}
        
        INSTRUCTIONS:
        - If customer asks about speakers after selecting a receiver, suggest compatible options
        - Mention special pricing when available
        - Ask follow-up questions about room size, budget, preferences
        - Suggest complete systems, not just individual items
        - Use natural language, avoid bullet points
        - Reference specific products from the inventory when relevant
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI response generation error: {e}")
            return "I'm having trouble accessing my knowledge right now. Let me help you with what I know about your audio needs."
    
    def get_relevant_knowledge(self, query: str) -> Dict:
        """Retrieve relevant knowledge for the query"""
        # This would normally use vector search, simplified for now
        relevant = {}
        
        # Check for speaker-related queries
        if any(word in query.lower() for word in ['speaker', 'speakers']):
            relevant['speaker_recommendations'] = [
                "Monitor Audio Bronze series pairs well with Denon receivers",
                "For 8K receivers, consider 6-8 ohm speakers",
                "Bookshelf speakers ideal for smaller rooms"
            ]
        
        # Check for receiver-related queries  
        if any(word in query.lower() for word in ['receiver', 'amplifier', 'avr']):
            relevant['receiver_info'] = [
                "Denon X-series offers excellent value",
                "Consider room size for power requirements",
                "8K support future-proofs your investment"
            ]
        
        return relevant
    
    def update_knowledge_base(self, categories: Dict, relationships: List[Dict]):
        """Update knowledge base with new training data"""
        for category, items in categories.items():
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []
            self.knowledge_base[category].extend(items)
        
        # Store relationships
        if 'relationships' not in self.knowledge_base:
            self.knowledge_base['relationships'] = []
        self.knowledge_base['relationships'].extend(relationships)

# Global instances
document_intelligence = None
audio_consultant_ai = None

def initialize_ai_training(openai_api_key: str):
    """Initialize AI training components"""
    global document_intelligence, audio_consultant_ai
    document_intelligence = DocumentIntelligence(openai_api_key)
    audio_consultant_ai = EnhancedAudioConsultantAI(openai_api_key)