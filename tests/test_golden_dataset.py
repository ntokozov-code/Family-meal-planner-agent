"""Automated Evaluation Suite running agent assertions against a golden test dataset."""
import json
import os
import pytest
from tools import check_allergen_compliance

def test_against_golden_dataset():
    golden_path = os.path.join(os.path.dirname(__file__), "..", "evals", "golden_dataset.json")
    with open(golden_path, "r") as f:
        dataset = json.load(f)

    for case in dataset:
        safe_sample = ["chicken breast", "broccoli", "brown rice", "olive oil"]
        res = check_allergen_compliance(safe_sample, case["allergens"])
        assert res["is_safe"] == case["expected_safety"]
        assert len(res["violations"]) == len(case["forbidden_detected"])
