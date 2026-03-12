"""
🚀 Comprehensive API Integration Test Suite
============================================
Standalone integration test that exercises ALL API endpoints against a live server.
Covers happy paths, negative/error paths, and authorization checks.
Generates an HTML report at the end.
Usage:
    python tests/e2e/test_api.py
"""
import html as html_module
import requests
from datetime import datetime
import time
import sys
import os

# Report output path — always next to this script file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_PATH = os.path.join(SCRIPT_DIR, "api_test_report.html")

# --- CONFIGURATION ---
BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 10  # seconds — prevents indefinite hangs on stalled connections
API_URL = f"{BASE_URL}/api/v1"
ADMIN_EMAIL = "boss@example.com"
ADMIN_PASSWORD = "TestPassword123!"
# Generate unique identifiers to avoid conflicts across runs
timestamp = str(int(time.time()))
DYNAMIC_USER_EMAIL = f"test_user_{timestamp}@example.com"
DYNAMIC_USER_PASSWORD = "ValidPassword123!"
DYNAMIC_USER2_EMAIL = f"test_user2_{timestamp}@example.com"
DYNAMIC_USER2_PASSWORD = "ValidPassword456!"
test_results = []
current_section = ""
# ==========================================
# HELPER FUNCTIONS
# ==========================================
def set_section(name):
    """Set the current test section for report grouping."""
    global current_section
    current_section = name
    print(f"\n{'='*60}")
    print(f"  📋 {name}")
    print(f"{'='*60}")
def run_test(name, method, path, expected_status, headers=None, json_data=None, params=None):
    """
    Execute a single API test and record the result.
    Args:
        name: Human-readable test name
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        path: URL path (relative to BASE_URL)
        expected_status: Expected HTTP status code
        headers: Optional request headers
        json_data: Optional JSON body
        params: Optional query parameters
    Returns:
        Response object or None on exception
    """
    url = f"{BASE_URL}{path}"
    try:
        kwargs = {"headers": headers, "timeout": REQUEST_TIMEOUT}
        if json_data is not None:
            kwargs["json"] = json_data
        if params is not None:
            kwargs["params"] = params
        if method == "GET":
            res = requests.get(url, **kwargs)
        elif method == "POST":
            res = requests.post(url, **kwargs)
        elif method == "PUT":
            res = requests.put(url, **kwargs)
        elif method == "PATCH":
            res = requests.patch(url, **kwargs)
        elif method == "DELETE":
            res = requests.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        passed = res.status_code == expected_status
        details = "Success" if passed else f"Expected {expected_status}, Got {res.status_code}. {res.text[:300]}"
        test_results.append({
            "section": current_section,
            "name": name,
            "method": method,
            "path": path,
            "status": "PASS" if passed else "FAIL",
            "details": details,
        })
        print(f"  {'✅' if passed else '❌'} {name}")
        return res
    except Exception as e:
        test_results.append({
            "section": current_section,
            "name": name,
            "method": method,
            "path": path,
            "status": "FAIL",
            "details": str(e),
        })
        print(f"  ❌ {name} (Exception: {e})")
        return None
def generate_html_report():
    """Generate a grouped HTML test report with summary statistics."""
    total = len(test_results)
    passed = sum(1 for t in test_results if t["status"] == "PASS")
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    # Group by section
    sections_order = []
    sections_map = {}
    for t in test_results:
        sec = t.get("section", "Other")
        if sec not in sections_map:
            sections_order.append(sec)
            sections_map[sec] = []
        sections_map[sec].append(t)
    rows = ""
    for sec in sections_order:
        esc_sec = html_module.escape(sec)
        rows += f"""<tr class="section-header"><td colspan="5">📋 {esc_sec}</td></tr>\n"""
        for t in sections_map[sec]:
            rows += (
                f"<tr>"
                f"<td>{html_module.escape(t['name'])}</td>"
                f"<td>{html_module.escape(t['method'])}</td>"
                f"<td>{html_module.escape(t['path'])}</td>"
                f"<td class='{html_module.escape(t['status'])}'>{html_module.escape(t['status'])}</td>"
                f"<td>{html_module.escape(t['details'])}</td>"
                f"</tr>\n"
            )
    html_content = f"""<!DOCTYPE html>
<html><head><title>Full API Master Test Report</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f4f4f9; }}
    h1 {{ color: #333; }}
    .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
    .summary .card {{ padding: 15px 25px; border-radius: 8px; color: white; font-size: 18px; font-weight: bold; }}
    .summary .total {{ background-color: #2c3e50; }}
    .summary .pass {{ background-color: #27ae60; }}
    .summary .fail {{ background-color: #c0392b; }}
    .summary .rate {{ background-color: #2980b9; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #fff; }}
    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; font-size: 14px; }}
    th {{ background-color: #2c3e50; color: white; }}
    td {{ max-width: 400px; word-wrap: break-word; }}
    .PASS {{ color: #27ae60; font-weight: bold; }}
    .FAIL {{ color: #c0392b; font-weight: bold; }}
    .section-header td {{ background-color: #ecf0f1; font-weight: bold; font-size: 15px; color: #2c3e50; }}
</style></head><body>
<h1>🚀 Full API Master Test Report</h1>
<p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<div class="summary">
    <div class="card total">Total: {total}</div>
    <div class="card pass">Passed: {passed}</div>
    <div class="card fail">Failed: {failed}</div>
    <div class="card rate">Pass Rate: {pass_rate:.1f}%</div>
</div>
<table>
<tr><th>Test Name</th><th>Method</th><th>Endpoint</th><th>Result</th><th>Details</th></tr>
{rows}
</table>
</body></html>"""
    with open(REPORT_PATH, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"\n📄 Master HTML Report generated: {REPORT_PATH}")
    print(f"   Total: {total} | ✅ Passed: {passed} | ❌ Failed: {failed} | Rate: {pass_rate:.1f}%")

def main():
    # ==========================================
    # 🚀 TEST EXECUTION START
    # ==========================================
    print("🚀 Starting Full API Master Test Suite...\n")
    # Track IDs for cleanup
    author_id = None
    author2_id = None
    category_id = None
    category2_id = None
    book_id = None
    review_id = None
    user_id = None
    user2_id = None
    admin_headers = None
    user_headers = None
    user2_headers = None
    user2_is_admin = False
    try:
        # ======================================================================
        # 1. SYSTEM HEALTH
        # ======================================================================
        set_section("System Health")
        run_test("Root Endpoint", "GET", "/", 200)
        run_test("Health Check", "GET", "/health", 200)
        # ======================================================================
        # 2. AUTHENTICATION — Registration
        # ======================================================================
        set_section("Authentication — Registration")
        res = run_test("Register New User", "POST", "/api/v1/auth/register", 201,
                       json_data={"email": DYNAMIC_USER_EMAIL, "password": DYNAMIC_USER_PASSWORD})
        if res and res.status_code == 201:
            user_id = res.json().get("id")
        res = run_test("Register Second User", "POST", "/api/v1/auth/register", 201,
                       json_data={"email": DYNAMIC_USER2_EMAIL, "password": DYNAMIC_USER2_PASSWORD})
        if res and res.status_code == 201:
            user2_id = res.json().get("id")
        # Negative: duplicate registration
        run_test("Register Duplicate Email (400)", "POST", "/api/v1/auth/register", 400,
                 json_data={"email": DYNAMIC_USER_EMAIL, "password": DYNAMIC_USER_PASSWORD})
        # Negative: weak password
        run_test("Register Weak Password (422)", "POST", "/api/v1/auth/register", 422,
                 json_data={"email": f"weak_{timestamp}@example.com", "password": "short"})
        # Negative: invalid email format
        run_test("Register Invalid Email (422)", "POST", "/api/v1/auth/register", 422,
                 json_data={"email": "not-an-email", "password": "ValidPassword123!"})
        # ======================================================================
        # 3. AUTHENTICATION — Login
        # ======================================================================
        set_section("Authentication — Login")
    
        # Record time of first login for rate limit calculations
        first_login_time = time.time()
    
        # Login the 3 users first (logins 1-3 of the 5/min rate limit)
        admin_login = run_test("Login Admin", "POST", "/api/v1/auth/login", 200,
                               json_data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        user_login = run_test("Login Standard User", "POST", "/api/v1/auth/login", 200,
                              json_data={"email": DYNAMIC_USER_EMAIL, "password": DYNAMIC_USER_PASSWORD})
        user2_login = run_test("Login Second User", "POST", "/api/v1/auth/login", 200,
                               json_data={"email": DYNAMIC_USER2_EMAIL, "password": DYNAMIC_USER2_PASSWORD})
    
        # Abort if we can't get tokens
        if (not admin_login or admin_login.status_code != 200
                or not user_login or user_login.status_code != 200
                or not user2_login or user2_login.status_code != 200):
            print("\n❌ Fatal Error: Could not acquire tokens. Exiting.")
            generate_html_report()
            sys.exit(1)
    
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        user_headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}
        user2_headers = {"Authorization": f"Bearer {user2_login.json()['access_token']}"}
    
        # ======================================================================
        # 4. AUTHENTICATION — Profile
        # ======================================================================
        set_section("Authentication — Profile")
    
        run_test("Get Admin Profile (GET /auth/me)", "GET", "/api/v1/auth/me", 200, headers=admin_headers)
        run_test("Get User Profile (GET /auth/me)", "GET", "/api/v1/auth/me", 200, headers=user_headers)
    
        # Negative: no auth
        run_test("Get Profile Without Auth (401)", "GET", "/api/v1/auth/me", 401)
    
        # Update user profile
        run_test("Update Profile Email (PUT /auth/me)", "PUT", "/api/v1/auth/me", 200,
                 headers=user2_headers,
                 json_data={"email": f"updated_{timestamp}@example.com",
                            "current_password": DYNAMIC_USER2_PASSWORD})
    
        # Negative: update without current password
        run_test("Update Profile Without Current Password (400)", "PUT", "/api/v1/auth/me", 400,
                 headers=user2_headers,
                 json_data={"email": f"hack_{timestamp}@example.com"})
    
        # Re-login user2 after email change (login 4 of 5/min — still under the limit)
        user2_login_new = run_test("Re-Login User2 After Email Change", "POST", "/api/v1/auth/login", 200,
                                   json_data={"email": f"updated_{timestamp}@example.com",
                                               "password": DYNAMIC_USER2_PASSWORD})
        if user2_login_new and user2_login_new.status_code == 200:
            user2_headers = {"Authorization": f"Bearer {user2_login_new.json()['access_token']}"}
    
        # ======================================================================
        # 4b. LOGIN — Negative Tests (may need rate limit cooldown after 4 logins above)
        # ======================================================================
        set_section("Authentication — Login Negative Tests")
    
        # Wait for rate limit window to fully expire (5 logins/min rolling window)
        # All 4 logins happened after first_login_time; wait 62s from that point
        elapsed = time.time() - first_login_time
        wait_needed = max(0, 62 - elapsed)
        if wait_needed > 0:
            print(f"  ⏳ Waiting {int(wait_needed)}s for login rate limit window to reset...")
            time.sleep(wait_needed)
    
        # Negative: wrong password
        run_test("Login Wrong Password (401)", "POST", "/api/v1/auth/login", 401,
                 json_data={"email": ADMIN_EMAIL, "password": "WrongPassword999!"})
    
        # Negative: non-existent user
        run_test("Login Non-Existent User (401)", "POST", "/api/v1/auth/login", 401,
                 json_data={"email": "ghost@nowhere.com", "password": "GhostPass123!"})
        # ======================================================================
        # 5. USER MANAGEMENT (Admin Only)
        # ======================================================================
        set_section("User Management (Admin Only)")
        run_test("List All Users (Admin)", "GET", "/api/v1/users", 200, headers=admin_headers)
        # Negative: standard user tries to list users
        run_test("List Users as Standard User (403)", "GET", "/api/v1/users", 403, headers=user_headers)
        # Get user by ID
        if user_id:
            run_test("Get User by ID (Admin)", "GET", f"/api/v1/users/{user_id}", 200, headers=admin_headers)
        # Negative: non-existent user
        run_test("Get Non-Existent User (404)", "GET", "/api/v1/users/99999", 404, headers=admin_headers)
        # Negative: standard user tries get user by ID
        if user_id:
            run_test("Get User by ID as Standard User (403)", "GET", f"/api/v1/users/{user_id}", 403,
                     headers=user_headers)
        # Update user role
        if user2_id:
            run_test("Promote User2 to Admin", "PATCH", f"/api/v1/users/{user2_id}/role", 200,
                     headers=admin_headers, json_data={"role": "admin"})
            # Demote back to user
            demote_res = run_test("Demote User2 Back to User", "PATCH", f"/api/v1/users/{user2_id}/role", 200,
                                  headers=admin_headers, json_data={"role": "user"})
            # Track whether user2 is still admin (affects later authorization tests)
            user2_is_admin = (demote_res is None or demote_res.status_code != 200)
        # Negative: standard user tries to update roles
        if user2_id:
            run_test("Update Role as Standard User (403)", "PATCH", f"/api/v1/users/{user2_id}/role", 403,
                     headers=user_headers, json_data={"role": "admin"})
        # Negative: non-existent user role update
        run_test("Update Role Non-Existent User (404)", "PATCH", "/api/v1/users/99999/role", 404,
                 headers=admin_headers, json_data={"role": "admin"})
        # ======================================================================
        # 6. AUTHORS — CRUD
        # ======================================================================
        set_section("Authors — CRUD")
        # Create
        res = run_test("Create Author (Admin)", "POST", "/api/v1/authors", 201, headers=admin_headers,
                       json_data={"name": f"Author {timestamp}", "bio": "Test author biography",
                                  "nationality": "Brazilian"})
        author_id = res.json()["id"] if res and res.status_code == 201 else None
        res = run_test("Create Second Author (Admin)", "POST", "/api/v1/authors", 201, headers=admin_headers,
                       json_data={"name": f"Author2 {timestamp}"})
        author2_id = res.json()["id"] if res and res.status_code == 201 else None
        # Negative: standard user tries to create author
        run_test("Create Author as Standard User (403)", "POST", "/api/v1/authors", 403,
                 headers=user_headers, json_data={"name": "Unauthorized Author"})
        # List
        run_test("List All Authors", "GET", "/api/v1/authors", 200)
        # Get single
        if author_id:
            run_test("Get Author by ID", "GET", f"/api/v1/authors/{author_id}", 200)
        # Negative: non-existent
        run_test("Get Non-Existent Author (404)", "GET", "/api/v1/authors/99999", 404)
        # Update
        if author_id:
            run_test("Update Author (Admin)", "PUT", f"/api/v1/authors/{author_id}", 200,
                     headers=admin_headers, json_data={"bio": "Updated biography"})
        # Negative: standard user update
        if author_id:
            run_test("Update Author as Standard User (403)", "PUT", f"/api/v1/authors/{author_id}", 403,
                     headers=user_headers, json_data={"bio": "Hacked bio"})
        # Negative: update non-existent
        run_test("Update Non-Existent Author (404)", "PUT", "/api/v1/authors/99999", 404,
                 headers=admin_headers, json_data={"bio": "Ghost bio"})
        # ======================================================================
        # 7. CATEGORIES — CRUD
        # ======================================================================
        set_section("Categories — CRUD")
        # Create
        res = run_test("Create Category (Admin)", "POST", "/api/v1/categories", 201, headers=admin_headers,
                       json_data={"name": f"Category {timestamp}", "description": "Test category"})
        category_id = res.json()["id"] if res and res.status_code == 201 else None
        res = run_test("Create Second Category (Admin)", "POST", "/api/v1/categories", 201, headers=admin_headers,
                       json_data={"name": f"Category2 {timestamp}"})
        category2_id = res.json()["id"] if res and res.status_code == 201 else None
        # Negative: standard user tries to create category
        run_test("Create Category as Standard User (403)", "POST", "/api/v1/categories", 403,
                 headers=user_headers, json_data={"name": "Unauthorized Category"})
        # Negative: duplicate category name
        if category_id:
            run_test("Create Duplicate Category (400)", "POST", "/api/v1/categories", 400,
                     headers=admin_headers, json_data={"name": f"Category {timestamp}"})
        # List
        run_test("List All Categories", "GET", "/api/v1/categories", 200)
        # Get single
        if category_id:
            run_test("Get Category by ID", "GET", f"/api/v1/categories/{category_id}", 200)
        # Negative: non-existent
        run_test("Get Non-Existent Category (404)", "GET", "/api/v1/categories/99999", 404)
        # Update
        if category_id:
            run_test("Update Category (Admin)", "PUT", f"/api/v1/categories/{category_id}", 200,
                     headers=admin_headers, json_data={"description": "Updated description"})
        # Negative: standard user update
        if category_id:
            run_test("Update Category as Standard User (403)", "PUT", f"/api/v1/categories/{category_id}", 403,
                     headers=user_headers, json_data={"description": "Hacked description"})
        # Negative: update non-existent
        run_test("Update Non-Existent Category (404)", "PUT", "/api/v1/categories/99999", 404,
                 headers=admin_headers, json_data={"description": "Ghost"})
        # ======================================================================
        # 8. BOOKS — CRUD
        # ======================================================================
        set_section("Books — CRUD")
        if author_id and category_id:
            # Create book (admin) — schema uses author_ids (list), not author_id
            isbn = f"978-0-{timestamp[-9:]}"
            res = run_test("Create Book (Admin)", "POST", "/api/v1/books", 201, headers=admin_headers,
                           json_data={
                               "title": f"Test Book {timestamp}",
                               "isbn": isbn,
                               "published_date": "2026-01-15",
                               "description": "A comprehensive test book",
                               "author_ids": [author_id],
                               "category_ids": [category_id],
                           })
            book_id = res.json()["id"] if res and res.status_code == 201 else None
            # Negative: standard user tries to create book
            run_test("Create Book as Standard User (403)", "POST", "/api/v1/books", 403,
                     headers=user_headers,
                     json_data={
                         "title": "Unauthorized Book",
                         "isbn": f"978-1-{timestamp[-9:]}",
                         "published_date": "2026-01-01",
                         "author_ids": [author_id],
                         "category_ids": [category_id],
                     })
            # Negative: duplicate ISBN
            if book_id:
                run_test("Create Book Duplicate ISBN (400)", "POST", "/api/v1/books", 400,
                         headers=admin_headers,
                         json_data={
                             "title": "Duplicate ISBN Book",
                             "isbn": isbn,
                             "published_date": "2026-02-01",
                             "author_ids": [author_id],
                             "category_ids": [category_id],
                         })
            # Negative: non-existent author
            run_test("Create Book Invalid Author (404)", "POST", "/api/v1/books", 404,
                     headers=admin_headers,
                     json_data={
                         "title": "Ghost Author Book",
                         "isbn": f"978-2-{timestamp[-9:]}",
                         "published_date": "2026-03-01",
                         "author_ids": [99999],
                         "category_ids": [category_id],
                     })
            # Negative: non-existent category
            run_test("Create Book Invalid Category (404)", "POST", "/api/v1/books", 404,
                     headers=admin_headers,
                     json_data={
                         "title": "Ghost Category Book",
                         "isbn": f"978-3-{timestamp[-9:]}",
                         "published_date": "2026-04-01",
                         "author_ids": [author_id],
                         "category_ids": [99999],
                     })
        # List books (public, with pagination)
        run_test("List Books (Page 1)", "GET", "/api/v1/books", 200, params={"page": 1, "size": 5})
        # List books with search
        if book_id:
            run_test("Search Books by Title", "GET", "/api/v1/books", 200,
                     params={"search": f"Test Book {timestamp}"})
        # List books with author filter
        if author_id:
            run_test("Filter Books by Author", "GET", "/api/v1/books", 200,
                     params={"author_id": author_id})
        # Get single book
        if book_id:
            run_test("Get Book by ID", "GET", f"/api/v1/books/{book_id}", 200)
        # Negative: non-existent book
        run_test("Get Non-Existent Book (404)", "GET", "/api/v1/books/99999", 404)
        # Update book (admin)
        if book_id:
            run_test("Update Book (Admin)", "PUT", f"/api/v1/books/{book_id}", 200,
                     headers=admin_headers,
                     json_data={"description": "Updated description for the test book"})
        # Negative: standard user tries to update someone else's book
        if book_id:
            run_test("Update Book as Non-Owner User (403)", "PUT", f"/api/v1/books/{book_id}", 403,
                     headers=user_headers,
                     json_data={"description": "Hacked description"})
        # Negative: update non-existent book
        run_test("Update Non-Existent Book (404)", "PUT", "/api/v1/books/99999", 404,
                 headers=admin_headers, json_data={"description": "Ghost"})
        # Update book categories
        if book_id and category2_id:
            run_test("Update Book Categories (Admin)", "PUT", f"/api/v1/books/{book_id}/categories", 200,
                     headers=admin_headers, json_data={"category_ids": [category_id, category2_id]})
        # Negative: update book categories with non-existent category
        if book_id:
            run_test("Update Book Categories Invalid (404)", "PUT", f"/api/v1/books/{book_id}/categories", 404,
                     headers=admin_headers, json_data={"category_ids": [99999]})
        # ======================================================================
        # 9. REVIEWS — CRUD
        # ======================================================================
        set_section("Reviews — CRUD")
        if book_id:
            # Standard user creates a review (admin can't review their own book)
            res = run_test("Create Review (Standard User)", "POST", "/api/v1/reviews", 201,
                           headers=user_headers,
                           json_data={"book_id": book_id, "rating": 5,
                                      "comment": "Excellent automated test book!"})
            review_id = res.json()["id"] if res and res.status_code == 201 else None
            # Negative: admin tries to review own book
            run_test("Review Own Book (400)", "POST", "/api/v1/reviews", 400,
                     headers=admin_headers,
                     json_data={"book_id": book_id, "rating": 4, "comment": "Self-review attempt"})
            # Negative: duplicate review (same user, same book)
            run_test("Duplicate Review (400)", "POST", "/api/v1/reviews", 400,
                     headers=user_headers,
                     json_data={"book_id": book_id, "rating": 3, "comment": "Duplicate review"})
            # Negative: review non-existent book
            run_test("Review Non-Existent Book (404)", "POST", "/api/v1/reviews", 404,
                     headers=user_headers,
                     json_data={"book_id": 99999, "rating": 3, "comment": "Ghost book review"})
            # Negative: review without auth
            run_test("Review Without Auth (401)", "POST", "/api/v1/reviews", 401,
                     json_data={"book_id": book_id, "rating": 3, "comment": "No auth"})
            # Get book reviews
            run_test("Get Book Reviews", "GET", f"/api/v1/books/{book_id}/reviews", 200)
            # Negative: reviews for non-existent book
            run_test("Get Reviews Non-Existent Book (404)", "GET", "/api/v1/books/99999/reviews", 404)
            # Get single review
            if review_id:
                run_test("Get Review by ID", "GET", f"/api/v1/reviews/{review_id}", 200)
            # Negative: non-existent review
            run_test("Get Non-Existent Review (404)", "GET", "/api/v1/reviews/99999", 404)
            # Update review (owner only)
            if review_id:
                run_test("Update Review (Owner)", "PUT", f"/api/v1/reviews/{review_id}", 200,
                         headers=user_headers,
                         json_data={"rating": 4, "comment": "Updated: still a great book!"})
            # Negative: user2 tries to update user1's review
            if review_id:
                run_test("Update Review as Non-Owner (403)", "PUT", f"/api/v1/reviews/{review_id}", 403,
                         headers=user2_headers,
                         json_data={"rating": 1, "comment": "Hacked review"})
            # Negative: update non-existent review
            run_test("Update Non-Existent Review (404)", "PUT", "/api/v1/reviews/99999", 404,
                     headers=user_headers, json_data={"rating": 1})
        # ======================================================================
        # 10. FAVORITES
        # ======================================================================
        set_section("Favorites")
        if book_id:
            # Add to favorites (standard user)
            run_test("Add Book to Favorites", "POST", f"/api/v1/books/{book_id}/favorite", 201,
                     headers=user_headers)
            # Negative: duplicate favorite
            run_test("Add Duplicate Favorite (400)", "POST", f"/api/v1/books/{book_id}/favorite", 400,
                     headers=user_headers)
            # Negative: favorite non-existent book
            run_test("Favorite Non-Existent Book (404)", "POST", "/api/v1/books/99999/favorite", 404,
                     headers=user_headers)
            # Negative: favorite without auth
            run_test("Favorite Without Auth (401)", "POST", f"/api/v1/books/{book_id}/favorite", 401)
            # List my favorites
            run_test("List My Favorites", "GET", "/api/v1/users/me/favorites", 200, headers=user_headers)
            # User2 also favorites (for cross-user coverage)
            run_test("User2 Add Favorite", "POST", f"/api/v1/books/{book_id}/favorite", 201,
                     headers=user2_headers)
            run_test("User2 List Favorites", "GET", "/api/v1/users/me/favorites", 200,
                     headers=user2_headers)
        # ======================================================================
        # 11. STATISTICS
        # ======================================================================
        set_section("Statistics")
        run_test("Get Store Stats", "GET", "/api/v1/stats", 200)
        # ======================================================================
        # 12. DELETE / NEGATIVE — Constraint & Authorization Tests
        # ======================================================================
        set_section("Delete Constraints & Negative Tests")
        # Negative: delete author that has books (should be 409 Conflict)
        if author_id and book_id:
            run_test("Delete Author with Books (409)", "DELETE", f"/api/v1/authors/{author_id}", 409,
                     headers=admin_headers)
        # Negative: standard user tries to delete book
        if book_id:
            run_test("Delete Book as Standard User (403)", "DELETE", f"/api/v1/books/{book_id}", 403,
                     headers=user_headers)
        # Negative: delete non-existent entities
        run_test("Delete Non-Existent Author (404)", "DELETE", "/api/v1/authors/99999", 404,
                 headers=admin_headers)
        run_test("Delete Non-Existent Category (404)", "DELETE", "/api/v1/categories/99999", 404,
                 headers=admin_headers)
        run_test("Delete Non-Existent Book (404)", "DELETE", "/api/v1/books/99999", 404,
                 headers=admin_headers)
        run_test("Delete Non-Existent Review (404)", "DELETE", "/api/v1/reviews/99999", 404,
                 headers=admin_headers)
        # Negative: user2 tries to delete user1's review
        # Note: user2 must be a regular user for this to return 403.
        # If the demote failed earlier, user2 is still admin and CAN delete any review.
        if review_id and not user2_is_admin:
            run_test("Delete Review as Non-Owner (403)", "DELETE", f"/api/v1/reviews/{review_id}", 403,
                     headers=user2_headers)
        # Negative: remove non-favorited book
        run_test("Remove Non-Favorited Book (404)", "DELETE", "/api/v1/books/99999/favorite", 404,
                 headers=user_headers)
    finally:
        # ======================================================================
        # 13. TEARDOWN — Clean Up All Created Entities
        # ======================================================================
        set_section("Teardown / Cleanup")
        if admin_headers:
            # Delete review first (depends on book)
            # Note: review may have already been deleted if user2 was still admin during non-owner test
            if review_id:
                del_review = run_test("Delete Review", "DELETE", f"/api/v1/reviews/{review_id}", 200,
                                      headers=admin_headers)
                # Accept 404 as well — review may already be gone
                if del_review and del_review.status_code == 404:
                    # Retroactively mark as PASS since this is expected
                    test_results[-1]["status"] = "PASS"
                    test_results[-1]["details"] = "Success (review already deleted)"
            # Remove favorites (depends on book)
            if book_id and user_headers:
                run_test("Remove User1 Favorite", "DELETE", f"/api/v1/books/{book_id}/favorite", 200,
                         headers=user_headers)
            if book_id and user2_headers:
                run_test("Remove User2 Favorite", "DELETE", f"/api/v1/books/{book_id}/favorite", 200,
                         headers=user2_headers)
            # Delete book (depends on author & category)
            if book_id:
                run_test("Delete Book", "DELETE", f"/api/v1/books/{book_id}", 200,
                         headers=admin_headers)
            # Delete authors (now free of books)
            if author_id:
                run_test("Delete Author", "DELETE", f"/api/v1/authors/{author_id}", 200,
                         headers=admin_headers)
            if author2_id:
                run_test("Delete Second Author", "DELETE", f"/api/v1/authors/{author2_id}", 200,
                         headers=admin_headers)
            # Delete categories
            if category_id:
                run_test("Delete Category", "DELETE", f"/api/v1/categories/{category_id}", 200,
                         headers=admin_headers)
            if category2_id:
                run_test("Delete Second Category", "DELETE", f"/api/v1/categories/{category2_id}", 200,
                         headers=admin_headers)
        else:
            print("  ⚠️  Skipping teardown — no admin token available (login failed)")
        generate_html_report()


if __name__ == "__main__":
    main()
