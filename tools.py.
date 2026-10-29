"""
tools.py - Agent Tools with strict schemas, docstrings, and guided error handling.
"""
from typing import List, Dict, Any

def check_allergen_compliance(
    ingredients: List[str], 
    known_allergens: List[str]
) -> Dict[str, Any]:
    """
    Validates recipe ingredients against a family's list of severe allergens.

    Args:
        ingredients (List[str]): List of ingredients in the proposed meal.
        known_allergens (List[str]): Prohibited allergens (e.g., ['peanuts', 'shellfish', 'gluten']).

    Returns:
        Dict[str, Any]: Validation report with 'is_safe' boolean, detected violations, and guided remediation.
    """
    try:
        if not isinstance(ingredients, list) or not isinstance(known_allergens, list):
            raise TypeError("Both ingredients and known_allergens must be provided as lists of strings.")

        detected = []
        for allergen in known_allergens:
            allergen_clean = allergen.strip().lower()
            if not allergen_clean:
                continue
            for item in ingredients:
                if allergen_clean in item.lower():
                    detected.append({"allergen": allergen, "found_in": item})

        return {
            "status": "success",
            "is_safe": len(detected) == 0,
            "violations": detected,
            "remediation_guidance": "Substitute flagged ingredients with allergen-safe alternatives immediately." if detected else "All clear."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "remediation_guidance": "Ensure inputs are valid lists of ingredient strings."
        }


def categorize_grocery_list(items: List[str]) -> Dict[str, Any]:
    """
    Sorts a raw grocery list into store departments for efficient family shopping.

    Args:
        items (List[str]): List of raw grocery items (e.g., ['apples', 'chicken breasts', 'milk']).

    Returns:
        Dict[str, Any]: Categorized grocery list grouped by department.
    """
    try:
        categories: Dict[str, List[str]] = {
            "Produce": [],
            "Meat & Seafood": [],
            "Dairy & Refrigerated": [],
            "Pantry & Grains": [],
            "Spices & Condiments": []
        }

        keywords = {
            "Produce": ["apple", "onion", "garlic", "spinach", "potato", "carrot", "herb", "lemon", "vegetable", "lettuce", "tomato"],
            "Meat & Seafood": ["chicken", "beef", "pork", "salmon", "turkey", "fish", "shrimp", "steak"],
            "Dairy & Refrigerated": ["milk", "cheese", "butter", "yogurt", "cream", "egg", "tofu"],
            "Pantry & Grains": ["rice", "pasta", "flour", "beans", "broth", "oil", "oats", "canned"],
        }

        for item in items:
            item_lower = item.lower()
            assigned = False
            for cat, words in keywords.items():
                if any(w in item_lower for w in words):
                    categories[cat].append(item)
                    assigned = True
                    break
            if not assigned:
                categories["Spices & Condiments"].append(item)

        return {
            "status": "success",
            "categorized_items": categories,
            "total_items": len(items)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "remediation_guidance": "Provide grocery items as a valid list of strings."
        }
