import mysql.connector
from mysql.connector import Error
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

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

    def search_products(self, query: str, category: str = None, limit: int = 50) -> List[Dict]:
        """Search products in OpenCart database"""
        if not self.connect():
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Build search query for OpenCart product table
            search_sql = """
            SELECT 
                p.product_id,
                pd.name,
                pd.description,
                p.model,
                p.price,
                p.quantity,
                p.status,
                cd.name as category_name,
                p.image
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            LEFT JOIN oc_product_to_category ptc ON p.product_id = ptc.product_id
            LEFT JOIN oc_category_description cd ON ptc.category_id = cd.category_id
            WHERE pd.language_id = 1 AND cd.language_id = 1
            AND (pd.name LIKE %s OR pd.description LIKE %s OR p.model LIKE %s)
            """
            
            params = [f"%{query}%", f"%{query}%", f"%{query}%"]
            
            if category:
                search_sql += " AND cd.name LIKE %s"
                params.append(f"%{category}%")
            
            search_sql += f" AND p.status = 1 LIMIT {limit}"
            
            cursor.execute(search_sql, params)
            products = cursor.fetchall()
            
            # Convert prices to South African Rands (assuming prices are in USD)
            for product in products:
                if product['price']:
                    # Convert USD to ZAR (approximate rate: 1 USD = 18.5 ZAR)
                    product['price_zar'] = round(float(product['price']) * 18.5, 2)
                    product['price_formatted'] = f"R{product['price_zar']:,.2f}"
                
            return products
            
        except Error as e:
            logger.error(f"Error searching products: {e}")
            return []
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
            WHERE cd.language_id = 1 AND p.status = 1
            GROUP BY cd.category_id, cd.name
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
        """Get AI-powered product recommendations based on category and requirements"""
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
        
        # Search for products matching category
        all_recommendations = []
        for term in search_terms[:3]:  # Limit to first 3 terms to avoid too many results
            products = self.search_products(term, limit=10)
            all_recommendations.extend(products)
        
        # Remove duplicates and limit results
        seen_ids = set()
        unique_recommendations = []
        for product in all_recommendations:
            if product['product_id'] not in seen_ids:
                seen_ids.add(product['product_id'])
                unique_recommendations.append(product)
                if len(unique_recommendations) >= 15:  # Limit to 15 recommendations
                    break
        
        return unique_recommendations

# Global instance
sqlantern_db = SQLanternDB()
