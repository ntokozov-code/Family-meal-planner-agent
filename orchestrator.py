"""
orchestrator.py - Multi-Agent Architecture with Strategic Model Routing and Human-in-the-Loop stops.
"""
import os
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai
from google.genai import types

from tools import check_allergen_compliance, categorize_grocery_list
from observability import log_event, start_span

# -------------------------------------------------------------
# Strategic Model Routing: Directs tasks by complexity & cost
# -------------------------------------------------------------
def route_model(task_complexity: str) -> str:
    """
    Routes complex meal reasoning to Pro and fast safety/formatting to Flash.
    """
    if task_complexity == "high_reasoning_planning":
        return "gemini-2.5-pro"  # High capability tier for multi-constraint planning
    return "gemini-2.5-flash"     # Low latency tier for safety audits and classification

# -------------------------------------------------------------
# Multi-Agent Pattern: Specialized Collaborative Agents
# -------------------------------------------------------------
class DietitianAgent:
    """Specialized Agent: Generates balanced 5-day dinner meal plans."""
    def __init__(self, client: genai.Client):
        self.client = client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=8))
    def draft_plan(self, family_size: int, cook_time: int, cuisine_preferences: List[str]) -> str:
        model_name = route_model("high_reasoning_planning")
        prompt = (
            f"Draft a healthy 5-day dinner plan for a family of {family_size}. "
            f"Max cook time: {cook_time} mins. Preferred cuisines: {cuisine_preferences}."
        )
        response = self.client.models.generate_content(model=model_name, contents=prompt)
        return response.text

class SafetyAuditorAgent:
    """Specialized Agent: Audits meal plans against severe allergen lists."""
    def audit(self, ingredients: List[str], allergens: List[str]) -> Dict[str, Any]:
        return check_allergen_compliance(ingredients=ingredients, known_allergens=allergens)

class GroceryAgent:
    """Specialized Agent: Transforms approved recipes into categorized shopping lists."""
    def build_list(self, raw_items: List[str]) -> Dict[str, Any]:
        return categorize_grocery_list(items=raw_items)

# -------------------------------------------------------------
# Master Orchestrator with Human-in-the-Loop (HITL) Stop
# -------------------------------------------------------------
class MealAgentOrchestrator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.dietitian = DietitianAgent(self.client) if self.client else None
        self.safety_auditor = SafetyAuditorAgent()
        self.grocery_agent = GroceryAgent()

    def run_workflow(
        self, 
        preferences: Dict[str, Any], 
        parent_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Multi-agent pipeline with explicit Human-in-the-Loop (HITL) confirmation stop.
        """
        with start_span("meal_planning_orchestration") as span:
            trace_id = hex(span.get_span_context().trace_id) if hasattr(span, "get_span_context") else "trace_001"
            log_event("workflow_started", trace_id, intent="multi_agent_meal_planning", metadata=preferences)

            # Step 1: Dietitian Agent drafts plan
            raw_plan = self.dietitian.draft_plan(
                family_size=preferences.get("size", 4),
                cook_time=preferences.get("time_limit", 30),
                cuisine_preferences=preferences.get("cuisines", ["Kid-Friendly"])
            ) if self.dietitian else "Mock 5-Day Plan"

            # Step 2: Safety Auditor Agent verifies allergen compliance
            allergens = preferences.get("allergies", "").split(",")
            safety_report = self.safety_auditor.audit(ingredients=[raw_plan], allergens=allergens)

            # Step 3: Explicit Human-in-the-Loop (HITL) Confirmation Check
            if not parent_approved:
                log_event("hitl_stop_triggered", trace_id, intent="parent_review", outcome="AWAITING_APPROVAL")
                return {
                    "status": "PENDING_HUMAN_APPROVAL",
                    "human_in_the_loop_required": True,
                    "message": "Plan generated and safety audited. Requires parent approval before generating grocery order.",
                    "meal_plan": raw_plan,
                    "safety_report": safety_report
                }

            # Step 4: Grocery Agent compiles list only after Human Confirmation
            grocery_list = self.grocery_agent.build_list(["chicken", "rice", "broccoli", "olive oil"])
            log_event("workflow_completed", trace_id, intent="multi_agent_meal_planning", outcome="APPROVED_AND_FINALIZED")

            return {
                "status": "COMPLETED",
                "human_in_the_loop_required": False,
                "meal_plan": raw_plan,
                "grocery_list": grocery_list,
                "safety_report": safety_report
            }
