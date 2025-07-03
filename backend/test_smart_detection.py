# backend/test_smart_detection.py
import asyncio
import pandas as pd
import os
from app.services.gpt4_document_processor import GPT4DocumentProcessor
from app.services.smart_column_detector import SmartColumnDetector

async def test_nology_pricelist():
    """
    Test the enhanced GPT-4 processor with your actual Nology pricelist
    """
    print("🧪 Testing Smart Detection + GPT-4 Integration")
    print("=" * 50)
    
    # Initialize processor
    api_key = os.getenv("OPENAI_API_KEY")  # Make sure this is set
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return
    
    processor = GPT4DocumentProcessor(api_key)
    
    # Load your Nology pricelist
    pricelist_path = "path/to/Nology Pricelist July 2025.xlsx"  # Update this path
    
    try:
        print("📂 Loading Nology pricelist...")
        df = pd.read_excel(pricelist_path, header=None)
        print(f"✅ File loaded: {df.shape[0]} rows x {df.shape[1]} columns")
        
        # Test 1: Structure Analysis
        print("\n🔍 Testing Structure Analysis...")
        structure = await processor.analyze_pricelist_structure(df)
        
        print(f"Layout Type: {structure.get('layout_type', 'Unknown')}")
        print(f"Analysis Method: {structure.get('analysis_method', 'Unknown')}")
        print(f"Brands Detected: {len(structure.get('brands_detected', []))}")
        print(f"Is Valid: {structure.get('is_valid', False)}")
        
        if structure.get('brands_detected'):
            print("Brands found:", structure['brands_detected'][:10])  # Show first 10
        
        # Test 2: Product Extraction
        print("\n📦 Testing Product Extraction...")
        products = await processor.extract_products_with_gpt4(df, structure)
        
        print(f"Total Products Extracted: {len(products)}")
        
        if products:
            # Show sample products
            print("\n📋 Sample Products:")
            for i, product in enumerate(products[:5]):  # Show first 5
                print(f"{i+1}. Brand: {product.get('brand', 'N/A')}")
                print(f"   Code: {product.get('product_code', 'N/A')}")
                print(f"   Raw Price: {product.get('raw_price', 'N/A')}")
                print(f"   Parsed Price: {product.get('parsed_price', 'N/A')}")
                print(f"   Method: {product.get('extraction_method', 'N/A')}")
                print()
        
        # Test 3: Brand-specific Analysis
        print("\n🏷️ Brand-specific Analysis:")
        brand_counts = {}
        price_success = {}
        
        for product in products:
            brand = product.get('brand', 'Unknown')
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            if product.get('parsed_price') is not None:
                price_success[brand] = price_success.get(brand, 0) + 1
        
        for brand in sorted(brand_counts.keys())[:10]:  # Show top 10 brands
            success_rate = (price_success.get(brand, 0) / brand_counts[brand]) * 100
            print(f"{brand}: {brand_counts[brand]} products, {success_rate:.1f}% price success")
        
        # Test 4: Validation
        print("\n✅ Validation Results:")
        success_count = len([p for p in products if p.get('parsed_price') is not None])
        total_count = len(products)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"Overall Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
        
        if success_rate > 80:
            print("🎉 EXCELLENT: High success rate!")
        elif success_rate > 60:
            print("✅ GOOD: Acceptable success rate")
        else:
            print("⚠️ NEEDS IMPROVEMENT: Low success rate")
        
        return {
            "structure": structure,
            "products": products,
            "success_rate": success_rate
        }
        
    except FileNotFoundError:
        print(f"❌ File not found: {pricelist_path}")
        print("Please update the file path in the test script")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_smart_detection_only():
    """
    Test just the Smart Column Detector without GPT-4
    """
    print("\n🔧 Testing Smart Detection Only")
    print("=" * 30)
    
    detector = SmartColumnDetector()
    
    # Create mock Nology-style data for quick testing
    mock_data = {
        0: ['Updated - 02/07/2025', '', 'Updated - 25/06/2025', '', 'Updated - 28/04/2025'],
        1: ['YEALINK', '', 'JABRA', '', 'DNAKE'],
        2: ['Stock Code', 'Price (excl. VAT)', 'Stock Code', 'Price (excl. VAT)', 'Stock Code'],
        3: ['16WALIC', 'P.O.R', 'EVOLVE-20', '890.00', '280M-S8'],
        4: ['YEA-001', '1250.50', 'JAB-002', '1500.00', 'DNA-003'],
        5: ['YEA-003', '750.00', 'JAB-004', 'P.O.R', 'DNA-005']
    }
    
    df = pd.DataFrame(mock_data).T
    print("📊 Mock data created (Nology-style format)")
    
    # Test structure detection
    structure = detector.detect_horizontal_structure(df)
    
    print(f"Layout Type: {structure.get('layout_type')}")
    print(f"Brands Found: {structure.get('brands_detected')}")
    print(f"Is Valid: {structure.get('is_valid')}")
    
    # Test product extraction
    if structure.get('is_valid'):
        products = detector.extract_products_from_structure(df, structure)
        print(f"Products Extracted: {len(products)}")
        
        for product in products:
            print(f"- {product.get('brand')}: {product.get('product_code')} = {product.get('parsed_price')}")
    
    return structure

if __name__ == "__main__":
    print("🚀 Starting Smart Detection Tests\n")
    
    # Test 1: Smart Detection Only (quick test)
    asyncio.run(test_smart_detection_only())
    
    # Test 2: Full Integration Test (requires actual file)
    print("\n" + "="*60)
    asyncio.run(test_nology_pricelist())
