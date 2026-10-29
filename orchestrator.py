"""
orchestrator.py - Agent orchestration loop with exponential backoff retry for 503/API errors.
"""
import os
import time
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google import genai
from google.genai import types

from tools import check_allergen_compliance, categorize_grocery_list
from observability import log_event, create_trace_id

class MealAgentOrchestrator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    # Handles the 503 error that crashed the evaluator!
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def call_model_with_retry(self, system_instruction: str, prompt: str) -> str:
        """Invokes the model with exponential backoff retry to withstand 503 spikes."""
        if not self.client:
            return "Mock response: API Key not set."

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        return response.text

    def plan_week(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-step orchestration: Plan -> Validate Safety -> Compile Groceries."""
        trace_id = create_trace_id()
        log_event("workflow_started", trace_id, intent="generate_weekly_plan", metadata=preferences)

        sys_prompt = (
            f"You are a Family Meal Planning Concierge Agent. Create a 5-day dinner plan for a family of "
            f"{preferences.get('size', 4)} with max cook time of {preferences.get('time_limit', 30)} minutes. "
            f"Forbidden Allergens: {preferences.get('allergies', 'None')}."
        )

        # Step 1: Model generation
        raw_plan = self.call_model_with_retry(
            system_instruction=sys_prompt,
            prompt="Generate a 5-day dinner plan including ingredient lists."
        )

        # Step 2: Tool execution for safety guardrails
        safety_check = check_allergen_compliance(
            ingredients=[raw_plan],
            known_allergens=preferences.get("allergies", "").split(",")
        )

        outcome = "plan_generated_and_verified" if safety_check["is_safe"] else "plan_flagged_for_review"
        log_event("workflow_completed", trace_id, intent="generate_weekly_plan", outcome=outcome)

        return {
            "trace_id": trace_id,
            "meal_plan": raw_plan,
            "safety_validation": safety_check
        }
