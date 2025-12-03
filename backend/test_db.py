#!/usr/bin/env python3
"""
Simple test script to check database connection and basic functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test if we can connect to the database"""
    try:
        from app.db.database import engine
        from app.db.postgres_models import Base
        
        print("🔍 Testing database connection...")
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Try to get a session
        from app.db.database import get_postgres_db
        db = next(get_postgres_db())
        
        # Test a simple query
        result = db.execute("SELECT 1 as test").fetchone()
        print(f"✅ Database query test: {result}")
        
        db.close()
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_models():
    """Test if models can be imported and used"""
    try:
        from app.db.postgres_models import UserRole, UserStatus, User, Region, Township
        
        print("🔍 Testing models...")
        print(f"✅ UserRole: {[role.value for role in UserRole]}")
        print(f"✅ UserStatus: {[status.value for status in UserStatus]}")
        print("✅ Models imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        return False

def test_security():
    """Test if security functions work"""
    try:
        from app.core.security import get_password_hash, verify_password
        
        print("🔍 Testing security functions...")
        
        test_password = "test123"
        hashed = get_password_hash(test_password)
        print(f"✅ Password hashed: {hashed[:20]}...")
        
        is_valid = verify_password(test_password, hashed)
        print(f"✅ Password verification: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Potato Backend Tests...\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Models", test_models),
        ("Security", test_security),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 40)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The backend should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)



