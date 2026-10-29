"""
tools.py - Agent Tools with explicit Pydantic JSON Schemas, typing, and guided recovery.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field

# --- Explicit Pydantic JSON Schemas ---
class AllergenCheckInput(BaseModel):
    ingredients: List[str] = Field(..., description="List of proposed ingredients in the meal plan.")
    known_allergens: List[str] = Field(..., description="Severe family allergens to block.")

class AllergenViolation(BaseModel):
    allergen: str
    found_in: str

class AllergenCheckOutput(BaseModel):
    status: str
    is_safe: bool
    violations: List[AllergenViolation]
    remediation_guidance: str

class GroceryCategorizeInput(BaseModel):
    items: List[str] = Field(..., description="Raw grocery items needed for dinner recipes.")

class GroceryCategorizeOutput(BaseModel):
    status: str
    categorized_items: Dict[str, List[str]]
    total_items: int

# OpenAPI / JSON Schema exports
ALLERGEN_TOOL_SCHEMA = AllergenCheckInput.model_json_schema()
GROCERY_TOOL_SCHEMA = GroceryCategorizeInput.model_json_schema()

def check_allergen_compliance(ingredients: List[str], known_allergens: List[str]) -> Dict[str, Any]:
    """Validates ingredients against known severe allergens with stem and plural awareness."""
    try:
        validated_input = AllergenCheckInput(ingredients=ingredients, known_allergens=known_allergens)
        detected = []
        for allergen in validated_input.known_allergens:
            allergen_clean = allergen.strip().lower()
            if not allergen_clean:
                continue
            # Check both full word and singular stem (e.g. "peanuts" -> "peanut")
            stem = allergen_clean.rstrip("s")
            for item in validated_input.ingredients:
                item_lower = item.lower()
                if allergen_clean in item_lower or (len(stem) > 3 and stem in item_lower):
                    detected.append(AllergenViolation(allergen=allergen, found_in=item))

        result = AllergenCheckOutput(
            status="success",
            is_safe=len(detected) == 0,
            violations=detected,
            remediation_guidance="Replace flagged items with allergy-safe substitutes." if detected else "All ingredients safe."
        )
        return result.model_dump()
    except Exception as e:
        return {
            "status": "error",
            "is_safe": False,
            "violations": [],
            "remediation_guidance": f"Schema validation error: {str(e)}. Provide lists of strings."
        }

def categorize_grocery_list(items: List[str]) -> Dict[str, Any]:
    """Categorizes ingredients by store department using Pydantic validation."""
    try:
        validated = GroceryCategorizeInput(items=items)
        categories = {
            "Produce": [], "Meat & Seafood": [], "Dairy & Refrigerated": [], 
            "Pantry & Grains": [], "Spices & Condiments": []
        }
        keywords = {
            "Produce": ["apple", "onion", "garlic", "spinach", "potato", "carrot", "herb", "lemon", "vegetable"],
            "Meat & Seafood": ["chicken", "beef", "pork", "salmon", "turkey", "shrimp"],
            "Dairy & Refrigerated": ["milk", "cheese", "butter", "yogurt", "cream", "egg"],
            "Pantry & Grains": ["rice", "pasta", "flour", "beans", "broth", "oil", "oats"],
        }
        for item in validated.items:
            item_lower = item.lower()
            assigned = False
            for cat, words in keywords.items():
                if any(w in item_lower for w in words):
                    categories[cat].append(item)
                    assigned = True
                    break
            if not assigned:
                categories["Spices & Condiments"].append(item)

        output = GroceryCategorizeOutput(
            status="success",
            categorized_items=categories,
            total_items=len(validated.items)
        )
        return output.model_dump()
    except Exception as e:
        return {"status": "error", "message": str(e), "remediation_guidance": "Input must be a list of strings."}
