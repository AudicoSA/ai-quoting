# diagnose.py - Check what's actually available
import sys
sys.path.append('.')

try:
    from app.db.sqlantern import *
    print("✅ SQLantern import successful")
    
    # Check what's imported
    import app.db.sqlantern as sqlantern_module
    
    print("\n📋 Available items in sqlantern module:")
    for item in dir(sqlantern_module):
        if not item.startswith('_'):
            obj = getattr(sqlantern_module, item)
            print(f"  - {item}: {type(obj)}")
            
            # If it's a class, show its methods
            if hasattr(obj, '__class__') and hasattr(obj, '__dict__'):
                print(f"    Methods: {[m for m in dir(obj) if not m.startswith('_')]}")
            
except Exception as e:
    print(f"❌ Error importing sqlantern: {e}")
    
    # Try to see what files exist
    import os
    if os.path.exists('app/db/sqlantern.py'):
        print("\n📁 File exists. First 20 lines:")
        with open('app/db/sqlantern.py', 'r') as f:
            for i, line in enumerate(f):
                if i < 20:
                    print(f"{i+1:2d}: {line.rstrip()}")
                else:
                    break
    else:
        print("❌ File app/db/sqlantern.py not found")
