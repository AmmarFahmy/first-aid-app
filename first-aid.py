import streamlit as st
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.openrouter import OpenRouter
from agno.tools.duckduckgo import DuckDuckGoTools
from typing import List, Optional
import logging
from agno.media import Image as AgnoImage
from pathlib import Path
import tempfile
import os
from pytube import Search

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def initialize_agents(api_key: str) -> tuple[Agent, Agent, Agent, Agent, Agent]:
    try:
        model = OpenRouter(id="google/gemini-2.0-flash-lite-001", api_key=api_key)
        
        image_agent = Agent(
            model=model,
            instructions=[
                "You are an image analysis expert that:",
                "1. Identifies injuries, symptoms, and medical conditions from images",
                "2. Provides visual diagnosis and recommendations",
                "3. Suggests immediate first aid measures",
                "Be specific and technical in your analysis"
            ],
            markdown=True
        )

        procedure_agent = Agent(
            model=model,
            instructions=[
                "You are a procedure expert that:",
                "1. Provides step-by-step first aid procedures",
                "2. Ensures safety and effectiveness of the procedures",
                "3. Adapts procedures to the user's specific situation",
                "4. Since the user are from Sri Lanka, the procedures should be considering the local conditions, like emergency services, hospitals, etc.",
                "5. Focus on accuracy and safety"
            ],
            markdown=True
        )

        web_agent = Agent(
            model=model,
            tools=[DuckDuckGoTools(search=True, news=False, fixed_max_results=5)],
            instructions=[
                "You are a web search expert that:",
                "1. Finds useful URLs related to the user's problem",
                "2. Don't use or search for YouTube videos for visual guidance",
                "3. Provides reliable and relevant information",
                "Focus on actionable web resources"
            ],
            markdown=True,
            debug_mode=True
        )

        orchestrator = Agent(
            model=model,
            instructions=[
                "You are the orchestrator that:",
                "1. Coordinates between different agents",
                "2. Ensures a seamless user experience",
                "3. Provides a comprehensive first aid solution",
                "Focus on integration and user satisfaction"
            ],
            markdown=True
        )
        
        return image_agent, procedure_agent, web_agent, orchestrator
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None, None, None, None, None

# Set page config and UI elements
st.set_page_config(page_title="Virtual First Aid Assistant", layout="wide")

# Sidebar for API key input
with st.sidebar:
    st.header("🔑 API Configuration")

    if "api_key_input" not in st.session_state:
        st.session_state.api_key_input = ""
        
    api_key = st.text_input(
        "Enter your OpenRouter API Key",
        value=st.session_state.api_key_input,
        type="password",
        help="Get your API key from OpenRouter",
        key="api_key_widget"  
    )

    if api_key != st.session_state.api_key_input:
        st.session_state.api_key_input = api_key
    
    if api_key:
        st.success("API Key provided! ✅")
    else:
        st.warning("Please enter your API key to proceed")
        st.markdown("""
        To get your API key:
        Go to [OpenRouter](https://openrouter.ai/settings/keys)
        """)

st.title("Virtual First Aid Assistant")

if st.session_state.api_key_input:
    image_agent, procedure_agent, web_agent, orchestrator = initialize_agents(st.session_state.api_key_input)
    
    if all([image_agent, procedure_agent, web_agent, orchestrator]):
        # File Upload Section
        st.header("📤 Upload Content")
        col1, space, col2 = st.columns([1, 0.1, 1])
        
        with col1:
            medical_images = st.file_uploader(
                "Upload Medical Images",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="medical_images"
            )
            
            if medical_images:
                for file in medical_images:
                    st.image(file, caption=file.name, use_container_width=True)

        # Analysis Configuration
        st.header("🎯 Analysis Configuration")

        context = st.text_area(
            "Describe the problem or symptoms",
            placeholder="Provide details about the medical issue or symptoms..."
        )

        # Analysis Process
        if st.button("🚀 Run Analysis", type="primary"):
            if medical_images:
                try:
                    st.header("📊 Analysis Results")
                    
                    def process_images(files):
                        processed_images = []
                        for file in files:
                            try:
                                temp_dir = tempfile.gettempdir()
                                temp_path = os.path.join(temp_dir, f"temp_{file.name}")
                                
                                with open(temp_path, "wb") as f:
                                    f.write(file.getvalue())
                                
                                agno_image = AgnoImage(filepath=Path(temp_path))
                                processed_images.append(agno_image)
                                
                            except Exception as e:
                                logger.error(f"Error processing image {file.name}: {str(e)}")
                                continue
                        return processed_images
                    
                    medical_images_processed = process_images(medical_images)
                    
                    # Image Analysis
                    with st.spinner("🔍 Analyzing images..."):
                        if medical_images_processed:
                            image_prompt = f"""
                            Analyze these medical images and provide insights.
                            Context: {context}
                            Provide specific insights about potential injuries or conditions.
                            
                            Please format your response with clear headers and bullet points.
                            Focus on concrete observations and actionable insights.
                            """
                            
                            response = image_agent.run(
                                message=image_prompt,
                                images=medical_images_processed
                            )
                            
                            st.subheader("🔍 Image Analysis")
                            st.markdown(response.content)
                    
                    # Procedure
                    with st.spinner("📝 Providing first aid procedures..."):
                        procedure_prompt = f"""
                        Provide step-by-step first aid procedures based on the analysis.
                        Context: {context}
                        Ensure safety and effectiveness of the procedures.
                        """
                        
                        response = procedure_agent.run(
                            message=procedure_prompt
                        )
                        
                        st.subheader("📝 First Aid Procedures")
                        st.markdown(response.content)
                    
                    # Web Resources
                    with st.spinner("🌐 Finding web resources..."):
                        web_prompt = f"""
                        Search the web for medical resources related to: {context if context else "first aid procedures"}
                        Use the duckduckgo_search tool to find reliable medical websites and articles.
                        Provide a list of 3-5 useful resources with brief descriptions.
                        Focus on first aid procedures from reputable medical sources.
                        """
                        
                        response = web_agent.run(
                            message=web_prompt
                        )
                        
                        st.subheader("🌐 Web Resources")
                        st.markdown(response.content)
                        
                        st.markdown("#### YouTube Videos")
                        s = Search(f"first aid videos for {context}")
                        for video in s.results[:3]:
                            print(video.title, video.watch_url)
                            st.markdown(f"{video.title} - {video.watch_url}")
                    
                except Exception as e:
                    logger.error(f"Error during analysis: {str(e)}")
                    st.error("An error occurred during analysis. Please check the logs for details.")
            else:
                st.warning("Please upload at least one medical image to analyze.")
    else:
        st.info("👈 Please enter your API key in the sidebar to get started")
else:
    st.info("👈 Please enter your API key in the sidebar to get started")

# Footer with usage tips
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <h4>Tips for Best Results</h4>
    <p>
    • Upload clear, high-resolution images<br>
    • Provide detailed context about the medical issue<br>
    • Ensure all necessary information is provided for accurate analysis
    </p>
</div>
""", unsafe_allow_html=True)
