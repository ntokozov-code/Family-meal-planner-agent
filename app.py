import os
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Family Meal Concierge",
    page_icon="🍳",
    layout="wide"
)

# ---------------------------------------------------------
# Initialize Gemini Client
# ---------------------------------------------------------
# Checks environment variable first (for evaluators), then UI input
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.info("Please provide your Gemini API key in the sidebar to begin.")
    st.stop()

client = genai.Client(api_key=api_key)

# ---------------------------------------------------------
# Sidebar: Persistent Hard Constraints
# ---------------------------------------------------------
st.sidebar.title("👨‍👩‍👧‍👦 Family Profile")
st.sidebar.caption("Pinned constraints are strictly injected into every response.")

household_size = st.sidebar.number_input("Household Size (Portions)", min_value=1, max_value=12, value=4)
severe_allergies = st.sidebar.text_input("🚨 Severe Allergies (Hard Block)", placeholder="e.g., Peanuts, Shellfish, Gluten")
time_limit = st.sidebar.slider("Max Weeknight Cook Time (minutes)", min_value=15, max_value=90, value=35, step=5)
dietary_style = st.sidebar.multiselect(
    "Preferences / Diet",
    ["Kid-Friendly", "Low Carb", "Vegetarian", "Dairy-Free", "Mediterranean", "Budget-Friendly"],
    default=["Kid-Friendly"]
)

if st.sidebar.button("Clear Conversation"):
    st.session_state.chat = None
    st.session_state.messages = []
    st.rerun()

# ---------------------------------------------------------
# System Instructions
# ---------------------------------------------------------
SYSTEM_INSTRUCTION = f"""
You are a Family Meal Planning Concierge Agent. Your role is to help busy parents create healthy, personalized weekly meal plans and grocery lists while strictly adhering to family preferences and dietary constraints.

CURRENT PINNED PROFILE CONSTRAINTS:
- Household Size: {household_size} people
- SEVERE ALLERGIES: {severe_allergies if severe_allergies else "None explicitly entered in sidebar (ask if unknown)"}
- Max Weeknight Cook Time: {time_limit} minutes
- Dietary Preferences: {", ".join(dietary_style) if dietary_style else "None specified"}

Core Responsibilities:
1. GATHER MISSING DETAILS: If essential preferences (allergies, household size, cuisines) are not in the profile or prior chat, politely ask before drafting a full plan.
2. 5-DAY MEAL PLAN: Provide a structured dinner plan (Monday to Friday). Each meal must include:
   - Recipe Name & Prep/Cook Time (must respect the {time_limit} min limit).
   - Brief 2-3 step instructions.
   - Core ingredients.
3. CATEGORIZED GROCERY LIST: Organize all ingredients into clear sections:
   - [Produce]
   - [Meat & Seafood / Plant Proteins]
   - [Dairy & Refrigerated]
   - [Pantry, Grains & Canned Goods]
   - [Spices & Condiments]
4. HARD SAFETY CONSTRAINT: NEVER suggest any recipe, condiment, or ingredient containing known user allergens ({severe_allergies}). Watch out for hidden ingredients (e.g., soy sauce, dressings, broths). If unsure, specify a safe alternative.
"""

# ---------------------------------------------------------
# Session State & Chat Setup
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state or st.session_state.chat is None:
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.4,
        )
    )

# ---------------------------------------------------------
# UI Header & Conversation History
# ---------------------------------------------------------
st.title("🍳 Family Meal Planning Concierge")
st.write("Plan weeknight dinners in minutes, respect family diets, and generate ready-to-shop grocery lists.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.messages:
    welcome_msg = (
        f"Hi there! I'm your meal planning concierge. I'm ready to build a 5-day dinner plan "
        f"for a family of **{household_size}** (max **{time_limit} mins** per meal)."
    )
    if severe_allergies:
        welcome_msg += f"\n\nI have noted strict safety exclusions for: **{severe_allergies}**."
    else:
        welcome_msg += "\n\nBefore we begin, **does anyone have severe food allergies or intolerances?**"
        
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
    with st.chat_message("assistant"):
        st.markdown(welcome_msg)

# ---------------------------------------------------------
# User Input & Streaming Response
# ---------------------------------------------------------
user_prompt = st.chat_input("Tell me what you're craving, or ask to generate this week's plan...")

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        def response_stream():
            response = st.session_state.chat.send_message_stream(user_prompt)
            for chunk in response:
                yield chunk.text

        full_response = st.write_stream(response_stream)

    st.session_state.messages.append({"role": "assistant", "content": full_response})