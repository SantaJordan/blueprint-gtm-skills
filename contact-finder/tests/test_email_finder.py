"""
Test script for Email Finder with MillionVerifier integration
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.discovery.email_permutator import (
    generate_email_permutations,
    parse_name,
    is_valid_for_permutation,
    split_name
)
from modules.discovery.email_finder import EmailFinder, find_email_for_contact
from modules.validation.million_verifier import MillionVerifierClient, verify_email_quick


def test_name_parsing():
    """Test name parsing and validation"""
    print("\n=== Testing Name Parsing ===\n")

    test_cases = [
        ("John Smith", True),
        ("John", True),  # Single name still valid
        ("Dr. John Smith Jr.", True),  # With prefix/suffix
        ("J Smith", False),  # Single initial too short
        ("ABC Corp LLC", False),  # Company name
        ("Mike's Plumbing Inc", False),  # Company indicator
        ("José García", True),  # Unicode characters
        ("", False),  # Empty
        ("123 Business", False),  # Contains numbers
    ]

    for name, expected_valid in test_cases:
        is_valid, reason = is_valid_for_permutation(name)
        status = "PASS" if is_valid == expected_valid else "FAIL"
        reason_str = f" ({reason})" if reason else ""
        print(f"  [{status}] '{name}' -> valid={is_valid}{reason_str}")

    # Test split_name
    print("\n  Split Name Tests:")
    split_cases = [
        ("John Smith", ("John", "Smith")),
        ("Dr. John Smith Jr.", ("John", "Smith")),
        ("John", ("John", None)),
        ("John David Smith", ("John", "Smith")),  # Uses last word as last name
    ]

    for full_name, expected in split_cases:
        first, last = split_name(full_name)
        status = "PASS" if (first, last) == expected else "FAIL"
        print(f"  [{status}] '{full_name}' -> first='{first}', last='{last}'")


def test_permutation_generation():
    """Test email permutation generation"""
    print("\n=== Testing Email Permutations ===\n")

    test_cases = [
        ("John Smith", "example.com", 8),
        ("John", "example.com", 1),  # Only firstname@
        ("María García", "test.io", 8),  # Unicode -> ASCII
        ("ABC Corp LLC", "company.com", 0),  # Company name rejected
    ]

    for name, domain, expected_count in test_cases:
        permutations = generate_email_permutations(name, domain)
        status = "PASS" if len(permutations) == expected_count else "FAIL"
        print(f"  [{status}] '{name}' @ {domain} -> {len(permutations)} permutations")
        if permutations:
            print(f"          {permutations[:3]}{'...' if len(permutations) > 3 else ''}")


async def test_million_verifier():
    """Test MillionVerifier API (requires API key)"""
    print("\n=== Testing MillionVerifier API ===\n")

    api_key = os.environ.get("MILLIONVERIFIER_API_KEY")
    if not api_key:
        print("  SKIPPED: MILLIONVERIFIER_API_KEY not set")
        return

    # Test with demo key patterns
    test_emails = [
        ("test@gmail.com", "Should work - common domain"),
        ("invalid@thisdoesnotexist12345.com", "Should be invalid - fake domain"),
        ("info@google.com", "Role account at major company"),
    ]

    client = MillionVerifierClient(api_key=api_key, max_concurrent=5)

    try:
        # Check credits first
        credits = await client.get_credits()
        print(f"  Credits available: {credits:,}")

        for email, description in test_emails:
            result = await client.verify_email(email)
            print(f"\n  {email} ({description})")
            print(f"    Result: {result.result.value}")
            print(f"    Quality: {result.quality.value}")
            print(f"    Confidence: {result.confidence_score}")
            print(f"    Free: {result.is_free}, Role: {result.is_role}")
            if result.did_you_mean:
                print(f"    Did you mean: {result.did_you_mean}")
            if result.error:
                print(f"    Error: {result.error}")

    finally:
        await client.close()


async def test_email_finder():
    """Test full EmailFinder flow (requires API key)"""
    print("\n=== Testing EmailFinder ===\n")

    api_key = os.environ.get("MILLIONVERIFIER_API_KEY")
    if not api_key:
        print("  SKIPPED: MILLIONVERIFIER_API_KEY not set")
        return

    test_cases = [
        ("Sundar Pichai", "google.com", None),  # Real person, big company
        ("Test Person", "example.com", "test@example.com"),  # With existing email
    ]

    finder = EmailFinder(million_verifier_api_key=api_key)

    try:
        for name, domain, existing in test_cases:
            print(f"\n  Searching: {name} @ {domain}")
            if existing:
                print(f"    Existing email: {existing}")

            result = await finder.find_email(
                full_name=name,
                domain=domain,
                existing_emails=[existing] if existing else None
            )

            print(f"    Name parsed: valid={result.name_components.is_valid if result.name_components else 'N/A'}")
            print(f"    Permutations generated: {result.permutations_generated}")
            print(f"    Total verifications: {result.total_verifications}")
            print(f"    Credits used: {result.credits_used}")

            if result.found_valid_email:
                print(f"    FOUND: {result.best_email}")
                print(f"    Result: {result.best_result_type}")
                print(f"    Confidence: {result.best_confidence}")
            else:
                print(f"    No valid email found")

            # Show checked candidates
            if result.candidates_checked:
                print(f"    Candidates checked:")
                for c in result.candidates_checked[:5]:
                    if c.verification:
                        print(f"      - {c.email}: {c.result_type} (conf={c.confidence})")

    finally:
        await finder.close()
        print(f"\n  Total credits used: {finder.credits_used}")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Email Finder Test Suite")
    print("=" * 60)

    # Unit tests (no API needed)
    test_name_parsing()
    test_permutation_generation()

    # Integration tests (need API key)
    await test_million_verifier()
    await test_email_finder()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
