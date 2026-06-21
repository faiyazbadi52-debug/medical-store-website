import urllib.request
import json
import sys
import time

# Give server a second to fully reload if needed
time.sleep(2)

base_url = "http://127.0.0.1:5000"

routes = [
    ("/", "Jan Aushadhi"),
    ("/catalog", "Generic Medicine Catalog"),
    ("/contact", "Contact Jan Aushadhi"),
    ("/login", "Login"),
]

print("--- AUTOMATED API & ROUTE VERIFICATION ---")
failed = False

# 1. Test HTML routes
for route, keyword in routes:
    url = f"{base_url}{route}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            status = response.status
            if status == 200 and keyword in html:
                print(f"[PASS] Route {route} loaded successfully (Keyword: '{keyword}' found)")
            else:
                print(f"[FAIL] Route {route} loaded with status {status} but keyword '{keyword}' missing")
                failed = True
    except Exception as e:
        print(f"[FAIL] Route {route} failed to load: {e}")
        failed = True

# 2. Test JSON Details API
api_route = "/api/medicine/1"
url = f"{base_url}{api_route}"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        status = response.status
        if status == 200 and 'name' in data and 'generic_name' in data:
            print(f"[PASS] API route {api_route} returned valid JSON details for: '{data['name']}'")
        else:
            print(f"[FAIL] API route {api_route} returned status {status} but missing fields")
            failed = True
except Exception as e:
    print(f"[FAIL] API route {api_route} failed to fetch: {e}")
    failed = True

print("------------------------------------------")
if failed:
    print("Verification completed with errors.")
    sys.exit(1)
else:
    print("All routes verified successfully! Server is healthy.")
    sys.exit(0)
