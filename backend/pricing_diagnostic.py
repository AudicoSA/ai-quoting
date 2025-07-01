# pricing_diagnostic.py - Immediate Diagnostic Tool
import mysql.connector
from mysql.connector import Error

def test_denon_pricing():
    """Test exact Denon AVR-X1800H pricing to identify issue"""
    
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
        
        # DIAGNOSTIC QUERY 1: Find the exact Denon product
        print("🔍 STEP 1: Finding Denon AVR-X1800H in database...")
        cursor.execute("""
            SELECT p.product_id, pd.name, p.model, p.price
            FROM oc_product p
            JOIN oc_product_description pd ON p.product_id = pd.product_id
            WHERE (pd.name LIKE '%1800%' OR p.model LIKE '%1800%')
            AND (pd.name LIKE '%denon%' OR pd.name LIKE '%avr%')
            AND pd.language_id = 1
        """)
        
        products = cursor.fetchall()
        print(f"Found {len(products)} matching products:")
        for p in products:
            print(f"  ID: {p['product_id']} | Name: {p['name']} | Model: {p['model']} | Price: R{p['price']}")
        
        if not products:
            print("❌ NO DENON AVR-X1800H FOUND!")
            return
        
        # Use the first match
        target_product = products[0]
        product_id = target_product['product_id']
        
        print(f"\n🎯 TESTING PRODUCT ID: {product_id}")
        print(f"   Name: {target_product['name']}")
        print(f"   Regular Price: R{target_product['price']}")
        
        # DIAGNOSTIC QUERY 2: Check for special prices
        print(f"\n🔍 STEP 2: Checking special prices for product {product_id}...")
        cursor.execute("""
            SELECT 
                ps.price as special_price,
                ps.date_start,
                ps.date_end,
                ps.customer_group_id,
                ps.priority
            FROM oc_product_special ps
            WHERE ps.product_id = %s
            ORDER BY ps.priority ASC, ps.date_start DESC
        """, (product_id,))
        
        special_prices = cursor.fetchall()
        print(f"Found {len(special_prices)} special price records:")
        
        for sp in special_prices:
            print(f"  Special Price: R{sp['special_price']}")
            print(f"  Date Range: {sp['date_start']} to {sp['date_end']}")
            print(f"  Customer Group: {sp['customer_group_id']}")
            print(f"  Priority: {sp['priority']}")
            print("  ---")
        
        # DIAGNOSTIC QUERY 3: Test your current query logic
        print(f"\n🔍 STEP 3: Testing current query logic...")
        cursor.execute("""
            SELECT 
                p.product_id,
                pd.name,
                p.model,
                p.price as regular_price,
                ps.price as special_price,
                ps.date_start,
                ps.date_end
            FROM oc_product p
            LEFT JOIN oc_product_description pd ON p.product_id = pd.product_id
            LEFT JOIN oc_product_special ps ON p.product_id = ps.product_id
            WHERE p.product_id = %s AND pd.language_id = 1
        """, (product_id,))
        
        current_result = cursor.fetchall()
        print(f"Current query returns {len(current_result)} rows:")
        
        for cr in current_result:
            regular = float(cr['regular_price'])
            special = cr['special_price']
            
            if special and float(special) > 0:
                special_val = float(special)
                print(f"  Regular: R{regular} | Special: R{special_val}")
                
                if special_val < regular:
                    print(f"  ✅ SHOULD USE SPECIAL: R{special_val} (Save R{regular - special_val})")
                    if special_val == 15990.00:
                        print(f"  🎉 CORRECT! Found R15,990 special price!")
                    else:
                        print(f"  ⚠️  Special price is R{special_val}, expected R15,990")
                else:
                    print(f"  ⚠️  Special price R{special_val} not less than regular R{regular}")
            else:
                print(f"  Regular: R{regular} | No special price")
                print(f"  ❌ PROBLEM: No valid special price found!")
        
        # DIAGNOSTIC QUERY 4: Check customer groups
        print(f"\n🔍 STEP 4: Checking customer groups...")
        cursor.execute("SELECT * FROM oc_customer_group")
        groups = cursor.fetchall()
        print("Available customer groups:")
        for g in groups:
            print(f"  ID: {g['customer_group_id']} | Name: {g.get('name', 'N/A')}")
        
        connection.close()
        
        print(f"\n🔍 DIAGNOSIS COMPLETE!")
        print(f"Next steps:")
        print(f"1. If special price found: Update JOIN condition in sqlantern.py")
        print(f"2. If no special price: Check database for special pricing data")
        print(f"3. If wrong special price: Update special price in database")
        
    except Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    test_denon_pricing()
