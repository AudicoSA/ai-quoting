# backend/app/services/smart_column_detector.py
import pandas as pd
import re
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SmartColumnDetector:
    def __init__(self):
        self.brand_patterns = [
            r'YEALINK', r'JABRA', r'DNAKE', r'CALL4TEL', r'LG', r'SHELLY',
            r'MIKROTIK', r'ZYXEL', r'TP-LINK', r'VILO', r'CAMBIUM', r'BLUETTI',
            r'MOTOROLA', r'NEAT', r'LOGITECH', r'TELRAD', r'HUAWEI', r'TELTONICA',
            r'SAMSUNG', r'NETGOY', r'MINIX'
        ]
        
        self.product_code_patterns = [
            r'stock.?code', r'product.?code', r'item.?code', r'sku', r'part.?number',
            r'model', r'code'
        ]
        
        self.price_patterns = [
            r'price', r'cost', r'msrp', r'retail', r'excl.*vat', r'incl.*vat',
            r'excluding.*vat', r'including.*vat'
        ]

    def detect_horizontal_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect horizontal multi-brand structure like Nology pricelist
        """
        try:
            structure = {
                "layout_type": "horizontal_multi_brand",
                "brands_detected": [],
                "brand_column_ranges": {},
                "header_rows": [],
                "data_start_row": None,
                "column_mapping": {}
            }
            
            # Step 1: Find header rows and brand positions
            header_info = self._find_brand_headers(df)
            structure.update(header_info)
            
            # Step 2: Map columns for each brand
            column_mapping = self._map_brand_columns(df, structure)
            structure["column_mapping"] = column_mapping
            
            # Step 3: Validate structure
            structure["is_valid"] = self._validate_structure(structure)
            
            logger.info(f"Detected structure: {len(structure['brands_detected'])} brands")
            return structure
            
        except Exception as e:
            logger.error(f"Structure detection failed: {str(e)}")
            return self._create_fallback_structure()

    def _find_brand_headers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find where brands are positioned in the header rows
        """
        brands_detected = []
        brand_column_ranges = {}
        header_rows = []
        data_start_row = None
        
        # Check first 5 rows for brand names
        for row_idx in range(min(5, len(df))):
            row = df.iloc[row_idx]
            row_brands = []
            
            for col_idx, cell_value in enumerate(row):
                if pd.isna(cell_value):
                    continue
                    
                cell_str = str(cell_value).upper().strip()
                
                # Check if this cell contains a brand name
                for brand_pattern in self.brand_patterns:
                    if re.search(brand_pattern, cell_str):
                        brand_name = brand_pattern.replace(r'\.?\?', '')  # Clean pattern
                        
                        if brand_name not in brands_detected:
                            brands_detected.append(brand_name)
                            
                        row_brands.append({
                            "brand": brand_name,
                            "column": col_idx,
                            "row": row_idx,
                            "original_text": cell_str
                        })
            
            if row_brands:
                header_rows.append(row_idx)
                
                # Map brand column ranges
                for i, brand_info in enumerate(row_brands):
                    start_col = brand_info["column"]
                    
                    # Estimate end column (until next brand or end)
                    if i < len(row_brands) - 1:
                        end_col = row_brands[i + 1]["column"] - 1
                    else:
                        end_col = start_col + 3  # Default span of 3 columns
                    
                    brand_column_ranges[brand_info["brand"]] = {
                        "start_col": start_col,
                        "end_col": end_col,
                        "header_row": row_idx
                    }
        
        # Find data start row (first row after headers with actual product data)
        data_start_row = max(header_rows) + 1 if header_rows else 2
        
        return {
            "brands_detected": brands_detected,
            "brand_column_ranges": brand_column_ranges,
            "header_rows": header_rows,
            "data_start_row": data_start_row
        }

    def _map_brand_columns(self, df: pd.DataFrame, structure: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Map specific columns (product code, price) for each brand
        """
        column_mapping = {}
        
        for brand, range_info in structure["brand_column_ranges"].items():
            start_col = range_info["start_col"]
            end_col = range_info["end_col"]
            header_row = range_info["header_row"]
            
            # Get column headers in this brand's range
            brand_columns = []
            for col_idx in range(start_col, min(end_col + 1, len(df.columns))):
                # Look for column headers in the row after brand name
                for check_row in range(header_row + 1, min(header_row + 3, len(df))):
                    if check_row < len(df):
                        cell_value = df.iloc[check_row, col_idx]
                        if not pd.isna(cell_value):
                            brand_columns.append({
                                "column_index": col_idx,
                                "header": str(cell_value).strip(),
                                "header_row": check_row
                            })
                            break
            
            # Map columns to types
            mapping = self._identify_column_types(brand_columns)
            column_mapping[brand] = mapping
        
        return column_mapping

    def _identify_column_types(self, brand_columns: List[Dict]) -> Dict[str, Any]:
        """
        Identify which columns contain product codes vs prices
        """
        mapping = {
            "product_code_column": None,
            "price_column": None,
            "additional_columns": []
        }
        
        for col_info in brand_columns:
            header = col_info["header"].lower()
            col_idx = col_info["column_index"]
            
            # Check for product code patterns
            for pattern in self.product_code_patterns:
                if re.search(pattern, header):
                    mapping["product_code_column"] = col_idx
                    break
            
            # Check for price patterns
            for pattern in self.price_patterns:
                if re.search(pattern, header):
                    mapping["price_column"] = col_idx
                    break
            
            # Store additional columns
            if col_idx not in [mapping["product_code_column"], mapping["price_column"]]:
                mapping["additional_columns"].append({
                    "column_index": col_idx,
                    "header": col_info["header"],
                    "type": "unknown"
                })
        
        return mapping

    def _validate_structure(self, structure: Dict[str, Any]) -> bool:
        """
        Validate that the detected structure is usable
        """
        if not structure["brands_detected"]:
            return False
        
        valid_brands = 0
        for brand in structure["brands_detected"]:
            mapping = structure["column_mapping"].get(brand, {})
            if mapping.get("product_code_column") is not None and mapping.get("price_column") is not None:
                valid_brands += 1
        
        return valid_brands > 0

    def _create_fallback_structure(self) -> Dict[str, Any]:
        """
        Create a basic structure when detection fails
        """
        return {
            "layout_type": "unknown",
            "brands_detected": [],
            "brand_column_ranges": {},
            "header_rows": [],
            "data_start_row": 1,
            "column_mapping": {},
            "is_valid": False,
            "error": "Structure detection failed"
        }

    def extract_products_from_structure(self, df: pd.DataFrame, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract products using the detected structure
        """
        products = []
        
        if not structure["is_valid"]:
            logger.warning("Invalid structure detected, cannot extract products")
            return products
        
        data_start_row = structure["data_start_row"]
        
        for brand in structure["brands_detected"]:
            brand_mapping = structure["column_mapping"].get(brand, {})
            
            if not brand_mapping.get("product_code_column") or not brand_mapping.get("price_column"):
                logger.warning(f"Incomplete mapping for brand {brand}, skipping")
                continue
            
            brand_products = self._extract_brand_products(
                df, brand, brand_mapping, data_start_row
            )
            products.extend(brand_products)
        
        logger.info(f"Extracted {len(products)} products from {len(structure['brands_detected'])} brands")
        return products

    def _extract_brand_products(self, df: pd.DataFrame, brand: str, mapping: Dict[str, Any], start_row: int) -> List[Dict[str, Any]]:
        """
        Extract products for a specific brand
        """
        products = []
        code_col = mapping["product_code_column"]
        price_col = mapping["price_column"]
        
        # Extract data from start_row onwards
        for row_idx in range(start_row, len(df)):
            try:
                # Get product code
                if code_col < len(df.columns):
                    product_code = df.iloc[row_idx, code_col]
                else:
                    continue
                
                # Get price
                if price_col < len(df.columns):
                    price_raw = df.iloc[row_idx, price_col]
                else:
                    continue
                
                # Skip empty rows
                if pd.isna(product_code) or str(product_code).strip() == '':
                    continue
                
                # Clean and validate data
                code_clean = str(product_code).strip()
                price_clean = str(price_raw).strip() if not pd.isna(price_raw) else ''
                
                if code_clean and code_clean.lower() not in ['nan', 'none', '']:
                    product = {
                        "brand": brand,
                        "product_code": code_clean,
                        "raw_price": price_clean,
                        "parsed_price": self._parse_price(price_clean),
                        "row_index": row_idx,
                        "source_columns": {
                            "code_column": code_col,
                            "price_column": price_col
                        }
                    }
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error extracting row {row_idx} for brand {brand}: {str(e)}")
                continue
        
        return products

    def _parse_price(self, price_text: str) -> Optional[float]:
        """
        Parse price text to numeric value
        """
        if not price_text or price_text.upper() in ['P.O.R', 'POA', 'CALL', 'TBC', 'NAN']:
            return None
        
        # Remove currency symbols and clean
        cleaned = re.sub(r'[R$€£,\s]', '', price_text)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
