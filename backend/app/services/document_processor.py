import pandas as pd
import pdfplumber
from typing import Dict, List, Any, Optional
import re
import logging
from pathlib import Path
import openai
from sqlalchemy.orm import Session
from ..models.database import Product, Supplier, PricelistUpload

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, openai_api_key: str):
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        
    async def process_document(self, file_path: str, supplier_id: int, db: Session) -> Dict[str, Any]:
        """Main document processing entry point"""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension in ['.xlsx', '.xls']:
            return await self._process_excel(file_path, supplier_id, db)
        elif file_extension == '.pdf':
            return await self._process_pdf(file_path, supplier_id, db)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    
    async def _process_excel(self, file_path: str, supplier_id: int, db: Session) -> Dict[str, Any]:
        """Process Excel files with AI-enhanced parsing"""
        try:
            # Get supplier info
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                raise ValueError("Supplier not found")
            
            # Read Excel file
            df = pd.read_excel(file_path, nrows=10)
            
            # Detect structure type
            structure_type = self._detect_excel_structure(df)
            
            if structure_type == "nology_multi_brand":
                return await self._process_nology_format(file_path, supplier, db)
            elif structure_type == "standard_vertical":
                return await self._process_standard_vertical(file_path, supplier, db)
            else:
                # Use AI to understand the format
                return await self._process_with_ai(file_path, supplier, db, "excel")
                
        except Exception as e:
            logger.error(f"Excel processing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _process_pdf(self, file_path: str, supplier_id: int, db: Session) -> Dict[str, Any]:
        """Process PDF files with AI-enhanced parsing"""
        try:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                raise ValueError("Supplier not found")
            
            # Extract text from PDF
            text_content = self._extract_pdf_text(file_path)
            
            # Detect if it's a Denon-style format or other
            if "Old RRP" in text_content and "New RRP" in text_content:
                return await self._process_denon_format(text_content, supplier, db)
            else:
                # Use AI to understand the format
                return await self._process_with_ai(file_path, supplier, db, "pdf", text_content)
                
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {"success": False, "error": str(e)}
    
    def _detect_excel_structure(self, df: pd.DataFrame) -> str:
        """Detect Excel file structure type"""
        try:
            # Check for Nology multi-brand format
            if len(df) > 2:
                brands_row = df.iloc[1]
                header_row = df.iloc[2]
                
                brand_count = sum(1 for cell in brands_row if pd.notna(cell) and str(cell).strip())
                header_count = sum(1 for cell in header_row if pd.notna(cell) and 'code' in str(cell).lower())
                
                if brand_count > 2 and header_count > 2:
                    return "nology_multi_brand"
            
            # Check for standard vertical format
            if 'stock' in str(df.columns).lower() or 'code' in str(df.columns).lower():
                return "standard_vertical"
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    async def _process_nology_format(self, file_path: str, supplier: Supplier, db: Session) -> Dict[str, Any]:
        """Process Nology multi-brand horizontal format"""
        try:
            df = pd.read_excel(file_path)
            
            # Get structure rows
            brands_row = df.iloc[1] if len(df) > 1 else pd.Series()
            header_row = df.iloc[2] if len(df) > 2 else pd.Series()
            
            # Map brands to columns
            brand_positions = {}
            current_brand = None
            
            for idx, cell in enumerate(brands_row):
                if pd.notna(cell) and str(cell).strip():
                    current_brand = str(cell).strip().upper()
                    if current_brand not in brand_positions:
                        brand_positions[current_brand] = []
                if current_brand:
                    brand_positions[current_brand].append(idx)
            
            products = []
            
            # Process each brand
            for brand, columns in brand_positions.items():
                # Find stock code and price columns
                stock_col = None
                price_col = None
                
                for col_idx in columns:
                    if col_idx < len(header_row):
                        header = str(header_row.iloc[col_idx]).lower()
                        if 'stock' in header or 'code' in header:
                            stock_col = col_idx
                        elif 'price' in header and 'excl' in header:
                            price_col = col_idx
                
                if stock_col is not None and price_col is not None:
                    # Extract products for this brand
                    for row_idx in range(3, len(df)):
                        row = df.iloc[row_idx]
                        
                        if stock_col < len(row) and price_col < len(row):
                            stock_code = row.iloc[stock_col]
                            price = row.iloc[price_col]
                            
                            if pd.notna(stock_code) and pd.notna(price):
                                stock_code = str(stock_code).strip()
                                
                                # Handle price
                                if str(price) != 'P.O.R':
                                    try:
                                        price_val = float(price)
                                        
                                        # Apply markup if configured
                                        if supplier.markup_percentage > 0:
                                            if supplier.vat_inclusive:
                                                cost_price = price_val / 1.15  # Remove VAT first
                                            else:
                                                cost_price = price_val
                                            
                                            final_price = cost_price * (1 + supplier.markup_percentage / 100)
                                        else:
                                            final_price = price_val
                                        
                                        products.append({
                                            'brand': brand,
                                            'stock_code': stock_code,
                                            'product_name': stock_code,  # Use stock code as name for now
                                            'price_excl_vat': final_price,
                                            'cost_price': price_val,
                                            'markup_applied': supplier.markup_percentage,
                                            'supplier_id': supplier.id,
                                            'parsed_by_ai': False
                                        })
                                        
                                    except ValueError:
                                        continue
            
            return {
                'success': True,
                'products': products,
                'brands_detected': len(brand_positions),
                'structure_type': 'nology_multi_brand'
            }
            
        except Exception as e:
            logger.error(f"Nology format processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _process_denon_format(self, text_content: str, supplier: Supplier, db: Session) -> Dict[str, Any]:
        """Process Denon-style PDF format"""
        try:
            products = []
            lines = text_content.split('\n')
            
            current_category = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Detect category headers
                if line and line.isupper() and len(line) > 3 and not re.search(r'R\d+', line):
                    current_category = line
                    continue
                
                # Look for product lines with prices
                price_pattern = r'R(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
                prices = re.findall(price_pattern, line)
                
                if len(prices) >= 2:  # Old RRP and New RRP
                    # Extract product name (everything before first price)
                    product_match = re.search(r'^(.+?)\s+R\d', line)
                    if product_match:
                        product_name = product_match.group(1).strip()
                        
                        # Extract prices
                        old_price = float(prices[0].replace(',', ''))
                        new_price = float(prices[1].replace(',', ''))
                        
                        # Use new price as base
                        final_price = new_price
                        
                        # Apply markup if configured
                        if supplier.markup_percentage > 0:
                            if supplier.vat_inclusive:
                                cost_price = final_price / 1.15
                            else:
                                cost_price = final_price
                            
                            final_price = cost_price * (1 + supplier.markup_percentage / 100)
                        
                        # Generate stock code from product name
                        stock_code = re.sub(r'[^A-Za-z0-9\-]', '', product_name.replace(' ', '-'))[:20]
                        
                        products.append({
                            'brand': supplier.name,
                            'stock_code': stock_code,
                            'product_name': product_name,
                            'category': current_category,
                            'price_excl_vat': final_price,
                            'cost_price': new_price,
                            'markup_applied': supplier.markup_percentage,
                            'supplier_id': supplier.id,
                            'parsed_by_ai': False
                        })
            
            return {
                'success': True,
                'products': products,
                'brands_detected': 1,
                'structure_type': 'denon_pdf'
            }
            
        except Exception as e:
            logger.error(f"Denon format processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _process_with_ai(self, file_path: str, supplier: Supplier, db: Session, file_type: str, text_content: str = None) -> Dict[str, Any]:
        """Use AI to process unknown document formats"""
        if not self.openai_client:
            return {'success': False, 'error': 'OpenAI API key not configured'}
        
        try:
            if file_type == "excel":
                # Read first few rows for AI analysis
                df = pd.read_excel(file_path, nrows=20)
                content = df.to_string()
            else:
                content = text_content[:5000]  # Limit content size
            
            # Create AI prompt
            prompt = f"""
            You are an expert at parsing pricelists. Analyze this {file_type} content and extract product information.
            
            Supplier: {supplier.name}
            VAT Setting: {'Inclusive' if supplier.vat_inclusive else 'Exclusive'}
            Markup: {supplier.markup_percentage}%
            
            Content:
            {content}
            
            Please identify:
            1. Product names
            2. Stock codes
            3. Prices
            4. Brands
            5. Categories
            
            Return a JSON structure with products array containing: brand, stock_code, product_name, price_excl_vat, category
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            
            # Parse AI response
            import json
            try:
                ai_data = json.loads(response.choices[0].message.content)
                products = ai_data.get('products', [])
                
                # Apply markup to AI-parsed products
                for product in products:
                    if supplier.markup_percentage > 0 and 'price_excl_vat' in product:
                        base_price = product['price_excl_vat']
                        if supplier.vat_inclusive:
                            cost_price = base_price / 1.15
                        else:
                            cost_price = base_price
                        
                        product['price_excl_vat'] = cost_price * (1 + supplier.markup_percentage / 100)
                        product['cost_price'] = base_price
                        product['markup_applied'] = supplier.markup_percentage
                    
                    product['supplier_id'] = supplier.id
                    product['parsed_by_ai'] = True
                
                return {
                    'success': True,
                    'products': products,
                    'brands_detected': len(set(p.get('brand', '') for p in products)),
                    'structure_type': 'ai_parsed'
                }
                
            except json.JSONDecodeError:
                return {'success': False, 'error': 'AI response not valid JSON'}
                
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
        return text