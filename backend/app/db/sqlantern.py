import mysql.connector
from mysql.connector import Error
import hashlib
import re
from typing import List, Dict, Optional
import logging
from datetime import datetime
import difflib

logger = logging.getLogger(__name__)

class ProductMatcher:
    """Smart product deduplication and flexible search"""
    
    @staticmethod
    def normalize_search_term(term: str) -> str:
        """Normalize search terms for flexible matching"""
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', term.lower())
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    @staticmethod
    def create_search_variants(query: str) -> List[str]:
        """Create search variants for flexible matching"""
        variants = [query]
        
        # Original query
        variants.append(query)
        
        # Normalized version
        normalized = ProductMatcher.normalize_search_term(query)
        variants.append(normalized)
        
        # Add/remove dashes and spaces
        with_dashes = re.sub(r'\s+', '-', normalized)
        without_dashes = re.sub(r'[-\s]+', '', normalized)
        with_spaces = re.sub(r'[-_]', ' ', normalized)
        
        variants.extend([with_dashes, without_dashes, with_spaces])
        
        # Model number specific variants
        if 'avr' in normalized:
            # Handle AVR-X1800H vs AVRX1800H variations
            avr_with_dash = re.sub(r'avr\s*x(\d+)', r'avr-x\1', normalized)
            avr_without_dash = re.sub(r'avr-x(\d+)', r'avrx\1', normalized)
            variants.extend([avr_with_dash, avr_without_dash])
        
        # Remove duplicates while preserving order
        unique_variants = []
        for variant in variants:
            if variant and variant not in unique_variants:
                unique_variants.append(variant)
        
        return unique_variants
    
    @staticmethod
    def generate_product_fingerprint(product: Dict) -> str:
        """Generate unique fingerprint for deduplication"""
        model = ProductMatcher.normalize_search_term(product.get('model', ''))
        name = ProductMatcher.normalize_search_term(product.get('name', ''))
        
        # Extract brand
        brand = product.get('manufacturer', '').lower()
        if not brand:
            known_brands = ['denon', 'yamaha', 'marantz', 'onkyo', 'pioneer', 'sony', 'bose', 'jbl', 'polk']
            for b in known_brands:
                if b in name:
                    brand = b
                    break
        
        # Create fingerprint
        fingerprint_data = f"{brand}_{model}"
        fingerprint_data = re.sub(r'[^a-zA-Z0-9_]', '', fingerprint_data.lower())
        
        return hashlib.md5(fingerprint_data.encode()).hexdigest()[:12]
    
    @staticmethod
    def deduplicate_products(products: List[Dict]) -> List[Dict]:
        """Smart deduplication while preserving category info"""
        unique_products = {}
        
        for product in products:
            fingerprint = ProductMatcher.generate_product_fingerprint(product)
            
            if fingerprint not in unique_products:
                product['all_categories'] = [product.get('category_name', 'Uncategorized')]
                unique_products[fingerprint] = product
            else:
                existing = unique_products[fingerprint]
                current_category = product.get('category_name', 'Uncategorized')
                
                if current_category not in existing['all_categories']:
                    existing['all_categories'].append(current_category)
                
                # Keep product with better pricing (special price preferred)
                current_special = product.get('special_price')
                existing_special = existing.get('special_price')
                
                # Prefer product with special pricing, or better stock status
                should_replace = False
                
                if current_special and not existing_special:
                    should_replace = True
                elif current_special and existing_special and float(current_special) < float(existing_special):
                    should_replace = True
                elif not current_special and not existing_special:
                    # Compare regular prices and stock
                    current_price = float(product.get('price', 0))
                    existing_price = float(existing.get('price', 0))
                    current_stock = product.get('quantity', 0)
                    existing_stock = existing.get('quantity', 0)
                    
                    if current_stock > 0 and existing_stock <= 0:
                        should_replace = True
                    elif current_stock > 0 and existing_stock > 0 and current_price < existing_price:
                        should_replace = True
                
                if should_replace:
                    categories = existing['all_categories'].copy()
                    product['all_categories'] = categories
                    if current_category not in categories:
                        product['all_categories'].append(current_category)
                    unique_products[fingerprint] = product
        
        # Add category display info
        result = []
        for product in unique_products.values():
            product['category_count'] = len(product['all_categories'])
            product['categories_display'] = ', '.join(product['all_categories'][:3])
            if len(product['all_categories']) > 3:
                product['categories_display'] += f' +{len(product["all_categories"]) - 3} more'
            result.append(product)
        
        return result

class SQLanternDB:
    def __init__(self):
        self.config = {
            'host': 'dedi159.cpt4.host-h.net',
            'database': 'audicdmyde_db__359',
            'user': 'audicdmyde_314',
            'password': '4hG4xcGS3tSgX76o5FSv',
            'port': 3306,
            'charset': 'utf8mb4',
            'autocommit': True
        }
        self.connection = None

    def connect(self):
        """Establish connection to SQLantern database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info("Successfully connected to SQLantern database")
                return True
        except Error as e:
            logger.error(f"Error connecting to SQLantern database: {e}")
            return False
        return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("SQLantern database connection closed")

    def search_products(self, query: str, category: str = None, limit: int = 50, include_out_of_stock: bool = False) -> List[Dict]:
        """Enhanced search with flexible matching and FIXED special pricing"""
        if not self.connect():
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Create search variants for flexible matching
            search_variants = ProductMatcher.create_search_variants(query)
            
            # Build dynamic search conditions
            search_conditions = []
            search_params = []
            
            for variant in search_variants:
                search_conditions.append("(pd.name LIKE %s OR pd.description LIKE %s OR p.model LIKE %s OR m.name LIKE %s)")
                search_params.extend([f"%{variant}%", f"%{variant}%", f"%{variant}%", f"%{variant}%"])
            
            search_condition = " OR ".join(search_conditions)
            
            # 🔥 FIXED QUERY - CUSTOMER GROUP 8 INCLUDED FOR SPECIAL PRICING
            search_sql = f"""
            SELECT 
                p.product_id,
                pd.name,
                pd.description,
                p.model,
                p.price,
                ps.price as special_price,
                p.quantity,
                p.status,
                cd.name as category_name,
                p.image,
                m.name as manufacturer,
                ps.date_start as special_start,
                ps.date_end as special_end,
                ps.customer_group_id
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            LEFT JOIN oc_product_to_category ptc ON p.product_id = ptc.product_id
            LEFT JOIN oc_category_description cd ON ptc.category_id = cd.category_id
            LEFT JOIN oc_manufacturer m ON p.manufacturer_id = m.manufacturer_id
            LEFT JOIN oc_product_special ps ON p.product_id = ps.product_id 
                AND (ps.customer_group_id = 8 OR ps.customer_group_id = 1)
                AND (ps.date_start IS NULL OR ps.date_start <= CURDATE()) 
                AND (ps.date_end IS NULL OR ps.date_end >= CURDATE())
            WHERE pd.language_id = 1 AND cd.language_id = 1
            AND ({search_condition})
            """
            
            if category:
                search_sql += " AND cd.name LIKE %s"
                search_params.append(f"%{category}%")
            
            # Filter out discontinued/out of stock unless specifically requested
            if not include_out_of_stock:
                search_sql += " AND p.status = 1 AND p.quantity > 0"
            else:
                search_sql += " AND p.status = 1"
            
            search_sql += f" ORDER BY ps.price ASC, p.quantity DESC, pd.name LIMIT {limit * 3}"  # Get more for deduplication
            
            cursor.execute(search_sql, search_params)
            raw_products = cursor.fetchall()
            
            # 🔥 CORRECTED PRICING LOGIC - NOW SHOWS R15,990 FOR CUSTOMER GROUP 8
            for product in raw_products:
                regular_price = float(product.get('price', 0))
                special_price = product.get('special_price')
                
                # Debug logging for Denon specifically
                if 'denon' in product.get('name', '').lower() and ('1800' in product.get('name', '') or 'x1800h' in product.get('model', '').lower()):
                    logger.info(f"🎯 DENON FOUND: {product['name'][:50]}...")
                    logger.info(f"   Regular Price: R{regular_price}")
                    logger.info(f"   Special Price: {special_price}")
                    logger.info(f"   Customer Group: {product.get('customer_group_id')}")
                
                # Check if special price exists and is valid
                if special_price and float(special_price) > 0 and float(special_price) < regular_price:
                    # 🎉 USE SPECIAL PRICE - THIS SHOWS R15,990!
                    final_price = float(special_price)
                    product['has_special_price'] = True
                    product['original_price'] = regular_price
                    product['savings'] = regular_price - final_price
                    
                    if 'denon' in product.get('name', '').lower() and '1800' in product.get('name', ''):
                        logger.info(f"   ✅ USING SPECIAL PRICE: R{final_price} (Save R{product['savings']})")
                else:
                    # Use regular price
                    final_price = regular_price
                    product['has_special_price'] = False
                    product['original_price'] = final_price
                    product['savings'] = 0
                    
                    if 'denon' in product.get('name', '').lower() and '1800' in product.get('name', ''):
                        logger.info(f"   ⚠️  Using regular price: R{final_price}")
                
                # Store pricing information
                product['price_zar'] = final_price
                product['price_formatted'] = f"R{final_price:,.2f}" if final_price > 0 else "R0.00"
                
                if product['has_special_price'] and product['original_price'] > 0:
                    product['original_price_formatted'] = f"R{product['original_price']:,.2f}"
                    product['savings_formatted'] = f"R{product['savings']:,.2f}"
            
            # Apply deduplication
            unique_products = ProductMatcher.deduplicate_products(raw_products)
            
            # Sort by availability, then special prices, then regular price
            sorted_products = sorted(unique_products, key=lambda x: (
                0 if x['quantity'] > 0 else 1,  # In stock first
                0 if x.get('has_special_price') else 1,  # Special prices first
                x['price_zar'] if x['price_zar'] > 0 else float('inf')  # Lower prices first
            ))[:limit]
            
            logger.info(f"Search '{query}' returned {len(sorted_products)} unique products (was {len(raw_products)} before deduplication)")
            
            # 🎯 LOG DENON RESULTS FOR DEBUGGING
            denon_results = [p for p in sorted_products if 'denon' in p.get('name', '').lower() and '1800' in p.get('name', '')]
            if denon_results:
                logger.info(f"🎯 DENON AVR-X1800H RESULTS: {len(denon_results)} found")
                for dr in denon_results:
                    logger.info(f"   {dr['name'][:50]}... - {dr['price_formatted']} (Special: {dr.get('has_special_price')})")
            
            return sorted_products
            
        except Error as e:
            logger.error(f"Error searching products: {e}")
            return []
        finally:
            self.disconnect()

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Get product by ID with FIXED special pricing for add to quote"""
        if not self.connect():
            return None

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # 🔥 FIXED QUERY - SAME CUSTOMER GROUP LOGIC AS SEARCH
            product_sql = """
            SELECT 
                p.product_id,
                pd.name,
                pd.description,
                p.model,
                p.price,
                ps.price as special_price,
                p.quantity,
                p.status,
                m.name as manufacturer,
                ps.customer_group_id
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            LEFT JOIN oc_manufacturer m ON p.manufacturer_id = m.manufacturer_id
            LEFT JOIN oc_product_special ps ON p.product_id = ps.product_id
                AND (ps.customer_group_id = 8 OR ps.customer_group_id = 1)
                AND (ps.date_start IS NULL OR ps.date_start <= CURDATE()) 
                AND (ps.date_end IS NULL OR ps.date_end >= CURDATE())
            WHERE p.product_id = %s AND pd.language_id = 1
            ORDER BY ps.priority ASC
            LIMIT 1
            """
            
            cursor.execute(product_sql, (product_id,))
            product = cursor.fetchone()
            
            if product:
                # Apply same pricing logic as search_products
                regular_price = float(product.get('price', 0))
                special_price = product.get('special_price')
                
                logger.info(f"🔍 GET_PRODUCT_BY_ID {product_id}: {product['name'][:30]}...")
                logger.info(f"   Regular: R{regular_price}, Special: {special_price}")
                
                if special_price and float(special_price) > 0 and float(special_price) < regular_price:
                    final_price = float(special_price)
                    product['has_special_price'] = True
                    product['original_price'] = regular_price
                    product['savings'] = regular_price - final_price
                    logger.info(f"   ✅ USING SPECIAL: R{final_price}")
                else:
                    final_price = regular_price
                    product['has_special_price'] = False
                    product['original_price'] = final_price
                    product['savings'] = 0
                    logger.info(f"   Using regular: R{final_price}")
                
                product['price_zar'] = final_price
                product['price_formatted'] = f"R{final_price:,.2f}" if final_price > 0 else "R0.00"
                
                if product['has_special_price']:
                    product['original_price_formatted'] = f"R{product['original_price']:,.2f}"
                    product['savings_formatted'] = f"R{product['savings']:,.2f}"
            
            return product
            
        except Error as e:
            logger.error(f"Error getting product by ID: {e}")
            return None
        finally:
            self.disconnect()

    def get_categories(self) -> List[Dict]:
        """Get all product categories"""
        if not self.connect():
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            categories_sql = """
            SELECT DISTINCT cd.category_id, cd.name, COUNT(ptc.product_id) as product_count
            FROM oc_category_description cd
            LEFT JOIN oc_product_to_category ptc ON cd.category_id = ptc.category_id
            LEFT JOIN oc_product p ON ptc.product_id = p.product_id
            WHERE cd.language_id = 1 AND p.status = 1 AND p.quantity > 0
            GROUP BY cd.category_id, cd.name
            HAVING product_count > 0
            ORDER BY cd.name
            """
            
            cursor.execute(categories_sql)
            return cursor.fetchall()
            
        except Error as e:
            logger.error(f"Error getting categories: {e}")
            return []
        finally:
            self.disconnect()

    def get_product_recommendations(self, category_type: str, requirements: str) -> List[Dict]:
        """Get product recommendations - will be enhanced with AI training later"""
        category_mapping = {
            'restaurants': ['Audio', 'Speakers', 'Amplifier', 'Commercial', 'Zone'],
            'home': ['Home', 'Hi-Fi', 'Stereo', 'Theater', 'Bookshelf'],
            'office': ['Commercial', 'PA', 'Conference', 'Ceiling', 'Paging'],
            'gym': ['Commercial', 'High Power', 'Fitness', 'Zone', 'Background'],
            'worship': ['Pro Audio', 'Line Array', 'Mixer', 'Wireless', 'Microphone'],
            'schools': ['PA System', 'Classroom', 'Horn', 'Educational', 'Safety'],
            'educational': ['Lecture', 'University', 'Conference', 'Recording', 'Distribution'],
            'tenders': ['Professional', 'Commercial', 'Installation', 'System', 'Integration']
        }
        
        search_terms = category_mapping.get(category_type, ['Audio', 'Equipment'])
        
        all_recommendations = []
        for term in search_terms[:3]:
            products = self.search_products(term, limit=5, include_out_of_stock=False)
            all_recommendations.extend(products)
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_recommendations = []
        for product in all_recommendations:
            if product['product_id'] not in seen_ids:
                seen_ids.add(product['product_id'])
                unique_recommendations.append(product)
                if len(unique_recommendations) >= 10:
                    break
        
        return unique_recommendations

# Global instance
sqlantern_db = SQLanternDB()