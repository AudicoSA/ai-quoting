from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from datetime import datetime
import uuid
from io import BytesIO
import asyncio

logger = logging.getLogger(__name__)

class PricingConfig(BaseModel):
    """Configuration for pricing context"""
    price_type: str = "cost_excl_vat"  # cost_excl_vat, cost_incl_vat, retail_incl_vat
    vat_rate: float = 0.15  # 15% VAT
    markup_percentage: float = 0.40  # 40% markup
    supplier_name: str = ""
    currency: str = "ZAR"

class ExcelStructureAnalyzer:
    """Analyzes complex Excel structures for multi-brand pricelists"""
    
    def __init__(self):
        self.brand_patterns = [
            r'^[A-Z][A-Z0-9\-_&\s]{2,20}$',  # Brand name patterns
            r'^[A-Z]{2,}[\s\-][A-Z0-9]+$'     # Brand with model patterns
        ]
        self.price_patterns = [
            r'price.*excl.*vat', r'price.*incl.*vat', r'cost.*excl', r'cost.*incl',
            r'rrp', r'retail', r'selling.*price', r'unit.*price', r'list.*price'
        ]
        self.product_patterns = [
            r'stock.*code', r'product.*code', r'item.*code', r'model', r'sku'
        ]
    
    def detect_excel_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect the structure of a complex Excel file"""
        structure = {
            "type": "unknown",
            "brands": [],
            "columns": {},
            "data_start_row": 0,
            "layout": "single"  # single, multi_column, multi_brand
        }
        
        # Convert all data to string for analysis
        df_str = df.astype(str)
        
        # Check first few rows for brand headers
        brand_row = None
        for i in range(min(5, len(df_str))):
            row = df_str.iloc[i]
            brands_found = self._detect_brands_in_row(row)
            if len(brands_found) >= 2:  # Multiple brands found
                brand_row = i
                structure["brands"] = brands_found
                structure["layout"] = "multi_brand"
                break
        
        if brand_row is not None:
            # Multi-brand layout detected
            structure["data_start_row"] = brand_row + 2  # Usually brands, then headers, then data
            structure["columns"] = self._map_brand_columns(df_str, brand_row, brands_found)
        else:
            # Single brand or simple structure
            structure["layout"] = "single"
            structure["data_start_row"] = self._find_data_start_row(df_str)
            structure["columns"] = self._detect_simple_columns(df_str)
        
        return structure
    
    def _detect_brands_in_row(self, row: pd.Series) -> List[Dict]:
        """Detect brand names in a row"""
        brands = []
        for col_idx, value in enumerate(row):
            if pd.isna(value) or str(value).strip() == '':
                continue
            
            value_str = str(value).strip().upper()
            
            # Check if it matches brand patterns
            if any(re.match(pattern, value_str, re.IGNORECASE) for pattern in self.brand_patterns):
                # Additional checks for known tech brands
                if (len(value_str) >= 3 and 
                    not value_str.startswith('UPDATED') and
                    not any(word in value_str for word in ['PRICE', 'CODE', 'STOCK', 'ITEM'])):
                    brands.append({
                        "name": value_str,
                        "column": col_idx,
                        "original_value": str(value).strip()
                    })
        
        return brands
    
    def _map_brand_columns(self, df: pd.DataFrame, brand_row: int, brands: List[Dict]) -> Dict:
        """Map columns for each brand in multi-brand layout"""
        column_map = {}
        
        # Check the row after brands for column headers
        if brand_row + 1 < len(df):
            header_row = df.iloc[brand_row + 1]
            
            for brand in brands:
                brand_name = brand["name"]
                brand_col = brand["column"]
                
                # Look for columns near this brand
                brand_columns = {}
                search_range = 5  # Look 5 columns to the right
                
                for offset in range(search_range):
                    col_idx = brand_col + offset
                    if col_idx < len(header_row):
                        header_value = str(header_row.iloc[col_idx]).strip().lower()
                        
                        # Detect column types
                        if any(pattern in header_value for pattern in ['stock', 'code', 'item']):
                            brand_columns["product_code"] = col_idx
                        elif any(pattern in header_value for pattern in ['price', 'cost']):
                            brand_columns["price"] = col_idx
                        elif any(pattern in header_value for pattern in ['rrp', 'retail']):
                            brand_columns["retail_price"] = col_idx
                
                if brand_columns:  # Only add if we found relevant columns
                    column_map[brand_name] = brand_columns
        
        return column_map
    
    def _find_data_start_row(self, df: pd.DataFrame) -> int:
        """Find where actual data starts in simple layout"""
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            # Look for rows that seem to contain actual product data
            non_empty_count = sum(1 for val in row if pd.notna(val) and str(val).strip() != '')
            if non_empty_count >= 2:  # At least 2 non-empty columns
                return i
        return 0
    
    def _detect_simple_columns(self, df: pd.DataFrame) -> Dict:
        """Detect columns in simple single-brand layout"""
        columns = {}
        
        # Check first few rows for headers
        for i in range(min(3, len(df))):
            row = df.iloc[i]
            for col_idx, value in enumerate(row):
                if pd.isna(value):
                    continue
                
                value_str = str(value).strip().lower()
                
                if any(pattern in value_str for pattern in self.product_patterns):
                    columns["product_code"] = col_idx
                elif any(re.search(pattern, value_str) for pattern in self.price_patterns):
                    columns["price"] = col_idx
        
        return columns

class EnhancedDocumentIntelligence:
    """Enhanced AI-powered document processing with multi-brand Excel support"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.excel_analyzer = ExcelStructureAnalyzer()
        self.categories = {
            'product_specs': [],
            'compatibility_rules': [],
            'pricing_info': [],
            'system_designs': [],
            'brand_relationships': [],
            'suppliers': []
        }
    
    async def process_document_with_config(self, file: UploadFile, config: PricingConfig = None) -> Dict[str, Any]:
        """Process document with pricing configuration"""
        try:
            if file.filename.endswith(('.xlsx', '.xls')):
                return await self.process_excel_with_config(file, config)
            elif file.filename.endswith('.pdf'):
                return await self.process_pdf_content(file)
            else:
                return await self.process_text_content(file)
                
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    async def process_excel_with_config(self, file: UploadFile, config: PricingConfig = None) -> Dict[str, Any]:
        """Process Excel file with pricing configuration"""
        if config is None:
            config = PricingConfig()
        
        content = await file.read()
        
        try:
            # Try reading Excel file
            df = pd.read_excel(BytesIO(content), header=None)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading Excel file: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel file appears to be empty")
        
        # Analyze Excel structure
        structure = self.excel_analyzer.detect_excel_structure(df)
        
        # Extract products based on structure
        if structure["layout"] == "multi_brand":
            extracted_data = self._extract_multi_brand_data(df, structure, config)
        else:
            extracted_data = self._extract_simple_data(df, structure, config)
        
        # Process with AI for additional insights
        ai_analysis = await self._ai_analyze_extracted_data(extracted_data, config)
        
        # Combine results
        result = {
            'knowledge_id': str(uuid.uuid4()),
            'filename': file.filename,
            'supplier': config.supplier_name,
            'structure_detected': structure,
            'products_extracted': len(extracted_data.get('products', [])),
            'extracted_data': extracted_data,
            'ai_analysis': ai_analysis,
            'pricing_config': config.dict(),
            'processed_at': datetime.now().isoformat(),
            'status': 'success'
        }
        
        return result
    
    def _extract_multi_brand_data(self, df: pd.DataFrame, structure: Dict, config: PricingConfig) -> Dict:
        """Extract data from multi-brand Excel layout"""
        extracted_data = {
            'products': [],
            'brands': list(structure['columns'].keys()),
            'supplier': config.supplier_name
        }
        
        data_start = structure['data_start_row']
        
        for brand_name, columns in structure['columns'].items():
            if 'product_code' not in columns or 'price' not in columns:
                continue
                
            product_col = columns['product_code']
            price_col = columns['price']
            
            # Extract products for this brand
            for i in range(data_start, len(df)):
                try:
                    product_code = df.iloc[i, product_col]
                    price_value = df.iloc[i, price_col]
                    
                    if pd.isna(product_code) or pd.isna(price_value):
                        continue
                    
                    product_code_str = str(product_code).strip()
                    price_str = str(price_value).strip()
                    
                    # Skip invalid entries
                    if (product_code_str == '' or price_str == '' or 
                        price_str.upper() in ['P.O.R', 'POA', 'CALL'] or
                        product_code_str.upper() in ['STOCK CODE', 'ITEM CODE']):
                        continue
                    
                    # Parse price
                    parsed_price = self._parse_price(price_str)
                    if parsed_price <= 0:
                        continue
                    
                    # Calculate different price types
                    prices = self._calculate_prices(parsed_price, config)
                    
                    product = {
                        'product_code': product_code_str,
                        'brand': brand_name,
                        'supplier': config.supplier_name,
                        'original_price': parsed_price,
                        'price_type': config.price_type,
                        **prices,
                        'currency': config.currency,
                        'row': i + 1
                    }
                    
                    extracted_data['products'].append(product)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {i} for brand {brand_name}: {e}")
                    continue
        
        return extracted_data
    
    def _extract_simple_data(self, df: pd.DataFrame, structure: Dict, config: PricingConfig) -> Dict:
        """Extract data from simple single-brand layout"""
        extracted_data = {
            'products': [],
            'brands': [config.supplier_name],
            'supplier': config.supplier_name
        }
        
        columns = structure['columns']
        if 'product_code' not in columns or 'price' not in columns:
            return extracted_data
        
        product_col = columns['product_code']
        price_col = columns['price']
        data_start = structure['data_start_row']
        
        for i in range(data_start, len(df)):
            try:
                product_code = df.iloc[i, product_col]
                price_value = df.iloc[i, price_col]
                
                if pd.isna(product_code) or pd.isna(price_value):
                    continue
                
                product_code_str = str(product_code).strip()
                price_str = str(price_value).strip()
                
                if product_code_str == '' or price_str == '':
                    continue
                
                parsed_price = self._parse_price(price_str)
                if parsed_price <= 0:
                    continue
                
                prices = self._calculate_prices(parsed_price, config)
                
                product = {
                    'product_code': product_code_str,
                    'brand': config.supplier_name,
                    'supplier': config.supplier_name,
                    'original_price': parsed_price,
                    'price_type': config.price_type,
                    **prices,
                    'currency': config.currency,
                    'row': i + 1
                }
                
                extracted_data['products'].append(product)
                
            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                continue
        
        return extracted_data
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price from string, handling various formats"""
        if not price_str or price_str.upper() in ['P.O.R', 'POA', 'CALL', 'N/A']:
            return 0
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[R$€£\s,]', '', str(price_str))
        
        try:
            return float(cleaned)
        except ValueError:
            return 0
    
    def _calculate_prices(self, original_price: float, config: PricingConfig) -> Dict[str, float]:
        """Calculate different price types based on configuration"""
        prices = {}
        
        if config.price_type == "cost_excl_vat":
            prices['cost_excl_vat'] = original_price
            prices['cost_incl_vat'] = original_price * (1 + config.vat_rate)
            prices['retail_incl_vat'] = prices['cost_incl_vat'] * (1 + config.markup_percentage)
            
        elif config.price_type == "cost_incl_vat":
            prices['cost_incl_vat'] = original_price
            prices['cost_excl_vat'] = original_price / (1 + config.vat_rate)
            prices['retail_incl_vat'] = original_price * (1 + config.markup_percentage)
            
        elif config.price_type == "retail_incl_vat":
            prices['retail_incl_vat'] = original_price
            prices['cost_incl_vat'] = original_price / (1 + config.markup_percentage)
            prices['cost_excl_vat'] = prices['cost_incl_vat'] / (1 + config.vat_rate)
        
        # Calculate margin
        if prices.get('retail_incl_vat') and prices.get('cost_incl_vat'):
            margin = (prices['retail_incl_vat'] - prices['cost_incl_vat']) / prices['retail_incl_vat']
            prices['margin_percentage'] = margin * 100
        
        return prices
    
    async def _ai_analyze_extracted_data(self, extracted_data: Dict, config: PricingConfig) -> Dict:
        """Use AI to analyze extracted product data"""
        if not extracted_data.get('products'):
            return {'categories': {}, 'insights': []}
        
        # Sample products for AI analysis
        sample_products = extracted_data['products'][:20]  # Analyze first 20 products
        
        sample_text = json.dumps(sample_products, indent=2)[:2000]  # Limit text length
        
        prompt = f"""
        Analyze this product data from supplier "{config.supplier_name}":
        
        {sample_text}
        
        Extract:
        1. Product categories and types
        2. Brand relationships and compatibility
        3. Pricing patterns and ranges
        4. Notable insights about the product range
        
        Return JSON format:
        {{
            "categories": {{"category1": ["item1", "item2"]}},
            "insights": ["insight1", "insight2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing product data and pricing. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            response_content = response.choices[0].message.content.strip()
            
            # Clean up response
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '').strip()
            
            return json.loads(response_content)
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return {'categories': {}, 'insights': []}
    
    async def process_pdf_content(self, file: UploadFile) -> Dict[str, Any]:
        """Process PDF content (existing method)"""
        # Your existing PDF processing code here
        return {'message': 'PDF processing not yet implemented in this version'}
    
    async def process_text_content(self, file: UploadFile) -> Dict[str, Any]:
        """Process text content (existing method)"""
        # Your existing text processing code here
        return {'message': 'Text processing not yet implemented in this version'}

class EnhancedAudioConsultantAI:
    """Enhanced audio consultant AI with supplier pricing intelligence"""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.knowledge_base = {}
        self.supplier_data = {}
    
    async def generate_professional_response(self, 
                                           user_message: str, 
                                           products_found: List[Dict],
                                           conversation_context: Dict,
                                           category: str) -> str:
        """Generate professional response with supplier pricing intelligence"""
        
        # Check if we have supplier pricing data for mentioned products
        pricing_context = self._get_supplier_pricing_context(user_message)
        
        system_prompt = f"""
        You are a professional audio consultant at Audico SA with access to real supplier pricing data.
        
        SUPPLIER PRICING CONTEXT:
        {json.dumps(pricing_context, indent=2)[:1000]}
        
        KNOWLEDGE BASE:
        {json.dumps(self.knowledge_base, indent=2)[:1000]}
        
        INSTRUCTIONS:
        - Use actual supplier pricing when available
        - Mention cost prices and margins when relevant
        - Reference specific suppliers (Nology, etc.) when discussing pricing
        - Provide professional advice on product selection
        - Suggest complete systems with compatible products
        - Keep responses conversational but informative
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
            return "I'm here to help with your audio system needs. What specific equipment are you looking for?"
    
    def _get_supplier_pricing_context(self, query: str) -> Dict:
        """Get relevant supplier pricing for the query"""
        context = {}
        
        # Look for product codes or brands mentioned in query
        query_upper = query.upper()
        
        for supplier, supplier_info in self.supplier_data.items():
            for product in supplier_info.get('products', []):
                product_code = product.get('product_code', '').upper()
                brand = product.get('brand', '').upper()
                
                if product_code in query_upper or brand in query_upper:
                    if supplier not in context:
                        context[supplier] = []
                    context[supplier].append({
                        'product_code': product.get('product_code'),
                        'brand': product.get('brand'),
                        'cost_excl_vat': product.get('cost_excl_vat'),
                        'retail_incl_vat': product.get('retail_incl_vat'),
                        'margin_percentage': product.get('margin_percentage')
                    })
        
        return context
    
    def update_knowledge_base(self, categories: Dict, relationships: List[Dict], supplier_data: Dict = None):
        """Update knowledge base with new training data including supplier information"""
        
        # Update categories
        for category, items in categories.items():
            if category not in self.knowledge_base:
                self.knowledge_base[category] = []
            
            for item in items:
                if item not in self.knowledge_base[category]:
                    self.knowledge_base[category].append(item)
        
        # Update supplier data
        if supplier_data:
            supplier_name = supplier_data.get('supplier')
            if supplier_name:
                self.supplier_data[supplier_name] = supplier_data
        
        logger.info(f"Knowledge base updated. Categories: {len(self.knowledge_base)}, Suppliers: {len(self.supplier_data)}")

# Global instances
document_intelligence: Optional[EnhancedDocumentIntelligence] = None
audio_consultant_ai: Optional[EnhancedAudioConsultantAI] = None

def initialize_ai_training(openai_api_key: str) -> bool:
    """Initialize enhanced AI training components"""
    global document_intelligence, audio_consultant_ai
    
    try:
        document_intelligence = EnhancedDocumentIntelligence(openai_api_key)
        audio_consultant_ai = EnhancedAudioConsultantAI(openai_api_key)
        logger.info("🧠 Enhanced AI Training System initialized successfully")
        return True
    except Exception as e:
        logger.error(f"AI Training initialization error: {e}")
        return False

def get_enhanced_knowledge_base_summary() -> Dict[str, Any]:
    """Get enhanced summary of current knowledge base including supplier data"""
    if not audio_consultant_ai:
        return {"error": "AI system not initialized"}
    
    summary = {
        'categories': {},
        'suppliers': {},
        'total_products': 0
    }
    
    # Summarize categories
    for category, items in audio_consultant_ai.knowledge_base.items():
        summary['categories'][category] = {
            "count": len(items),
            "sample": items[:3] if items else []
        }
    
    # Summarize supplier data
    for supplier, data in audio_consultant_ai.supplier_data.items():
        products = data.get('products', [])
        summary['suppliers'][supplier] = {
            "product_count": len(products),
            "brands": list(set(p.get('brand', '') for p in products)),
            "price_range": {
                "min": min((p.get('retail_incl_vat', 0) for p in products if p.get('retail_incl_vat')), default=0),
                "max": max((p.get('retail_incl_vat', 0) for p in products if p.get('retail_incl_vat')), default=0)
            }
        }
        summary['total_products'] += len(products)
    
    return summary