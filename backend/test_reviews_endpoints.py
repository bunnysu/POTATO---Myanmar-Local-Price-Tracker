#!/usr/bin/env python3
"""
Test script to verify reviews endpoints are working
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_reviews_endpoints():
    """Test the reviews endpoints"""
    
    print("🧪 Testing Reviews Endpoints")
    print("=" * 50)
    
    # Test 1: Check if reviews endpoint exists
    print("\n1️⃣ Testing /api/reviews/ endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/reviews/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            reviews = response.json()
            print(f"   Found {len(reviews)} reviews")
            if reviews:
                print(f"   Sample review: {reviews[0]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check if shops rating endpoint exists
    print("\n2️⃣ Testing /api/shops/1/rating endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/shops/1/rating")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            rating_data = response.json()
            print(f"   Rating data: {rating_data}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check if shops reviews endpoint exists
    print("\n3️⃣ Testing /api/shops/1/reviews endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/shops/1/reviews")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            reviews = response.json()
            print(f"   Found {len(reviews)} reviews for shop 1")
            if reviews:
                print(f"   Sample review: {reviews[0]}")
                # Check if user details are included
                if "user_name" in reviews[0]:
                    print(f"   ✅ User details included: {reviews[0]['user_name']} ({reviews[0]['user_role']})")
                else:
                    print(f"   ❌ User details missing")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Check if shops endpoint exists
    print("\n4️⃣ Testing /api/shops/ endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/shops/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            shops = response.json()
            print(f"   Found {len(shops)} shops")
            if shops:
                print(f"   Sample shop: {shops[0]}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")

if __name__ == "__main__":
    test_reviews_endpoints()
