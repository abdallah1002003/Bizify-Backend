import requests
import sys
import os

def check_health(base_url):
    print(f"Checking health at {base_url}/health...")
    try:
        resp = requests.get(f"{base_url}/health", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        print(f"Health check passed: {data}")
        return True
    except Exception as e:
        print(f"Health check FAILED: {e}")
        return False

def check_auth_status(base_url):
    print(f"Checking auth status at {base_url}/api/v1/auth/status...")
    try:
        resp = requests.get(f"{base_url}/api/v1/auth/status", timeout=10)
        # Should be 200 even if not logged in (to check if endpoint exists)
        # or 401 if it's protected. If it's a 404, the path is wrong.
        if resp.status_code in [200, 401]:
            print(f"Auth status check passed (Status: {resp.status_code})")
            return True
        else:
            print(f"Auth status check FAILED (Status: {resp.status_code})")
            return False
    except Exception as e:
        print(f"Auth status check FAILED: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DEPLOY_URL", "http://localhost:8000")
    
    success = True
    if not check_health(url):
        success = False
    
    if not check_auth_status(url):
        success = False
        
    if not success:
        print("Smoke tests FAILED!")
        sys.exit(1)
    
    print("Smoke tests PASSED!")
    sys.exit(0)
