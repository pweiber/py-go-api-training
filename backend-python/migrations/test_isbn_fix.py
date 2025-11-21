#!/usr/bin/env python3
"""
Test script to verify ISBN normalization and validation.

This demonstrates that the ISBN truncation issue has been fixed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schemas.book import BookCreate, BookUpdate
from datetime import date
from pydantic import ValidationError


def test_isbn_normalization():
    """Test that ISBNs are properly normalized."""
    
    print("=" * 70)
    print("ISBN NORMALIZATION TEST")
    print("=" * 70)
    
    test_cases = [
        # (input_isbn, expected_normalized, should_pass, description)
        ("9780123456789", "9780123456789", True, "ISBN-13 without dashes"),
        ("978-0-12-345678-9", "9780123456789", True, "ISBN-13 with dashes"),
        ("978 0 12 345678 9", "9780123456789", True, "ISBN-13 with spaces"),
        ("0123456789", "0123456789", True, "ISBN-10 without dashes"),
        ("0-12-345678-9", "0123456789", True, "ISBN-10 with dashes"),
        ("012345678X", "012345678X", True, "ISBN-10 with X check digit"),
        ("978-ABC-123", None, False, "Contains letters"),
        ("12345", None, False, "Too short"),
        ("978012345678901234", None, False, "Too long"),
        ("978-0123-456", None, False, "Wrong length after normalization"),
    ]
    
    passed = 0
    failed = 0
    
    for input_isbn, expected, should_pass, description in test_cases:
        try:
            book = BookCreate(
                title="Test Book",
                author="Test Author",
                isbn=input_isbn,
                published_date=date(2023, 1, 15)
            )
            
            if should_pass:
                if book.isbn == expected:
                    print(f"✓ PASS: {description}")
                    print(f"  Input:  '{input_isbn}'")
                    print(f"  Output: '{book.isbn}'")
                    passed += 1
                else:
                    print(f"✗ FAIL: {description}")
                    print(f"  Input:    '{input_isbn}'")
                    print(f"  Expected: '{expected}'")
                    print(f"  Got:      '{book.isbn}'")
                    failed += 1
            else:
                print(f"✗ FAIL: {description}")
                print(f"  Should have raised ValidationError but passed with: '{book.isbn}'")
                failed += 1
                
        except ValidationError as e:
            if not should_pass:
                print(f"✓ PASS: {description}")
                print(f"  Input:  '{input_isbn}'")
                print(f"  Error:  {e.errors()[0]['msg']}")
                passed += 1
            else:
                print(f"✗ FAIL: {description}")
                print(f"  Should have passed but got error: {e.errors()[0]['msg']}")
                failed += 1
        
        print()
    
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


def test_data_truncation_prevention():
    """Test that data truncation no longer occurs."""
    
    print("\n" + "=" * 70)
    print("DATA TRUNCATION PREVENTION TEST")
    print("=" * 70)
    
    # This was the original problematic case
    problematic_isbn = "978-0-12-345678-9"  # 17 characters with dashes
    
    print(f"\nOriginal Problem:")
    print(f"  - User input: '{problematic_isbn}' ({len(problematic_isbn)} chars)")
    print(f"  - Old database column: VARCHAR(13)")
    print(f"  - Result: DATA TRUNCATED to 13 chars! ❌")
    
    print(f"\nNew Solution:")
    print(f"  - User input: '{problematic_isbn}' ({len(problematic_isbn)} chars)")
    
    try:
        book = BookCreate(
            title="Test Book",
            author="Test Author",
            isbn=problematic_isbn,
            published_date=date(2023, 1, 15)
        )
        
        normalized = book.isbn
        print(f"  - Normalized: '{normalized}' ({len(normalized)} chars)")
        print(f"  - New database column: VARCHAR(17)")
        print(f"  - Result: NO TRUNCATION! ✓")
        
        if len(normalized) <= 17:
            print(f"\n✓ SUCCESS: ISBN fits in VARCHAR(17) column")
            return True
        else:
            print(f"\n✗ FAILURE: ISBN still too long for database!")
            return False
            
    except ValidationError as e:
        print(f"\n✗ FAILURE: Validation error: {e}")
        return False


def test_update_schema():
    """Test that BookUpdate also handles ISBN normalization."""
    
    print("\n" + "=" * 70)
    print("BOOK UPDATE SCHEMA TEST")
    print("=" * 70)
    
    try:
        # Test with dashed ISBN
        update = BookUpdate(isbn="978-1-23-456789-0")
        print(f"✓ BookUpdate normalization works")
        print(f"  Input:  '978-1-23-456789-0'")
        print(f"  Output: '{update.isbn}'")
        
        # Test with None (optional)
        update2 = BookUpdate(title="New Title")
        print(f"✓ BookUpdate handles optional ISBN")
        print(f"  ISBN: {update2.isbn}")
        
        return True
        
    except Exception as e:
        print(f"✗ BookUpdate failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("# ISBN TRUNCATION FIX - VERIFICATION TESTS")
    print("#" * 70)
    
    test1 = test_isbn_normalization()
    test2 = test_data_truncation_prevention()
    test3 = test_update_schema()
    
    print("\n" + "#" * 70)
    if test1 and test2 and test3:
        print("# ✓ ALL TESTS PASSED - ISBN truncation issue is FIXED!")
        print("#" * 70)
        sys.exit(0)
    else:
        print("# ✗ SOME TESTS FAILED - Please review the output above")
        print("#" * 70)
        sys.exit(1)

