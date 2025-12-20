"""
Python script to test API endpoints

Usage:
    python scripts/test_api.py
    python scripts/test_api.py --base-url http://localhost:8000
"""

import argparse
import requests
import json
from typing import Dict, Any


def test_endpoint(
    method: str,
    url: str,
    description: str,
    data: Dict[str, Any] = None,
    expected_status: int = 200
) -> bool:
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"  {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"  ❌ Unsupported method: {method}")
            return False
        
        status_ok = response.status_code == expected_status
        status_icon = "✅" if status_ok else "❌"
        
        print(f"  {status_icon} Status: {response.status_code} (expected: {expected_status})")
        
        try:
            response_json = response.json()
            print(f"  Response:")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except:
            print(f"  Response: {response.text[:200]}")
        
        return status_ok
        
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Connection Error: Cannot connect to {url}")
        print(f"     Make sure API is running!")
        return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test PIKA Memory API endpoints")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of the API (default: http://127.0.0.1:8000)"
    )
    
    args = parser.parse_args()
    base_url = args.base_url.rstrip('/')
    
    print("="*60)
    print("PIKA Memory API - Endpoint Testing")
    print("="*60)
    print(f"Base URL: {base_url}")
    
    results = []
    
    # Test 1: Root endpoint
    results.append(test_endpoint(
        "GET",
        f"{base_url}/",
        "Root endpoint"
    ))
    
    # Test 2: Health check
    results.append(test_endpoint(
        "GET",
        f"{base_url}/api/v1/health",
        "Health check"
    ))
    
    # Test 3: Liveness probe
    results.append(test_endpoint(
        "GET",
        f"{base_url}/api/v1/health/live",
        "Liveness probe"
    ))
    
    # Test 4: Readiness probe
    results.append(test_endpoint(
        "GET",
        f"{base_url}/api/v1/health/ready",
        "Readiness probe"
    ))
    
    # Test 5: Extract facts
    extract_data = {
        "user_id": "test-user-123",
        "conversation_id": "test-conv-456",
        "conversation": [
            {"role": "user", "content": "I love playing tennis on weekends"},
            {"role": "assistant", "content": "That is great! Tennis is a wonderful sport."},
            {"role": "user", "content": "I have a cat named Whiskers"}
        ],
        "metadata": {"source": "test"}
    }
    results.append(test_endpoint(
        "POST",
        f"{base_url}/api/v1/extract_facts",
        "Extract facts",
        data=extract_data
    ))
    
    # Test 6: Search facts
    search_data = {
        "user_id": "test-user-123",
        "query": "user favorite activities",
        "limit": 10,
        "score_threshold": 0.4
    }
    results.append(test_endpoint(
        "POST",
        f"{base_url}/api/v1/search_facts",
        "Search facts",
        data=search_data
    ))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

