from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import PyPDF2
import pandas as pd
import re
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime
import uuid
from io import BytesIO
import asyncio

logger = logging.getLogger(__name__)

class DocumentIntelligence:
    """AI-powered document processing and categorization"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
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
                file_content = await file.read()
                content = file_content.decode('utf-8')
            
            # Validate content length
            if len(content.strip()) == 0:
                raise HTTPException(status_code=400, detail="Document appears to be empty")
            
            # AI-powered categorization
            categories = await self.ai_categorize_content(content)
            
            # Extract product relationships
            relationships = await self.extract_product_relationships(content)
            
            # Store in knowledge base
            knowledge_id = str(uuid.uuid4())
            
            return {
                'knowledge_id': knowledge_id,
                'filename': file.filename,
                'content_length': len(content),
                'categories': categories,
                'relationships': relationships,
                'processed_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    async def extract_pdf_content(self, file: UploadFile) -> str:
        """Extract text from PDF"""
        try:
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if not text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise HTTPException(status_code=400, detail=f"Error extracting PDF content: {str(e)}")
    
    async def extract_excel_content(self, file: UploadFile) -> str:
        """Extract content from Excel files"""
        try:
            content = await file.read()
            df = pd.read_excel(BytesIO(content))
            
            if df.empty:
                raise ValueError("Excel file appears to be empty")
            
            # Convert to structured text
            text_content = df.to_string(index=False)
            return text_content
        except Exception as e:
            logger.error(f"Excel extraction error: {e}")
            raise HTTPException(status_code=400, detail=f"Error extracting Excel content: {str(e)}")
    
    async def ai_categorize_content(self, content: str) -> Dict[str, List[str]]:
        """AI-powered content categorization"""
        # Truncate content to avoid token limits
        content_sample = content[:3000] + "..." if len(content) > 3000 else content
        
        prompt = f"""
        Analyze this audio equipment document and categorize the content into these categories:
        
        1. PRODUCT_SPECS: Technical specifications, power ratings, frequency response, etc.
        2. COMPATIBILITY_RULES: What products work together, impedance matching, etc.
        3. PRICING_INFO: Prices, discounts, special offers, pricing tiers
        4. SYSTEM_DESIGNS: Complete system recommendations, room setups
        5. BRAND_RELATIONSHIPS: Which brands work well together, partnerships
        
        Content: {content_sample}
        
        Return only valid JSON format:
        {{
            "product_specs": ["spec1", "spec2"],
            "compatibility_rules": ["rule1", "rule2"],
            "pricing_info": ["price1", "price2"],
            "system_designs": ["design1", "design2"],
            "brand_relationships": ["relationship1", "relationship2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that categorizes audio equipment documentation. Return only valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Clean up response if it contains markdown formatting
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(response_content)
                # Validate that all expected keys are present
                for key in self.categories.keys():
                    if key not in result:
                        result[key] = []
                return result
            except json.JSONDecodeError as je:
                logger.error(f"JSON decode error: {je}, Response: {response_content}")
                return {category: [] for category in self.categories.keys()}
            
        except Exception as e:
            logger.error(f"AI categorization error: {e}")
            return {category: [] for category in self.categories.keys()}
    
    async def extract_product_relationships(self, content: str) -> List[Dict]:
        """Extract product compatibility relationships"""
        # Truncate content to avoid token limits
        content_sample = content[:3000] + "..." if len(content) > 3000 else content
        
        prompt = f"""
        Extract product relationships from this audio equipment content.
        Look for phrases like "works with", "compatible with", "pairs well with", "recommended for".
        
        Content: {content_sample}
        
        Return only valid JSON array of relationships:
        [
            {{"product_a": "Denon AVR-X1800H", "product_b": "Monitor Audio Bronze", "relationship": "pairs_well_with"}},
            {{"product_a": "8 ohm speakers", "product_b": "100W amplifier", "relationship": "compatible_with"}}
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract product relationships from audio equipment text. Return only valid JSON array."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Clean up response if it contains markdown formatting
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(response_content)
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                logger.error(f"JSON decode error in relationships, Response: {response_content}")
                return []
            
        except Exception as e:
            logger.error(f"Relationship extraction error: {e}")
            return []

class EnhancedAudioConsultantAI:
    """Professional audio consultant AI with training knowledge"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
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
        
        # Prepare product context
        product_context = ""
        if products_found:
            product_context = f"Found {len(products_found)} relevant products: "
            for product in products_found[:3]:  # Limit to top 3
                product_context += f"{product.get('name', 'Unknown')} ({product.get('price_formatted', 'Price N/A')}), "
        
        system_prompt = f"""
        You are a professional audio consultant at Audico SA with deep expertise in audio systems.
        
        PERSONALITY:
        - Professional but conversational (not robotic)
        - Knowledgeable about audio equipment and compatibility
        - Helpful in suggesting complete systems
        - Enthusiastic about great audio experiences
        
        KNOWLEDGE BASE:
        {json.dumps(relevant_knowledge, indent=2)[:1000]}
        
        CURRENT CONTEXT:
        - Customer category: {category}
        - {product_context}
        - Conversation context: {conversation_context}
        
        INSTRUCTIONS:
        - If customer asks about speakers after selecting a receiver, suggest compatible options
        - Mention special pricing when available
        - Ask follow-up questions about room size, budget, preferences
        - Suggest complete systems, not just individual items
        - Use natural language, avoid bullet points
        - Reference specific products from the inventory when relevant
        - Keep responses concise but informative (under 400 words)
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
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
            return "I'm having trouble accessing my knowledge right now. Let me help you with what I know about your audio needs. What specific equipment are you looking for?"
    
    def get_relevant_knowledge(self, query: str) -> Dict:
        """Retrieve relevant knowledge for the query"""
        relevant = {}
        query_lower = query.lower()
        
        # Check for speaker-related queries
        if any(word in query_lower for word in ['speaker', 'speakers', 'bookshelf', 'floorstanding']):
            relevant['speaker_recommendations'] = self.knowledge_base.get('product_specs', [])[:3]
            if not relevant['speaker_recommendations']:
                relevant['speaker_recommendations'] = [
                    "Monitor Audio Bronze series pairs well with Denon receivers",
                    "For 8K receivers, consider 6-8 ohm speakers",
                    "Bookshelf speakers ideal for smaller rooms"
                ]
        
        # Check for receiver-related queries  
        if any(word in query_lower for word in ['receiver', 'amplifier', 'avr', 'denon', 'yamaha']):
            relevant['receiver_info'] = self.knowledge_base.get('compatibility_rules', [])[:3]
            if not relevant['receiver_info']:
                relevant['receiver_info'] = [
                    "Denon X-series offers excellent value",
                    "Consider room size for power requirements",
                    "8K support future-proofs your investment"
                ]
        
        # Add pricing information if available
        if self.knowledge_base.get('pricing_info'):
            relevant['pricing_info'] = self.knowledge_base['pricing_info'][:2]
        
        return relevant
    
    def update_knowledge_base(self, categories: Dict, relationships: List[Dict]):
        """Update knowledge base with new training data"""
        for category, items in categories.items():
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []
            
            # Add new items if they're not already present
            for item in items:
                if item not in self.knowledge_base[category]:
                    self.knowledge_base[category].append(item)
        
        # Store relationships
        if 'relationships' not in self.knowledge_base:
            self.knowledge_base['relationships'] = []
        
        for rel in relationships:
            if rel not in self.knowledge_base['relationships']:
                self.knowledge_base['relationships'].append(rel)
        
        logger.info(f"Knowledge base updated. Total categories: {len(self.knowledge_base)}")

# Global instances
document_intelligence: Optional[DocumentIntelligence] = None
audio_consultant_ai: Optional[EnhancedAudioConsultantAI] = None

def initialize_ai_training(openai_api_key: str) -> bool:
    """Initialize AI training components"""
    global document_intelligence, audio_consultant_ai
    
    try:
        document_intelligence = DocumentIntelligence(openai_api_key)
        audio_consultant_ai = EnhancedAudioConsultantAI(openai_api_key)
        logger.info("🧠 AI Training System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"AI Training initialization error: {e}")
        return False

def get_knowledge_base_summary() -> Dict[str, Any]:
    """Get summary of current knowledge base"""
    if not audio_consultant_ai:
        return {"error": "AI system not initialized"}
    
    summary = {}
    for category, items in audio_consultant_ai.knowledge_base.items():
        summary[category] = {
            "count": len(items),
            "sample": items[:2] if items else []
        }
    
    return summary