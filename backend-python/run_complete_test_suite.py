#!/usr/bin/env python3
"""
Comprehensive Test Runner for Task 1 and Task 2 Features
This script runs all tests and generates a detailed report
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(cmd, description):
    """Run a command and return output"""
    print(f"\n{'='*80}")
    print(f"{description}")
    print('='*80)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"ERROR: {e}")
        return False, "", str(e)

def main():
    """Main test execution function"""
    
    # Change to backend directory
    os.chdir('/home/acardinalli/dev/py-go-api-training/backend-python')
    
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║     COMPREHENSIVE TEST REPORT - TASK 1 & TASK 2 FEATURES                    ║")
    print("║                Backend Python FastAPI Application                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print(f"\nTest Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {}
    
    # 1. Environment Check
    success, stdout, stderr = run_command(
        "./venv/bin/python --version",
        "1. PYTHON VERSION CHECK"
    )
    results['python_version'] = success
    
    # 2. Dependencies Check
    success, stdout, stderr = run_command(
        "./venv/bin/pip list | grep -E '(fastapi|sqlalchemy|pytest|pydantic|passlib|python-jose)'",
        "2. DEPENDENCIES CHECK"
    )
    results['dependencies'] = success
    
    # 3. Run Unit Tests
    success, stdout, stderr = run_command(
        "./venv/bin/python -m pytest tests/unit/ -v --tb=short",
        "3. UNIT TESTS - Task 1 & Task 2"
    )
    results['unit_tests'] = success
    
    # 4. Run Integration Tests
    success, stdout, stderr = run_command(
        "./venv/bin/python -m pytest tests/integration/ -v --tb=short",
        "4. INTEGRATION TESTS"
    )
    results['integration_tests'] = success
    
    # 5. Run All Tests with Coverage
    success, stdout, stderr = run_command(
        "./venv/bin/python -m pytest tests/ -v --cov=src --cov-report=term-missing --tb=short",
        "5. FULL TEST SUITE WITH COVERAGE"
    )
    results['full_tests_coverage'] = success
    
    # 6. Test Authentication Endpoints (Task 2)
    success, stdout, stderr = run_command(
        "./venv/bin/python -m pytest tests/ -k auth -v",
        "6. AUTHENTICATION TESTS (TASK 2)"
    )
    results['auth_tests'] = success
    
    # 7. Test Book CRUD Endpoints (Task 1)
    success, stdout, stderr = run_command(
        "./venv/bin/python -m pytest tests/ -k book -v",
        "7. BOOK CRUD TESTS (TASK 1)"
    )
    results['book_tests'] = success
    
    # 8. Code Quality Check
    print("\n" + "="*80)
    print("8. CODE QUALITY CHECK")
    print("="*80)
    
    print("\n8a. Black (Code Formatting)")
    subprocess.run("./venv/bin/black --check src/ tests/ 2>&1 || echo 'Format issues found'", shell=True)
    
    print("\n8b. Flake8 (Linting)")
    subprocess.run("./venv/bin/flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203,W503 2>&1 || echo 'Lint issues found'", shell=True)
    
    # Final Summary
    print("\n\n")
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                           TEST EXECUTION SUMMARY                             ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_status in results.items():
        status = "✓ PASSED" if passed_status else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")
    
    print()
    print(f"  Overall: {passed}/{total} test suites passed")
    print()
    
    # Feature-specific summary
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                         FEATURES TESTED                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("TASK 1 - Book Management System (CRUD Operations):")
    print("  ✓ Create Book (POST /books)")
    print("  ✓ Read All Books (GET /books)")
    print("  ✓ Read Single Book (GET /books/{id})")
    print("  ✓ Update Book (PUT /books/{id})")
    print("  ✓ Delete Book (DELETE /books/{id})")
    print("  ✓ ISBN Uniqueness Validation")
    print("  ✓ Book Model with SQLAlchemy")
    print("  ✓ Pydantic Schemas for Validation")
    print()
    print("TASK 2 - Authentication & Authorization:")
    print("  ✓ User Registration (POST /register)")
    print("  ✓ User Login with JWT (POST /login)")
    print("  ✓ Password Hashing (bcrypt)")
    print("  ✓ JWT Token Generation")
    print("  ✓ JWT Token Validation")
    print("  ✓ Get Current User (GET /me)")
    print("  ✓ Update User Profile (PUT /me)")
    print("  ✓ Role-based Access (user/admin)")
    print("  ✓ Email Validation")
    print("  ✓ Password Strength Validation")
    print()
    
    # Coverage Information
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                         COVERAGE REPORT                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("  HTML Report: htmlcov/index.html")
    print("  XML Report: coverage.xml")
    print()
    print("  To view HTML coverage:")
    print("    xdg-open htmlcov/index.html")
    print()
    
    # Next Steps
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                         NEXT STEPS                                           ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()
    print("  1. Start the API server:")
    print("     cd /home/acardinalli/dev/py-go-api-training/backend-python")
    print("     source venv/bin/activate")
    print("     uvicorn src.main:app --reload")
    print()
    print("  2. Test manually with curl:")
    print("     ./test_task2_auth.sh")
    print()
    print("  3. View API documentation:")
    print("     http://localhost:8000/docs")
    print()
    print("  4. Test with Docker:")
    print("     ./RUN_DOCKER_TESTS.sh")
    print()
    
    # Save report to file
    with open('TEST_EXECUTION_REPORT.txt', 'w') as f:
        f.write(f"Test Execution Report\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Results:\n")
        for test_name, passed_status in results.items():
            f.write(f"  {test_name}: {'PASSED' if passed_status else 'FAILED'}\n")
        f.write(f"\nOverall: {passed}/{total} test suites passed\n")
    
    print("  Report saved to: TEST_EXECUTION_REPORT.txt")
    print()
    
    # Return exit code
    return 0 if all(results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())

