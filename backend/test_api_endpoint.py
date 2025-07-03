# backend/test_api_endpoint.py
import requests
import json

def test_upload_endpoint():
    """
    Test the enhanced upload endpoint
    """
    print("🌐 Testing API Endpoint")
    print("=" * 25)
    
    # Update with your actual file path
    file_path = "path/to/Nology Pricelist July 2025.xlsx"
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            # Test the enhanced upload
            response = requests.post(
                'http://localhost:8000/training-center/upload/advanced',
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Upload successful!")
                print(f"Status: {result.get('status')}")
                print(f"Message: {result.get('message')}")
                
                preview_data = result.get('preview_data', {})
                print(f"Brands detected: {len(preview_data.get('brands_detected', []))}")
                print(f"Total products: {preview_data.get('total_products', 0)}")
                print(f"Processing ready: {result.get('processing_ready', False)}")
                
                return result
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(response.text)
                
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_upload_endpoint()
