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
    model=OpenRouter(id="google/gemma-3-27b-it:free"),
    markdown=True,
    enable_agentic_memory=True,
)

clarification_agent = Agent(
    name="Clarification & Follow-Up Agent",
    role="Ask critical follow-up questions to clarify first aid scenarios and understand severity.",
    model=OpenRouter(id="google/gemini-2.0-flash-thinking-exp-1219:free"),
    markdown=True,
    enable_agentic_memory=True,
)

procedure_agent = Agent(
    name="Procedure Generation Agent",
    role="Generate step-by-step first aid procedures based on the clarified scenario, prioritizing safety and proper medical protocol.",
    model=OpenRouter(id="google/gemini-2.5-pro-exp-03-25:free"),
    markdown=True,
    enable_agentic_memory=True,
)

web_agent = Agent(
    name="Web Resource Agent",
    role="Provide useful URLs (especially YouTube videos) for related first aid information and reputable medical sources.",
    model=OpenRouter(id="google/gemini-2.0-flash-exp:free"),
    tools=[DuckDuckGoTools()],
    show_tool_calls=True,
    markdown=True,
    enable_agentic_memory=True,
)

# --- Orchestrator using Agno Team ---
orchestrator = Team(
    name="First Aid Orchestrator",
    mode="sequential",
    model=OpenRouter(id="google/gemini-2.5-pro-exp-03-25:free"),
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
    show_members_responses=True,  # Show each agent's contribution
)

# Custom CSS for better UI
st.markdown("""
<style>
.chat-message {
    padding: 1.5rem; 
    border-radius: 0.5rem; 
    margin-bottom: 1rem; 
    display: flex;
    align-items: flex-start;
}
.chat-message.user {
    background-color: #2b313e;
}
.chat-message.assistant {
    background-color: #475063;
}
.chat-message .avatar {
    width: 20%;
}
.chat-message .avatar img {
    max-width: 78px;
    max-height: 78px;
    border-radius: 50%;
    object-fit: cover;
}
.chat-message .message {
    width: 80%;
    padding-left: 1rem;
}
.stApp {
    background-color: #1a1c24;
}
</style>
""", unsafe_allow_html=True)

# App Header
st.title("First Aid Multi-Agent Assistant 🚑")
st.markdown("#### Upload an image and/or describe your situation to get immediate first aid guidance")

# Sidebar for conversation history
with st.sidebar:
    st.title("Conversation History")
    clear_button = st.button("Clear Conversation")
    
    if clear_button:
        st.session_state.messages = []
        st.session_state.conversation_id = None
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input area
uploaded_file = st.file_uploader("Upload an image of the injury (optional)", type=["jpg", "jpeg", "png"])
user_input = st.chat_input("Describe your situation (e.g., 'I cut my finger and it's bleeding heavily')")

# Process the input and generate a response
if user_input:
    # Display user message
    st.chat_message("user").markdown(user_input)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Create the prompt
    prompt = f"Description: {user_input}"
    
    # If image is uploaded, process it and add to the prompt
    if uploaded_file:
        image_bytes = uploaded_file.read()
        image_b64 = base64.b64encode(image_bytes).decode()
        prompt += f"\nImage (base64): {image_b64}"
        
        # Display uploaded image in smaller format
        st.image(image_bytes, caption="Uploaded Image", width=300)
    
    # Create assistant message placeholder
    assistant_placeholder = st.chat_message("assistant")
    
    message_placeholder = assistant_placeholder.empty()
    message_placeholder.markdown("Analyzing your situation...")
    
    full_response = ""
    
    # Run the orchestrator with streaming
    with st.spinner("Processing..."):
        for chunk in orchestrator.run(prompt, conversation_id=st.session_state.conversation_id, stream=True):
            if hasattr(chunk, 'content'):
                full_response += chunk.content
            else:
                full_response += str(chunk)
            
            message_placeholder.markdown(full_response + "▌")
        
        # Save conversation ID for future messages
        if st.session_state.conversation_id is None and hasattr(orchestrator, "last_conversation_id"):
            st.session_state.conversation_id = orchestrator.last_conversation_id
    
    # Final update without the blinking cursor
    message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response}) 