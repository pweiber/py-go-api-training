import requests
from datetime import datetime
import time

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"
ADMIN_EMAIL = "boss@example.com"
ADMIN_PASSWORD = "TestPassword123!"

# Generate a unique email every time so the /register test never fails with "Email already exists"
timestamp = str(int(time.time()))
DYNAMIC_USER_EMAIL = f"test_user_{timestamp}@example.com"
DYNAMIC_USER_PASSWORD = "ValidPassword123!"

test_results = []


def run_test(name, method, path, expected_status, headers=None, json_data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            res = requests.get(url, headers=headers)
        elif method == "POST":
            res = requests.post(url, headers=headers, json=json_data)
        elif method == "PUT":
            res = requests.put(url, headers=headers, json=json_data)
        elif method == "PATCH":
            res = requests.patch(url, headers=headers, json=json_data)
        elif method == "DELETE":
            res = requests.delete(url, headers=headers)

        passed = res.status_code == expected_status
        details = "Success" if passed else f"Expected {expected_status}, Got {res.status_code}. {res.text}"

        test_results.append(
            {"name": name, "method": method, "path": path, "status": "PASS" if passed else "FAIL", "details": details})
        print(f"{'✅' if passed else '❌'} {name}")
        return res
    except Exception as e:
        test_results.append({"name": name, "method": method, "path": path, "status": "FAIL", "details": str(e)})
        print(f"❌ {name} (Exception)")
        return None


def generate_html_report():
    html_content = f"""
    <html><head><title>Full API Master Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }}
        h1 {{ color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #fff; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2c3e50; color: white; }}
        .PASS {{ color: #27ae60; font-weight: bold; }}
        .FAIL {{ color: #c0392b; font-weight: bold; }}
    </style></head><body>
    <h1>🚀 Full API Master Test Report</h1>
    <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <table><tr><th>Test Name</th><th>Method</th><th>Endpoint</th><th>Result</th><th>Details</th></tr>
    """
    for t in test_results:
        html_content += f"<tr><td>{t['name']}</td><td>{t['method']}</td><td>{t['path']}</td><td class='{t['status']}'>{t['status']}</td><td>{t['details']}</td></tr>"
    html_content += "</table></body></html>"

    with open("api_test_report.html", "w", encoding="utf-8") as file:
        file.write(html_content)
    print("\n📄 Master HTML Report generated: api_test_report.html")


# ==========================================
# 🚀 TEST EXECUTION START
# ==========================================
print("🚀 Starting Full API Master Test Suite...\n")

# --- 1. SYSTEM HEALTH ---
run_test("Root Endpoint", "GET", "/", 200)
run_test("Health Check", "GET", "/health", 200)

# --- 2. AUTHENTICATION & USER MANAGEMENT ---
print("\n--- Testing Auth & Users ---")
# Register a new dynamic user
run_test("Register New User", "POST", "/api/v1/auth/register", 201,
         json_data={"email": DYNAMIC_USER_EMAIL, "password": DYNAMIC_USER_PASSWORD})

# Login both users to get their tokens
admin_login = run_test("Login Admin", "POST", "/api/v1/auth/login", 200,
                       json_data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
user_login = run_test("Login Standard User", "POST", "/api/v1/auth/login", 200,
                      json_data={"email": DYNAMIC_USER_EMAIL, "password": DYNAMIC_USER_PASSWORD})

if not admin_login or admin_login.status_code != 200 or not user_login or user_login.status_code != 200:
    print("❌ Fatal Error: Could not acquire tokens. Exiting.")
    exit()

admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

# Test User Profile Endpoints
run_test("Get Admin Profile", "GET", "/api/v1/auth/me", 200, headers=admin_headers)
run_test("List All Users (Admin Only)", "GET", "/api/v1/users", 200, headers=admin_headers)

# Variables for cleanup
author_id, category_id, book_id, review_id = None, None, None, None

try:
    # --- 3. CREATE CORE DATA (As Admin) ---
    print("\n--- Testing Core Data Creation ---")
    res_author = run_test("Create Author", "POST", "/api/v1/authors", 201, headers=admin_headers,
                          json_data={"name": "Auto Author"})
    author_id = res_author.json()["id"] if res_author and res_author.status_code == 201 else None

    res_category = run_test("Create Category", "POST", "/api/v1/categories", 201, headers=admin_headers,
                            json_data={"name": "Auto Category"})
    category_id = res_category.json()["id"] if res_category and res_category.status_code == 201 else None

    if author_id and category_id:
        res_book = run_test("Create Book", "POST", "/api/v1/books", 201, headers=admin_headers, json_data={
            "title": "Auto Book", "isbn": f"99988877{str(int(time.time()))[-5:]}",
            "published_date": "2026-01-01", "author_id": author_id, "category_ids": [category_id]
        })
        book_id = res_book.json()["id"] if res_book and res_book.status_code == 201 else None

    # --- 4. INTERACTIVE FEATURES (As Standard User) ---
    if book_id:
        print("\n--- Testing Interactive Features ---")
        # Standard user favorites the book
        run_test("Add to Favorites", "POST", f"/api/v1/books/{book_id}/favorite", 201, headers=user_headers)
        run_test("List My Favorites", "GET", "/api/v1/users/me/favorites", 200, headers=user_headers)

        # Standard user leaves a review (Admin cannot review their own book)
        res_review = run_test("Leave a Review", "POST", "/api/v1/reviews", 201, headers=user_headers, json_data={
            "book_id": book_id, "rating": 5, "comment": "Great automated book!"
        })
        review_id = res_review.json()["id"] if res_review and res_review.status_code == 201 else None

        # Check the global stats
        run_test("Check Store Stats", "GET", "/api/v1/stats", 200)

finally:
    # --- 5. TEARDOWN / CLEANUP ---
    print("\n--- Testing DELETE / Cleanup ---")
    if review_id: run_test("Delete Review", "DELETE", f"/api/v1/reviews/{review_id}", 200, headers=admin_headers)
    if book_id:
        run_test("Remove from Favorites", "DELETE", f"/api/v1/books/{book_id}/favorite", 200, headers=user_headers)
        run_test("Delete Book", "DELETE", f"/api/v1/books/{book_id}", 200, headers=admin_headers)
    if author_id: run_test("Delete Author", "DELETE", f"/api/v1/authors/{author_id}", 200, headers=admin_headers)
    if category_id: run_test("Delete Category", "DELETE", f"/api/v1/categories/{category_id}", 200,
                             headers=admin_headers)

generate_html_report()