# New file
import os
import base64
import streamlit as st
from agno.agent import Agent
from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.models.openrouter import OpenRouter

# Set up page configuration
st.set_page_config(
    page_title="First Aid Assistant",
    page_icon="🚑",
    layout="wide"
)

# Configure OpenRouter as OpenAI-compatible
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENROUTER_API_KEY"))
os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

# --- Agent Definitions ---
image_agent = Agent(
    name="Image Analysis Agent",
    role="Analyze injuries in images and produce concise descriptions to help with first aid.",
    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
    markdown=True,
    enable_agentic_memory=True,
)

clarification_agent = Agent(
    name="Clarification & Follow-Up Agent",
    role="Ask critical follow-up questions to clarify first aid scenarios and understand severity.",
    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
    markdown=True,
    enable_agentic_memory=True,
)

procedure_agent = Agent(
    name="Procedure Generation Agent",
    role="Generate step-by-step first aid procedures based on the clarified scenario, prioritizing safety and proper medical protocol.",
    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
    markdown=True,
    enable_agentic_memory=True,
)

web_agent = Agent(
    name="Web Resource Agent",
    role="Provide useful URLs (especially YouTube videos) for related first aid information and reputable medical sources.",
    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True,
    enable_agentic_memory=True,
)

# --- Orchestrator using Agno Team ---
orchestrator = Team(
    name="First Aid Orchestrator",
    mode="sequential",
    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
    members=[image_agent, clarification_agent, procedure_agent, web_agent],
    instructions=[
        "Step through each agent in order:",
        "1. If an image is provided, have Image Analysis Agent describe it in detail.",
        "2. Have Clarification Agent ask follow-up questions if needed to better understand the situation.",
        "3. Have Procedure Generation Agent produce a step-by-step first aid guide based on all available information.",
        "4. Have Web Agent find and list relevant URLs for more detailed information.",
        "Output the final result in markdown with clear headings and formatting."
    ],
    markdown=True,
    enable_agentic_memory=True,
    enable_agentic_context=True,
    show_members_responses=True,  # Hide raw agent responses
    show_tool_calls=True,  # Hide tool calls
)