# diagnostic_tool.py - Check what's actually in your database
import mysql.connector
from mysql.connector import Error

def check_denon_products():
    """Check what Denon products exist in database"""
    config = {
        'host': 'dedi159.cpt4.host-h.net',
        'database': 'audicdmyde_db__359',
        'user': 'audicdmyde_314',
        'password': '4hG4xcGS3tSgX76o5FSv',
        'port': 3306,
        'charset': 'utf8mb4'
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor(dictionary=True)
        
        print("🔍 STEP 1: Finding ALL Denon products...")
        cursor.execute("""
            SELECT p.product_id, pd.name, p.model, p.price, p.quantity, p.status
            FROM oc_product p
            JOIN oc_product_description pd ON p.product_id = pd.product_id
            WHERE (pd.name LIKE '%denon%' OR pd.name LIKE '%Denon%')
            AND pd.language_id = 1
            ORDER BY pd.name
        """)
        
        all_denon = cursor.fetchall()
        print(f"Found {len(all_denon)} Denon products total:")
        for product in all_denon:
            status = "✅ Active" if product['status'] == 1 else "❌ Inactive"
            stock = f"Stock: {product['quantity']}" if product['quantity'] > 0 else "⚠️ Out of Stock"
            print(f"  ID: {product['product_id']} | {product['name'][:60]}... | {status} | {stock}")
        
        print("\n🎯 STEP 2: Looking specifically for AVR-X1800H...")
        cursor.execute("""
            SELECT p.product_id, pd.name, p.model, p.price, p.quantity, p.status
            FROM oc_product p
            JOIN oc_product_description pd ON p.product_id = pd.product_id
            WHERE (pd.name LIKE '%1800%' OR p.model LIKE '%1800%')
            AND pd.language_id = 1
        """)
        
        avr_products = cursor.fetchall()
        print(f"Found {len(avr_products)} products with '1800':")
        for product in avr_products:
            status = "✅ Active" if product['status'] == 1 else "❌ Inactive"
            stock = f"Stock: {product['quantity']}" if product['quantity'] > 0 else "⚠️ Out of Stock"
            print(f"  ID: {product['product_id']} | {product['name']} | Model: {product['model']} | {status} | {stock}")
        
        print("\n💰 STEP 3: Checking special pricing for product ID 7892...")
        cursor.execute("""
            SELECT ps.price as special_price, ps.customer_group_id, ps.date_start, ps.date_end
            FROM oc_product_special ps
            WHERE ps.product_id = 7892
        """)
        
        special_prices = cursor.fetchall()
        if special_prices:
            print(f"Found {len(special_prices)} special prices:")
            for sp in special_prices:
                print(f"  Special: R{sp['special_price']} | Group: {sp['customer_group_id']} | Start: {sp['date_start']} | End: {sp['date_end']}")
        else:
            print("❌ No special prices found for product 7892")
        
        print("\n🔍 STEP 4: Testing search with different terms...")
        search_terms = ['denon avr-x1800h', 'denon avrx1800h', 'avr-x1800h', '1800h']
        for term in search_terms:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM oc_product p
                JOIN oc_product_description pd ON p.product_id = pd.product_id
                WHERE (pd.name LIKE %s OR pd.description LIKE %s OR p.model LIKE %s)
                AND pd.language_id = 1 AND p.status = 1
            """, (f"%{term}%", f"%{term}%", f"%{term}%"))
            
            result = cursor.fetchone()
            print(f"  Search '{term}': {result['count']} results")
        
        connection.close()
        print("\n✅ Diagnostic complete!")
        
    except Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_denon_products()