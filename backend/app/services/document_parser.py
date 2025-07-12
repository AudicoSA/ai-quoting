import pandas as pd
import pdfplumber
import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self):
        pass
    
    async def parse_excel(self, file_path: str, supplier_config: Dict = None) -> Dict[str, Any]:
        """Parse Excel files like Nology format"""
        try:
            # Read first few rows to detect structure
            df_preview = pd.read_excel(file_path, nrows=10)
            
            # Detect Nology-style multi-brand format
            if len(df_preview) > 2:
                brands_row = df_preview.iloc[1] if len(df_preview) > 1 else pd.Series()
                header_row = df_preview.iloc[2] if len(df_preview) > 2 else pd.Series()
                
                # Extract brands
                brands = []
                for cell in brands_row:
                    if pd.notna(cell) and str(cell).strip():
                        brand = str(cell).strip().upper()
                        if brand and len(brand) < 30:
                            brands.append(brand)
                
                # Load full file
                df_full = pd.read_excel(file_path)
                products = []
                
                # Map brand positions
                brand_positions = {}
                for idx, cell in enumerate(brands_row):
                    if pd.notna(cell) and str(cell).strip():
                        brand = str(cell).strip().upper()
                        if brand not in brand_positions:
                            brand_positions[brand] = []
                        brand_positions[brand].append(idx)
                
                # Extract products
                for brand, columns in brand_positions.items():
                    for row_idx in range(3, len(df_full)):
                        row = df_full.iloc[row_idx]
                        stock_code = None
                        price = None
                        
                        for col_idx in columns:
                            if col_idx < len(row) and col_idx < len(header_row):
                                cell_value = row.iloc[col_idx]
                                header = str(header_row.iloc[col_idx]).lower() if pd.notna(header_row.iloc[col_idx]) else ""
                                
                                if pd.notna(cell_value):
                                    if 'stock' in header or 'code' in header:
                                        stock_code = str(cell_value).strip()
                                    elif 'price' in header and 'excl' in header:
                                        if str(cell_value) != 'P.O.R':
                                            try:
                                                price = float(cell_value)
                                            except:
                                                pass
                        
                        if stock_code and price:
                            # Apply markup if configured
                            final_price = price
                            if supplier_config and 'markup_percentage' in supplier_config:
                                markup = supplier_config['markup_percentage'] / 100
                                final_price = price * (1 + markup)
                            
                            products.append({
                                'brand': brand,
                                'stock_code': stock_code,
                                'product_name': stock_code,
                                'price_excl_vat': final_price,
                                'original_price': price,
                                'currency': supplier_config.get('default_currency', 'ZAR') if supplier_config else 'ZAR',
                                'supplier': supplier_config.get('name', 'Unknown') if supplier_config else 'Unknown',
                                'parsed_by_ai': True
                            })
                
                return {
                    'success': True,
                    'total_products': len(products),
                    'brands_detected': len(brands),
                    'products': products,
                    'structure_type': 'horizontal_multi_brand'
                }
            
            return {
                'success': False,
                'error': 'Unsupported Excel format',
                'products': []
            }
            
        except Exception as e:
            logger.error(f"Excel parsing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'products': []
            }
    
    async def parse_pdf(self, file_path: str, supplier_config: Dict = None) -> Dict[str, Any]:
        """Parse PDF files like Denon format"""
        try:
            products = []
            current_category = None
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Detect category headers (like "AV Receivers", "Soundbars")
                        if re.match(r'^[A-Z][A-Za-z\s&]+$', line) and len(line) < 50:
                            current_category = line
                            continue
                        
                        # Try to parse product lines with prices
                        # Pattern: Product description followed by prices
                        price_pattern = r'R([\d,]+\.?\d*)'
                        prices = re.findall(price_pattern, line)
                        
                        if prices and len(prices) >= 1:
                            # Extract product name (everything before first price)
                            price_match = re.search(r'R[\d,]+\.?\d*', line)
                            if price_match:
                                product_name = line[:price_match.start()].strip()
                                
                                if product_name and len(product_name) > 5:
                                    # Extract model number from product name
                                    model_match = re.search(r'^([A-Z0-9\-]+)', product_name)
                                    stock_code = model_match.group(1) if model_match else product_name.split()[0]
                                    
                                    # Use the last price (typically the "New RRP")
                                    price_str = prices[-1].replace(',', '')
                                    try:
                                        price = float(price_str)
                                        
                                        # Apply markup if configured
                                        final_price = price
                                        if supplier_config and 'markup_percentage' in supplier_config:
                                            markup = supplier_config['markup_percentage'] / 100
                                            final_price = price * (1 + markup)
                                        
                                        # Handle VAT
                                        if supplier_config and supplier_config.get('vat_included', False):
                                            final_price = final_price / 1.15  # Convert to excl VAT
                                        
                                        products.append({
                                            'brand': supplier_config.get('name', 'Unknown') if supplier_config else 'Unknown',
                                            'stock_code': stock_code,
                                            'product_name': product_name,
                                            'category': current_category,
                                            'price_excl_vat': final_price,
                                            'original_price': price,
                                            'currency': supplier_config.get('default_currency', 'ZAR') if supplier_config else 'ZAR',
                                            'supplier': supplier_config.get('name', 'Unknown') if supplier_config else 'Unknown',
                                            'parsed_by_ai': True
                                        })
                                    except ValueError:
                                        continue
            
            return {
                'success': True,
                'total_products': len(products),
                'brands_detected': 1,
                'products': products,
                'structure_type': 'category_based_pdf'
            }
            
        except Exception as e:
            logger.error(f"PDF parsing error: {e}")
            return {
                'success': False,
                'error': str(e),
                'products': []
            }