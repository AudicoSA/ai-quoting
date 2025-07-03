# backend/tests/test_nology_pricelist.py
import pytest
import pandas as pd
from app.services.smart_column_detector import SmartColumnDetector

def test_nology_pricelist_detection():
    """Test detection with actual Nology pricelist structure"""
    # Create mock data matching Nology format
    mock_data = {
        0: ['Updated - 02/07/2025', '', 'Updated - 25/06/2025', ''],
        1: ['YEALINK', '', 'JABRA', ''],
        2: ['Stock Code', 'Price (excl. VAT)', 'Stock Code', 'Price (excl. VAT)'],
        3: ['16WALIC', 'P.O.R', 'EVOLVE-20', '890'],
        4: ['280M-S8', '1029.00', '4999-823-109', '1250.50']
    }
    
    df = pd.DataFrame(mock_data).T
    detector = SmartColumnDetector()
    
    structure = detector.detect_horizontal_structure(df)
    
    assert structure["layout_type"] == "horizontal_multi_brand"
    assert "YEALINK" in structure["brands_detected"]
    assert "JABRA" in structure["brands_detected"]
    assert structure["is_valid"] == True
    
    # Test product extraction
    products = detector.extract_products_from_structure(df, structure)
    assert len(products) > 0
    
    # Check first product
    yealink_products = [p for p in products if p["brand"] == "YEALINK"]
    assert len(yealink_products) > 0
    assert yealink_products[0]["product_code"] == "16WALIC"
