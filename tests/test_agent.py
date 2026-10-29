"""Unit tests to verify tools, observability, and safety verification."""
import pytest
from tools import check_allergen_compliance, categorize_grocery_list
from observability import redact_pii

def test_allergen_detection():
    ingredients = ["peanut butter", "bread", "jelly"]
    allergens = ["peanuts", "tree nuts"]
    res = check_allergen_compliance(ingredients, allergens)
    assert res["is_safe"] is False
    assert len(res["violations"]) > 0

def test_safe_ingredients():
    ingredients = ["chicken breast", "broccoli", "olive oil"]
    allergens = ["peanuts", "shellfish"]
    res = check_allergen_compliance(ingredients, allergens)
    assert res["is_safe"] is True
    assert len(res["violations"]) == 0

def test_grocery_categorization():
    items = ["fresh apples", "chicken breast", "whole milk", "olive oil"]
    res = categorize_grocery_list(items)
    assert res["status"] == "success"
    assert len(res["categorized_items"]["Produce"]) > 0

def test_pii_redaction():
    text = "Contact the parent at parent@example.com or 555-123-4567."
    redacted = redact_pii(text)
    assert "parent@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
