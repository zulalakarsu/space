import streamlit as st
import requests
from PIL import Image
import io
import time
import json
from typing import List, Dict, Any, Optional

# Configure the page
st.set_page_config(
    page_title="Space Triage: AI-Guided Ultrasound",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "initial"  # Stages: initial, identify, navigate, describe
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "needs_navigation" not in st.session_state:
    st.session_state.needs_navigation = False
if "navigate_response" not in st.session_state:
    st.session_state.navigate_response = None
if "description_response" not in st.session_state:
    st.session_state.description_response = None

# API endpoints
IDENTIFY_API = "http://localhost:8000/identify"
NAVIGATE_API = "http://localhost:8000/navigate"
DESCRIBE_API = "http://localhost:8000/describe"

# Custom functions
def image_to_bytes(uploaded_image):
    """Convert uploaded image to bytes"""
    if uploaded_image is None:
        return None
    
    img = Image.open(uploaded_image)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def call_identify_api(image_bytes, target_organ):
    """Call the identify API endpoint with an image and organ name"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"entity_name": target_organ}
        response = requests.post(IDENTIFY_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling identify API: {e}")
        return {"found": False, "entity": target_organ, "error": str(e)}

def call_navigate_api(image_bytes, target_organ):
    """Call the navigate API endpoint with image and entity name"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"entity_name": target_organ}
        
        # Send entity_name as form data and the image file
        response = requests.post(NAVIGATE_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling navigate API: {e}")
        return {"response": "Error occurred during navigation guidance.", "error": str(e)}

def call_description_api(image_bytes, target_organ):
    """Call the describe API endpoint with an image"""
    try:
        files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
        data = {"target_organ": target_organ}
        response = requests.post(DESCRIBE_API, files=files, data=data)
        return response.json()
    except Exception as e:
        st.error(f"Error calling describe API: {e}")
        return {"description": "Error occurred during diagnosis.", "error": str(e)}

def process_image_flow():
    """Process the uploaded image through the flow based on current stage"""
    if st.session_state.uploaded_image is None:
        return
    
    image_bytes = image_to_bytes(st.session_state.uploaded_image)
    
    if st.session_state.current_stage == "identify":
        # Call identify API
        with st.spinner("Analyzing image..."):
            response = call_identify_api(
                image_bytes,
                st.session_state.target_organ
            )
            
        if response.get("found", False):
            st.session_state.messages.append({"role": "assistant", "content": f"✅ The {response.get('entity', 'target organ')} has been successfully identified in the image."})
            st.session_state.current_stage = "describe"
            
            # Move directly to description
            with st.spinner("Generating diagnosis..."):
                description_response = call_description_api(image_bytes, st.session_state.target_organ)
                st.session_state.description_response = description_response
                
            diagnosis_text = description_response.get("description", "No diagnosis available")
            st.session_state.messages.append({"role": "assistant", "content": f"🔬 **Diagnosis Results**:\n\n{diagnosis_text}"})
            
        else:
            st.session_state.messages.append({"role": "assistant", "content": f"❌ I couldn't clearly identify the {st.session_state.target_organ} in this image. Would you like me to help you navigate to get a better view?"})
            st.session_state.needs_navigation = True
            st.session_state.current_stage = "ask_navigation"
    
    elif st.session_state.current_stage == "navigate":
        # Call navigate API with image and entity name
        with st.spinner("Generating navigation guidance..."):
            response = call_navigate_api(image_bytes, st.session_state.target_organ)
            st.session_state.navigate_response = response
            
        navigation_text = response.get("response", "No navigation guidance available")
        st.session_state.messages.append({"role": "assistant", "content": f"🧭 **Navigation Guidance**:\n\n{navigation_text}\n\nPlease adjust your probe following these instructions and upload a new image when ready."})
        st.session_state.current_stage = "wait_for_new_image"
    
    elif st.session_state.current_stage == "describe":
        # Call describe API
        with st.spinner("Generating diagnosis..."):
            response = call_description_api(image_bytes, st.session_state.target_organ)
            st.session_state.description_response = response
            
        diagnosis_text = response.get("description", "No diagnosis available")
        st.session_state.messages.append({"role": "assistant", "content": f"🔬 **Diagnosis Results**:\n\n{diagnosis_text}"})
        st.session_state.current_stage = "chat"  # Move to open chat for follow-up questions

def handle_user_input(user_input):
    """Process text input from the user"""
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Handle user response based on current stage
        if st.session_state.current_stage == "ask_navigation" and st.session_state.needs_navigation:
            if "yes" in user_input.lower() or "sure" in user_input.lower() or "ok" in user_input.lower():
                st.session_state.current_stage = "navigate"
                st.session_state.messages.append({"role": "assistant", "content": "I'll help you navigate to get a better view. Processing your current image..."})
                process_image_flow()
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Please upload a different image that shows the target organ more clearly."})
                st.session_state.current_stage = "wait_for_new_image"
        
        # If we're in chat mode (after diagnosis), respond to follow-up questions
        elif st.session_state.current_stage == "chat":
            # Here you could integrate with an LLM to answer follow-up questions
            # For now we'll use a simple response
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Thank you for your question. To provide a more detailed answer, I would need to connect to a medical knowledge base. Is there something specific about the diagnosis you'd like to know more about?"
            })

def restart_session():
    """Reset the session state to start over"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.messages = []
    st.session_state.current_stage = "initial"
    st.session_state.uploaded_image = None
    st.session_state.needs_navigation = False
    st.session_state.navigate_response = None
    st.session_state.description_response = None
    st.rerun()

# Sidebar
with st.sidebar:
    st.title("🚀 Space Triage")
    st.subheader("AI-Guided Ultrasound")
    
    # Target organ selection
    st.session_state.target_organ = st.text_input(
        "Target Organ to Diagnose:",
        value=st.session_state.get("target_organ", ""),
        key="sidebar_target_organ"
    )
    
    # Additional information or settings could go here
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Enter the target organ you wish to diagnose")
    st.markdown("2. Upload an ultrasound image in the chat")
    st.markdown("3. Follow the AI guidance to improve your scan")
    st.markdown("4. Receive an AI-assisted diagnosis")
    
    # Reset button
    if st.button("🔄 Start New Session"):
        restart_session()

# Main content area - Chat interface
st.title("Space Triage: AI-Guided Ultrasound")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message has an image, display it
        if "image" in message:
            st.image(message["image"])

# Welcome message on first load
if st.session_state.current_stage == "initial" and not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("👋 Welcome to Space Triage! I'm your AI ultrasound assistant. Please enter the organ you wish to diagnose in the sidebar, then upload an ultrasound image to begin.")
    st.session_state.current_stage = "waiting_for_image"

# Image uploader in chat input
uploaded_file = st.file_uploader(
    "Upload an ultrasound image", 
    type=["png", "jpg", "jpeg"],
    key="chat_file_uploader",
    label_visibility="collapsed"
)

# Handle file upload
if uploaded_file is not None and (st.session_state.uploaded_image is None or uploaded_file != st.session_state.uploaded_image):
    # Store the uploaded image
    st.session_state.uploaded_image = uploaded_file
    
    # Add user message with image
    st.session_state.messages.append({
        "role": "user", 
        "content": f"I've uploaded an ultrasound image for {st.session_state.target_organ} analysis.",
        "image": uploaded_file  # Store image in message for reference
    })
    
    # Display the image
    with st.chat_message("user"):
        st.markdown(f"I've uploaded an ultrasound image for {st.session_state.target_organ} analysis.")
        st.image(uploaded_file, caption="Uploaded Ultrasound Image")
    
    # Set stage to identify if we have an organ target
    if st.session_state.target_organ:
        st.session_state.current_stage = "identify"
        # Process the image through our flow
        process_image_flow()
    else:
        with st.chat_message("assistant"):
            st.markdown("❗ Please specify the target organ in the sidebar before proceeding.")
    
    # Force a rerun to update the UI
    st.rerun()

# Chat input for text messages
user_input = st.chat_input("Ask a question or provide additional information...")
if user_input:
    handle_user_input(user_input)
    st.rerun()

# Add a footer
st.markdown("---")
st.caption("Space Triage | AI-Guided Ultrasound Assistant | Demo Version")