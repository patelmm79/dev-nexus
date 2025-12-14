"""
Test script for Authentication Proxy

Tests the proxy server endpoints without needing a frontend.
"""

import requests
import json
import sys

# Configuration
PROXY_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{PROXY_URL}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_root():
    """Test root endpoint"""
    print("\nTesting / endpoint...")
    try:
        response = requests.get(f"{PROXY_URL}/")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_skills():
    """Test skills list endpoint"""
    print("\nTesting /api/skills endpoint...")
    try:
        response = requests.get(f"{PROXY_URL}/api/skills")
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Total skills: {data.get('total', 0)}")

        if data.get('skills'):
            print(f"  Sample skills:")
            for skill in data['skills'][:3]:
                auth_label = "🔒" if skill.get('requires_auth') else "🔓"
                print(f"    {auth_label} {skill['skill_id']}: {skill['description']}")

        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_execute_public_skill():
    """Test executing a public skill"""
    print("\nTesting /api/execute with public skill...")
    try:
        response = requests.post(
            f"{PROXY_URL}/api/execute",
            json={
                "skill_id": "get_repository_list",
                "input": {
                    "include_metadata": False
                }
            }
        )
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Success: {data.get('success', False)}")

        if data.get('success'):
            print(f"  Repositories: {data.get('total_count', 0)}")
        else:
            print(f"  Error: {data.get('error', 'Unknown error')}")

        return response.status_code == 200
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_execute_authenticated_skill():
    """Test executing an authenticated skill"""
    print("\nTesting /api/execute with authenticated skill...")
    try:
        response = requests.post(
            f"{PROXY_URL}/api/execute",
            json={
                "skill_id": "add_deployment_info",
                "input": {
                    "repository": "test/proxy-test",
                    "deployment_info": {
                        "ci_cd_platform": "github_actions",
                        "infrastructure": {
                            "test": "proxy authentication"
                        }
                    }
                }
            }
        )
        print(f"  Status: {response.status_code}")
        data = response.json()
        print(f"  Success: {data.get('success', False)}")

        if data.get('success'):
            print(f"  Message: {data.get('message', '')}")
        else:
            print(f"  Error: {data.get('error', 'Unknown error')}")

        return response.status_code == 200 and data.get('success', False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Authentication Proxy Test Suite")
    print("=" * 60)
    print(f"Proxy URL: {PROXY_URL}")
    print()

    results = {
        "Health Check": test_health(),
        "Root Endpoint": test_root(),
        "List Skills": test_skills(),
        "Public Skill Execution": test_execute_public_skill(),
        "Authenticated Skill Execution": test_execute_authenticated_skill()
    }

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()

    total = len(results)
    passed = sum(results.values())
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
