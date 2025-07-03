# backend/app/services/gpt4_document_processor.py
import openai
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import the new Smart Column Detector
from app.services.smart_column_detector import SmartColumnDetector

logger = logging.getLogger(__name__)

class GPT4DocumentProcessor:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        # Add Smart Column Detector while keeping existing functionality
        self.column_detector = SmartColumnDetector()
        
    async def analyze_pricelist_structure(self, file_data: Any) -> Dict[str, Any]:
        """
        Enhanced analysis combining Smart Detection + GPT-4 (preserves existing logic)
        """
        try:
            # NEW: Try smart detection first for horizontal layouts
            if isinstance(file_data, pd.DataFrame):
                logger.info("Attempting smart column detection for horizontal layout...")
                smart_structure = self.column_detector.detect_horizontal_structure(file_data)
                
                if smart_structure.get("is_valid", False) and len(smart_structure.get("brands_detected", [])) > 0:
                    logger.info(f"Smart detection successful! Found {len(smart_structure['brands_detected'])} brands")
                    # Enhance with GPT-4 insights while keeping smart structure
                    enhanced_structure = await self._enhance_smart_structure_with_gpt4(file_data, smart_structure)
                    return enhanced_structure
                else:
                    logger.info("Smart detection didn't find valid structure, using GPT-4 analysis")
            
            # EXISTING: Fallback to your original GPT-4 analysis
            return await self._original_gpt4_structure_analysis(file_data)
            
        except Exception as e:
            logger.error(f"Combined analysis failed: {str(e)}")
            return self._fallback_analysis(file_data)

    async def _enhance_smart_structure_with_gpt4(self, file_data: pd.DataFrame, smart_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        NEW: Enhance smart detection results with GPT-4 insights
        """
        try:
            # Get sample data for GPT-4 validation
            if isinstance(file_data, pd.DataFrame):
                sample_data = file_data.head(10).to_string()
                column_info = f"Columns: {list(file_data.columns)}"
            else:
                sample_data = str(file_data)[:2000]
                column_info = "Raw data format"
            
            # Create enhanced structure combining both approaches
            enhanced_structure = smart_structure.copy()
            
            prompt = f"""
            Validate and enhance this pricelist structure analysis:

            DETECTED STRUCTURE:
            - Layout: {smart_structure.get('layout_type', 'unknown')}
            - Brands Found: {smart_structure.get('brands_detected', [])}
            - Valid Structure: {smart_structure.get('is_valid', False)}

            SAMPLE DATA:
            {sample_data}

            Please provide JSON response with:
            1. "validation": "confirmed" or "needs_adjustment" 
            2. "price_format_insights": analysis of price formats found
            3. "extraction_recommendations": specific tips for this data
            4. "quality_score": 1-10 for extraction confidence
            5. "potential_issues": any problems you foresee

            Focus on validating the smart detection results and providing extraction guidance.
            Respond only with valid JSON.
            """
            
            response = await self.client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert data analyst validating automated pricelist analysis. Provide accurate, structured responses in JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            gpt4_insights = json.loads(response.choices[0].message.content)
            
            # Merge smart detection with GPT-4 insights
            enhanced_structure.update({
                "analysis_method": "smart_detection_enhanced_by_gpt4",
                "gpt4_validation": gpt4_insights.get("validation", "unknown"),
                "price_format_insights": gpt4_insights.get("price_format_insights", ""),
                "extraction_recommendations": gpt4_insights.get("extraction_recommendations", ""),
                "quality_score": gpt4_insights.get("quality_score", 5),
                "potential_issues": gpt4_insights.get("potential_issues", [])
            })
            
            logger.info(f"Enhanced structure with GPT-4 validation: {gpt4_insights.get('validation', 'unknown')}")
            return enhanced_structure
            
        except Exception as e:
            logger.error(f"GPT-4 enhancement failed: {str(e)}, using smart detection only")
            smart_structure["analysis_method"] = "smart_detection_only"
            return smart_structure

    async def _original_gpt4_structure_analysis(self, file_data: Any) -> Dict[str, Any]:
        """
        EXISTING: Your original GPT-4 analysis method (preserved exactly)
        """
        try:
            # Convert file data to analyzable format
            if isinstance(file_data, pd.DataFrame):
                # Get first 10 rows for structure analysis
                sample_data = file_data.head(10).to_string()
                column_info = f"Columns: {list(file_data.columns)}"
            else:
                sample_data = str(file_data)[:2000]  # First 2000 chars
                column_info = "Raw data format"
            
            prompt = f"""
            Analyze this pricelist data structure and extract the following information:

            COLUMN INFO: {column_info}
            
            SAMPLE DATA:
            {sample_data}

            Please provide a JSON response with:
            1. "layout_type": "horizontal_multi_brand" or "vertical_single_brand" or "multi_sheet"
            2. "brands_detected": list of brand names found
            3. "column_mapping": for each brand, what columns contain product codes and prices
            4. "data_start_row": which row the actual product data starts
            5. "price_format": how prices are formatted (currency, tax inclusion, etc.)
            6. "extraction_strategy": recommended approach for processing this file

            Focus on identifying:
            - Brand names in headers (YEALINK, JABRA, DNAKE, etc.)
            - Product code columns (Stock Code, Item Code, etc.)
            - Price columns (Price excl. VAT, MSRP, etc.)
            - Any special formatting or patterns

            Respond only with valid JSON.
            """
            
            response = await self.client.chat.completions.acreate(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert data analyst specializing in pricelist and product catalog analysis. Provide accurate, structured responses in JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            result = json.loads(response.choices[0].message.content)
            result["analysis_method"] = "gpt4_original"
            logger.info(f"Original GPT-4 analysis completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Original GPT-4 analysis failed: {str(e)}")
            return self._fallback_analysis(file_data)

    async def extract_products_with_gpt4(self, file_data: pd.DataFrame, structure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enhanced extraction using Smart Detection + GPT-4 (preserves existing logic)
        """
        try:
            analysis_method = structure_analysis.get("analysis_method", "unknown")
            
            # NEW: Smart detection path
            if analysis_method in ["smart_detection_enhanced_by_gpt4", "smart_detection_only"]:
                logger.info("Using smart detection extraction method")
                products = await self._extract_with_smart_detection(file_data, structure_analysis)
                
                # Enhance with GPT-4 price parsing for failed cases
                enhanced_products = []
                failed_count = 0
                
                for product in products:
                    if product.get("parsed_price") is None and product.get("raw_price"):
                        # Use GPT-4 for complex price parsing
                        parsed_price = await self._parse_price_with_gpt4(product["raw_price"])
                        product["parsed_price"] = parsed_price
                        if parsed_price is None:
                            failed_count += 1
                    
                    enhanced_products.append(product)
                
                logger.info(f"Smart detection extracted {len(enhanced_products)} products, {failed_count} price parsing failures")
                return enhanced_products
            
            # EXISTING: Original GPT-4 extraction paths
            elif structure_analysis.get("layout_type") == "horizontal_multi_brand":
                return await self._extract_horizontal_layout(file_data, structure_analysis)
            elif structure_analysis.get("layout_type") == "vertical_single_brand":
                return await self._extract_vertical_layout(file_data, structure_analysis)
            else:
                return await self._extract_multi_sheet_layout(file_data, structure_analysis)
                
        except Exception as e:
            logger.error(f"Enhanced extraction failed: {str(e)}")
            return []

    async def _extract_with_smart_detection(self, df: pd.DataFrame, structure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        NEW: Extract products using smart column detection
        """
        try:
            products = self.column_detector.extract_products_from_structure(df, structure_analysis)
            
            # Add metadata to each product
            for product in products:
                product.update({
                    "currency": "ZAR",  # South African Rands
                    "price_excl_vat": True,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "smart_detection"
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Smart detection extraction failed: {str(e)}")
            return []

    # EXISTING METHODS (preserved exactly as they were)
    async def _extract_horizontal_layout(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        EXISTING: Extract products from horizontal multi-brand layout (preserved)
        """
        products = []
        brands = analysis["brands_detected"]
        column_mapping = analysis["column_mapping"]
        data_start_row = analysis.get("data_start_row", 2)
        
        # Process each brand section
        for brand in brands:
            if brand in column_mapping:
                brand_mapping = column_mapping[brand]
                code_col = brand_mapping.get("product_code_column")
                price_col = brand_mapping.get("price_column")
                
                if code_col and price_col:
                    # Extract products for this brand
                    brand_products = await self._extract_brand_products(
                        df, brand, code_col, price_col, data_start_row
                    )
                    products.extend(brand_products)
        
        return products
    
    async def _extract_vertical_layout(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        EXISTING: Extract products from vertical single-brand layout (preserved)
        """
        # Your existing vertical extraction logic here
        products = []
        # Add your existing implementation
        return products
    
    async def _extract_multi_sheet_layout(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        EXISTING: Extract products from multi-sheet layout (preserved)
        """
        # Your existing multi-sheet extraction logic here
        products = []
        # Add your existing implementation
        return products
    
    async def _extract_brand_products(self, df: pd.DataFrame, brand: str, code_col: str, price_col: str, start_row: int) -> List[Dict[str, Any]]:
        """
        EXISTING: Extract products for a specific brand (preserved)
        """
        products = []
        
        try:
            # Get the relevant data slice
            if code_col in df.columns and price_col in df.columns:
                brand_data = df[[code_col, price_col]].iloc[start_row:]
                
                for _, row in brand_data.iterrows():
                    code = str(row[code_col]).strip()
                    price = str(row[price_col]).strip()
                    
                    # Skip empty rows
                    if pd.isna(row[code_col]) or code == '' or code.lower() == 'nan':
                        continue
                    
                    # Parse price
                    parsed_price = await self._parse_price_with_gpt4(price)
                    
                    product = {
                        "brand": brand,
                        "product_code": code,
                        "raw_price": price,
                        "parsed_price": parsed_price,
                        "currency": "ZAR",  # South African Rands
                        "price_excl_vat": True,
                        "extracted_at": datetime.now().isoformat(),
                        "extraction_method": "gpt4_original"
                    }
                    
                    products.append(product)
            
        except Exception as e:
            logger.error(f"Error extracting products for brand {brand}: {str(e)}")
        
        return products
    
    async def _parse_price_with_gpt4(self, price_text: str) -> Optional[float]:
        """
        EXISTING: Use GPT-4 to parse complex price formats (preserved)
        """
        try:
            prompt = f"""
            Parse this price text and return only the numeric value as a float:
            "{price_text}"
            
            Rules:
            - If it says "P.O.R" or "POA" or similar, return null
            - Remove currency symbols, commas, spaces
            - Handle decimal points correctly
            - Return only the number or null
            
            Examples:
            "R1,250.00" -> 1250.00
            "890" -> 890.00
            "P.O.R" -> null
            "1029.50" -> 1029.50
            
            Response: (number only or null)
            """
            
            response = await self.client.chat.completions.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip()
            
            if result.lower() in ['null', 'none', '']:
                return None
            
            return float(result)
            
        except Exception as e:
            logger.error(f"Error parsing price '{price_text}': {str(e)}")
            return None
    
    def _fallback_analysis(self, file_data: Any) -> Dict[str, Any]:
        """
        EXISTING: Fallback analysis when GPT-4 fails (preserved)
        """
        return {
            "layout_type": "unknown",
            "brands_detected": [],
            "column_mapping": {},
            "data_start_row": 1,
            "price_format": "unknown",
            "extraction_strategy": "manual_review_required",
            "analysis_method": "fallback"
        }