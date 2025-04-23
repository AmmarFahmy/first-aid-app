import streamlit as st
from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools
import tempfile
import os
from PIL import Image
import io
import base64
from agno.media import Image as AgnoImage
from pathlib import Path

def init_session_state():
    """Initialize session state variables"""
    if 'openrouter_api_key' not in st.session_state:
        st.session_state.openrouter_api_key = None
    if 'first_aid_team' not in st.session_state:
        st.session_state.first_aid_team = None
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'processed_image' not in st.session_state:
        st.session_state.processed_image = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'conversation_context' not in st.session_state:
        st.session_state.conversation_context = ""

def process_image(uploaded_file):
    """Process an image into AgnoImage format for use with models"""
    try:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"temp_{uploaded_file.name}")
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        agno_image = AgnoImage(filepath=Path(temp_path))
        return agno_image
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="First Aid Assistant", layout="wide")
    init_session_state()

    st.title("First Aid Virtual Assistant 🚑")

    with st.sidebar:
        st.header("🔑 API Configuration")
   
        openrouter_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=st.session_state.openrouter_api_key if st.session_state.openrouter_api_key else "",
            help="Enter your OpenRouter API key"
        )
        if openrouter_key:
            st.session_state.openrouter_api_key = openrouter_key

        st.divider()

        if st.session_state.openrouter_api_key:
            # Add image upload section
            st.header("📷 Image Upload (Optional)")
            uploaded_image = st.file_uploader("Upload an image of the injury/condition", type=['jpg', 'jpeg', 'png'])
            if uploaded_image:
                # Store the image in session state
                image_bytes = uploaded_image.getvalue()
                st.session_state.uploaded_image = image_bytes
                # Process the image for Gemini model
                st.session_state.processed_image = process_image(uploaded_image)
                # Display the image
                image = Image.open(io.BytesIO(image_bytes))
                st.image(image, caption="Uploaded Image", width=200)
            
            if st.button("Clear Image"):
                st.session_state.uploaded_image = None
                st.session_state.processed_image = None
                st.rerun()
                
            if st.button("Reset Conversation"):
                st.session_state.chat_history = []
                st.session_state.conversation_context = ""
                st.rerun()

            st.divider()
            st.header("🔍 Assistance Options")
            assistance_type = st.selectbox(
                "Select Assistance Type",
                [
                    "Injury Assessment",
                    "First Aid Procedure",
                    "Emergency Response",
                    # "CPR Instructions",
                    "Custom Query"
                ]
            )
        else:
            st.warning("Please enter your OpenRouter API key to proceed")

    # Main content area
    if not st.session_state.openrouter_api_key:
        st.info("👈 Please configure your API key in the sidebar to begin")
    else:
        # Initialize the agents if they haven't been created yet
        if not st.session_state.first_aid_team:
            try:
                # Set the OpenRouter API key
                os.environ['OPENROUTER_API_KEY'] = st.session_state.openrouter_api_key
                
                # Initialize agents with Gemini models via OpenRouter
                image_agent = Agent(
                    name="Image Analyzer",
                    role="Medical image analysis specialist",
                    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
                    instructions=[
                        "Analyze uploaded injury/medical images",
                        "Identify visible symptoms and conditions",
                        "Be careful not to make definitive diagnosis",
                        "Focus on observable features only"
                    ],
                    markdown=True,
                    debug_mode=True
                )

                clarification_agent = Agent(
                    name="Clarification Specialist",
                    role="Medical clarification specialist",
                    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
                    instructions=[
                        "Ask relevant follow-up questions to clarify the situation",
                        "Focus on getting critical information for proper first aid",
                        "Ask about symptoms, severity, time since injury, allergies, etc.",
                        "Be compassionate but direct to get important information quickly"
                    ],
                    markdown=True,
                    debug_mode=True
                )

                procedure_agent = Agent(
                    name="First Aid Procedure Specialist", 
                    role="First aid procedure specialist",
                    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
                    instructions=[
                        "Provide clear step-by-step first aid instructions",
                        "Always include when to seek professional medical help",
                        "Reference standard first aid procedures",
                        "Include safety precautions and what NOT to do"
                    ],
                    markdown=True,
                    debug_mode=True
                )
                
                web_agent = Agent(
                    name="Medical Information Researcher",
                    role="Medical information researcher",
                    model=OpenRouter(id="google/gemini-2.0-flash-lite-001"),
                    tools=[DuckDuckGoTools()],
                    instructions=[
                        "Search for up-to-date medical information when needed",
                        "Provide references to authoritative medical sources",
                        "Focus on first aid procedures and emergency response protocols",
                        "Verify information from multiple sources when possible"
                    ],
                    show_tool_calls=True,
                    markdown=True,
                    debug_mode=True
                )

                # First Aid Team Orchestrator
                st.session_state.first_aid_team = Agent(
                    name="First Aid Coordinator",
                    role="First aid team coordinator",
                    model=OpenRouter(id="google/gemini-2.0-flash-001"),
                    team=[image_agent, clarification_agent, procedure_agent, web_agent],
                    instructions=[
                        "Coordinate analysis between team members",
                        "Prioritize immediate, life-saving information first",
                        "Ensure all recommendations follow standard first aid protocols",
                        "Include warnings about when to seek professional medical help",
                        "Present all team member interactions clearly in your response",
                        "Always include the full text of questions from the Clarification Specialist"
                    ],
                    show_tool_calls=True,
                    markdown=True,
                    debug_mode=True
                )
                
                st.success("✅ First aid assistant initialized!")
                
            except Exception as e:
                st.error(f"Error initializing agents: {str(e)}")

        # Create a dictionary for assistance type icons
        assistance_icons = {
            "Injury Assessment": "🔍",
            "First Aid Procedure": "📋",
            "Emergency Response": "🚨",
            # "CPR Instructions": "❤️",
            "Custom Query": "💭"
        }

        # Dynamic header with icon
        assistance_type = st.session_state.get('assistance_type', "Injury Assessment")
        st.header(f"{assistance_icons[assistance_type]} {assistance_type}")
  
        assistance_configs = {
            "Injury Assessment": {
                "query": "Assess this injury/situation and provide initial recommendations.",
                "agents": ["Image Analyzer", "Clarification Specialist", "First Aid Procedure Specialist"],
                "description": "Analysis of the injury/situation with follow-up questions for proper assessment"
            },
            "First Aid Procedure": {
                "query": "Provide detailed first aid procedure for this situation.",
                "agents": ["Clarification Specialist", "First Aid Procedure Specialist"],
                "description": "Step-by-step first aid instructions with clarifying questions"
            },
            "Emergency Response": {
                "query": "Provide emergency response steps for this situation.",
                "agents": ["Clarification Specialist", "First Aid Procedure Specialist", "Medical Information Researcher"],
                "description": "Urgent response guidance with up-to-date protocols"
            },
            # "CPR Instructions": {
            #     "query": "Provide current CPR instructions and guidelines.",
            #     "agents": ["First Aid Procedure Specialist", "Medical Information Researcher"],
            #     "description": "Comprehensive CPR guidance based on latest protocols"
            # },
            "Custom Query": {
                "query": None,
                "agents": ["Image Analyzer", "Clarification Specialist", "First Aid Procedure Specialist", "Medical Information Researcher"],
                "description": "Custom first aid assistance using all available agents"
            }
        }

        st.info(f"📋 {assistance_configs[assistance_type]['description']}")
        st.write(f"🤖 Active First Aid AI Agents: {', '.join(assistance_configs[assistance_type]['agents'])}")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").markdown(message["content"])
        
        # User input section - using st.chat_input for better UX
        user_query = st.chat_input("Describe the situation or injury...")
        
        if user_query:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            
            # Display user message
            st.chat_message("user").write(user_query)
            
            # Create assistant response placeholder
            with st.chat_message("assistant"):
                with st.spinner("Analyzing situation..."):
                    try:
                        # Ensure OpenRouter API key is set
                        os.environ['OPENROUTER_API_KEY'] = st.session_state.openrouter_api_key
                        
                        # Update conversation context with the new query
                        if st.session_state.conversation_context:
                            st.session_state.conversation_context += f"\n\nUser: {user_query}"
                        else:
                            st.session_state.conversation_context = f"User: {user_query}"
                        
                        # Prepare query with conversation context
                        if assistance_type != "Custom Query":
                            message_text = f"""
                            Previous conversation:
                            {st.session_state.conversation_context}
                            
                            Primary Assistance Task: {assistance_configs[assistance_type]['query']}
                            Focus Areas: {', '.join(assistance_configs[assistance_type]['agents'])}
                            
                            Please provide appropriate first aid guidance.
                            Always include when to seek professional medical help.
                            """
                        else:
                            message_text = f"""
                            Previous conversation:
                            {st.session_state.conversation_context}
                            
                            Please provide appropriate first aid assistance.
                            Focus Areas: {', '.join(assistance_configs[assistance_type]['agents'])}
                            
                            Always include when to seek professional medical help.
                            """

                        # Run the agent with or without image
                        if st.session_state.processed_image and "Image Analyzer" in assistance_configs[assistance_type]['agents']:
                            # Run with image
                            response = st.session_state.first_aid_team.run(
                                message=message_text,
                                images=[st.session_state.processed_image]
                            )
                        else:
                            # Run without image
                            response = st.session_state.first_aid_team.run(message=message_text)
                        
                        # Use a single approach to extract content - instead of combining multiple approaches
                        # which can lead to duplication
                        if hasattr(response, 'messages') and response.messages:
                            # Get only the final assistant message which should contain all content
                            assistant_messages = [msg.content for msg in response.messages if msg.role == 'assistant' and msg.content]
                            if assistant_messages:
                                content = assistant_messages[-1]  # Get the last assistant message
                            else:
                                content = response.content or "I don't have a specific recommendation at this time."
                        else:
                            content = response.content or "I don't have a specific recommendation at this time."
                            
                        # Update conversation context with assistant's response
                        st.session_state.conversation_context += f"\n\nAssistant: {content}"
                        
                        # Display the AI response
                        st.markdown(content)
                        
                        # Add to chat history
                        st.session_state.chat_history.append({"role": "assistant", "content": content})
                        
                        # Add disclaimer at the bottom
                        st.warning("⚠️ DISCLAIMER: This is AI-generated first aid guidance and not a substitute for professional medical advice. In case of serious injury or medical emergency, call emergency services (110) immediately.")

                    except Exception as e:
                        error_msg = f"Error during analysis: {str(e)}"
                        st.error(error_msg)
                        # Add error to chat history
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main() 