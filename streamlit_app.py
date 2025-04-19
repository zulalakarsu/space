import streamlit as st
import requests
from PIL import Image
import io
import time
import json
from typing import List, Dict, Any, Optional

# Define API endpoints
BASE_URL = "https://space-triage-199983032721.us-central1.run.app"
IDENTIFY_API = f"{BASE_URL}/identify"
NAVIGATE_API = f"{BASE_URL}/navigate"
DESCRIBE_API = f"{BASE_URL}/describe"

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
    st.session_state.selected_organ = None
    st.session_state.target_organ = ""
    st.rerun()

# Configure the page
st.set_page_config(
    page_title="Space Triage: AI-Guided Ultrasound",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style id="space-triage-styles">
    /* Main background */
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* Welcome page container */
    .welcome-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem;
        text-align: center;
    }
    
    /* Text background container */
    .text-background {
        background: rgba(0, 0, 0, 0.7);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
        margin-bottom: 2rem;
    }
    
    /* Welcome header */
    .welcome-header {
        text-align: center;
        padding: 1rem 0;
        color: #FFFFFF !important;
        font-size: 2.5rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        margin: 0;
    }
    
    /* Welcome message */
    .welcome-message {
        font-size: 1.2rem;
        color: #FFFFFF !important;
        line-height: 1.6;
        margin: 0;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Start button */
    .stButton > button {
        background-color: #3B82F6;
        color: white;
        padding: 1rem 2rem;
        font-size: 1.2rem;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
        max-width: 300px;
        margin: 0 auto;
    }
    
    .stButton > button:hover {
        background-color: #2563EB;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: rgba(255, 255, 255, 0.95);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    /* Dashboard styles */
    .dashboard-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    .organ-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    
    .organ-card:hover {
        transform: translateY(-2px);
    }
    
    .status-healthy {
        color: #10B981;
        font-weight: bold;
    }
    
    .status-unhealthy {
        color: #EF4444;
        font-weight: bold;
    }
    
    .dashboard-header {
        color: #FFFFFF !important;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Organ selection styles */
    .organ-selection-card {
        background: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        text-align: center;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .organ-selection-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    .organ-icon {
        font-size: 2.5rem;
        margin: 0;
        padding: 0.5rem;
    }
    
    .organ-name {
        font-size: 1.2rem;
        font-weight: bold;
        margin: 0.5rem 0;
        color: #2D3748;
    }
    
    .organ-description {
        font-size: 0.9rem;
        color: #718096;
        margin: 0;
    }
    
    /* Back to Dashboard button */
    .back-button {
        background-color: #4A5568;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .back-button:hover {
        background-color: #2D3748;
        transform: translateY(-2px);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: #FFFFFF !important;
    }
    
    /* Main title styling */
    .main-title {
        color: #FFFFFF !important;
        text-align: center;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        margin-bottom: 2rem;
    }
    
    /* Input label styling */
    .stTextInput label {
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "welcome"  # Stages: welcome, login, dashboard, select_organ, initial, identify, navigate, describe
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "needs_navigation" not in st.session_state:
    st.session_state.needs_navigation = False
if "navigate_response" not in st.session_state:
    st.session_state.navigate_response = None
if "description_response" not in st.session_state:
    st.session_state.description_response = None
if "astronaut_name" not in st.session_state:
    st.session_state.astronaut_name = ""
if "selected_organ" not in st.session_state:
    st.session_state.selected_organ = None
if "target_organ" not in st.session_state:
    st.session_state.target_organ = ""
if "health_records" not in st.session_state:
    # Sample health records data structure
    st.session_state.health_records = {
        "liver": {
            "latest_date": "2024-03-15",
            "status": "unhealthy",
            "notes": "Slight inflammation detected, elevated enzyme levels",
            "recommendations": [
                "Schedule follow-up in 2 weeks",
                "Monitor liver function tests",
                "Maintain low-fat diet",
                "Avoid alcohol consumption"
            ],
            "alerts": ["Elevated ALT levels", "Mild fatty changes"]
        },
        "kidneys": {
            "latest_date": "2024-03-14",
            "status": "healthy",
            "notes": "Normal function, good filtration rate",
            "recommendations": [
                "Continue regular hydration",
                "Monitor blood pressure",
                "Maintain balanced diet"
            ],
            "alerts": []
        },
        "pancreas": {
            "latest_date": "2024-03-13",
            "status": "healthy",
            "notes": "Normal size and function, no abnormalities detected",
            "recommendations": [
                "Monitor blood sugar levels",
                "Maintain healthy diet",
                "Regular exercise"
            ],
            "alerts": []
        },
        "breasts": {
            "latest_date": "2024-03-12",
            "status": "healthy",
            "notes": "Normal capacity and function",
            "recommendations": [
                "Maintain good hydration",
                "Regular voiding schedule",
                "Monitor for any changes"
            ],
            "alerts": []
        },
        "thyroid": {
            "latest_date": "2024-03-11",
            "status": "unhealthy",
            "notes": "Slightly enlarged, elevated TSH levels",
            "recommendations": [
                "Follow-up in 1 month",
                "Monitor thyroid function",
                "Consider medication adjustment"
            ],
            "alerts": ["Elevated TSH", "Mild enlargement"]
        },
        "heart": {
            "latest_date": "2024-03-10",
            "status": "healthy",
            "notes": "Normal rhythm, good ejection fraction",
            "recommendations": [
                "Continue regular exercise",
                "Monitor blood pressure",
                "Maintain heart-healthy diet"
            ],
            "alerts": []
        },
        "lungs": {
            "latest_date": "2024-03-09",
            "status": "healthy",
            "notes": "Clear lung fields, normal breathing capacity",
            "recommendations": [
                "Continue regular exercise",
                "Avoid exposure to irritants",
                "Practice deep breathing exercises"
            ],
            "alerts": []
        }
    }

# Welcome Page
if st.session_state.current_stage == "welcome":
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    # Text content with background
    st.markdown("""
        <div class="text-background">
            <h1 class="welcome-header">Welcome Astronaut</h1>
            <div class="welcome-message">
                Welcome to Space Triage, your AI-powered medical assistant for space missions.
                Let's begin your medical assessment journey.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Button
    if st.button("Login", key="login_button"):
        st.session_state.current_stage = "login"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Login Page
elif st.session_state.current_stage == "login":
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    
    # Text content with background
    st.markdown("""
        <div class="text-background">
            <h1 class="welcome-header">Astronaut Login</h1>
            <div class="welcome-message">
                Please enter your name to begin your medical assessment.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Login Form with white label
    st.markdown('<p style="color: white; text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);">Astronaut Name</p>', unsafe_allow_html=True)
    astronaut_name = st.text_input("", key="login_name")
    
    if st.button("Continue", key="continue_button"):
        if astronaut_name.strip():
            st.session_state.astronaut_name = astronaut_name
            st.session_state.current_stage = "dashboard"
            st.rerun()
        else:
            st.error("Please enter your name to continue.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Dashboard Page
elif st.session_state.current_stage == "dashboard":
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Dashboard Header
    st.markdown(f"""
        <h1 class="dashboard-header">Health Records Dashboard</h1>
        <h2 class="dashboard-header">Welcome, {st.session_state.astronaut_name}</h2>
    """, unsafe_allow_html=True)
    
    # Create tabs for each organ
    tabs = st.tabs([organ.capitalize() for organ in st.session_state.health_records.keys()])
    
    # Display detailed information for each organ in its respective tab
    for tab, (organ, data) in zip(tabs, st.session_state.health_records.items()):
        with tab:
            # Create three columns for the sub-dashboard
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                # Status Card
                st.markdown(f"""
                    <div class="organ-card">
                        <h3 style="text-transform: capitalize;">Status Overview</h3>
                        <p><strong>Latest Check:</strong> {data['latest_date']}</p>
                        <p><strong>Status:</strong> 
                            <span class="status-{data['status']}">
                                {data['status'].upper()}
                            </span>
                        </p>
                        <p><strong>Notes:</strong> {data['notes']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Quick Actions
                st.markdown("""
                    <div class="organ-card">
                        <h3>Quick Actions</h3>
                        <button class="stButton">Schedule New Check</button>
                        <button class="stButton">View History</button>
                        <button class="stButton">Download Report</button>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Detailed Information
                st.markdown(f"""
                    <div class="organ-card">
                        <h3>Detailed Information</h3>
                        <p><strong>Last Assessment:</strong> Complete evaluation on {data['latest_date']}</p>
                        <p><strong>Next Recommended Check:</strong> {data['latest_date']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Historical Data (placeholder)
                st.markdown("""
                    <div class="organ-card">
                        <h3>Historical Data</h3>
                        <p>No historical data available</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                # Recommendations
                recommendations_html = """
                    <div class="organ-card">
                        <h3>Recommendations</h3>
                        <p>Based on your latest assessment:</p>
                        <ul>
                """
                for rec in data.get('recommendations', []):
                    recommendations_html += f"<li>{rec}</li>"
                recommendations_html += """
                        </ul>
                    </div>
                """
                st.markdown(recommendations_html, unsafe_allow_html=True)
                
                # Alerts/Notifications
                alerts_html = """
                    <div class="organ-card">
                        <h3>Alerts</h3>
                """
                if data.get('alerts'):
                    alerts_html += "<ul>"
                    for alert in data['alerts']:
                        alerts_html += f'<li class="status-unhealthy">{alert}</li>'
                    alerts_html += "</ul>"
                else:
                    alerts_html += "<p>No active alerts</p>"
                alerts_html += "</div>"
                st.markdown(alerts_html, unsafe_allow_html=True)
    
    # Add a button to start new assessment
    if st.button("Start New Assessment", key="new_assessment"):
        st.session_state.current_stage = "select_organ"  # Changed from "initial" to "select_organ"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Organ Selection Page
elif st.session_state.current_stage == "select_organ":
    st.markdown('<div class="dashboard-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
        <h1 class="dashboard-header">Select Organ to Assess</h1>
        <h2 class="dashboard-header">Welcome, {st.session_state.astronaut_name}</h2>
    """, unsafe_allow_html=True)
    
    # Create a grid of organ selection buttons
    col1, col2, col3 = st.columns(3)
    
    # Define organ icons and descriptions
    organs = {
        "liver": {
            "icon": "🫁",
            "color": "#FF6B6B",
            "description": "Check liver function and health"
        },
        "kidneys": {
            "icon": "🫘",
            "color": "#4ECDC4",
            "description": "Assess kidney function"
        },
        "pancreas": {
            "icon": "🔬",
            "color": "#FFD93D",
            "description": "Evaluate pancreatic health"
        },
        "bladder": {
            "icon": "💧",
            "color": "#6C5CE7",
            "description": "Check bladder condition"
        },
        "thyroid": {
            "icon": "🦋",
            "color": "#A8E6CF",
            "description": "Assess thyroid function"
        },
        "heart": {
            "icon": "❤️",
            "color": "#FF8B94",
            "description": "Evaluate heart health"
        },
        "lungs": {
            "icon": "🫁",
            "color": "#95E1D3",
            "description": "Check lung function"
        }
    }
    
    # Create buttons for each organ
    for i, (organ, details) in enumerate(organs.items()):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
                <div class="organ-selection-card" style="border-color: {details['color']};">
                    <div class="organ-icon">{details['icon']}</div>
                    <div class="organ-name">{organ.capitalize()}</div>
                    <div class="organ-description">{details['description']}</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Select {organ.capitalize()}", key=f"select_{organ}"):
                st.session_state.selected_organ = organ
                st.session_state.target_organ = organ  # Set the target organ to the selected organ
                st.session_state.current_stage = "initial"
                st.rerun()
    
    # Back to Dashboard button
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem;">
            <button class="back-button">Back to Dashboard</button>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Back to Dashboard", key="back_to_dashboard"):
        st.session_state.current_stage = "dashboard"
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main Application (only show if not on welcome or login page)
elif st.session_state.current_stage not in ["welcome", "login"]:
    # Main title with white color
    st.markdown('<h1 class="main-title">Space Triage: AI-Guided Ultrasound</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🚀 Space Triage")
        st.subheader(f"Welcome, {st.session_state.astronaut_name}")
        
        # Display the selected organ instead of requiring input
        if st.session_state.selected_organ:
            st.markdown(f"### Target Organ: {st.session_state.selected_organ.capitalize()}")
            if st.button("Change Organ", key="change_organ"):
                st.session_state.current_stage = "select_organ"
                st.rerun()
        else:
            st.markdown("### No organ selected")
            if st.button("Select Organ", key="select_organ_button"):
                st.session_state.current_stage = "select_organ"
                st.rerun()
        
        # Additional information or settings could go here
        st.markdown("---")
        st.markdown("### How to use:")
        st.markdown("1. Select the organ you wish to diagnose")
        st.markdown("2. Upload an ultrasound image in the chat")
        st.markdown("3. Follow the AI guidance to improve your scan")
        st.markdown("4. Receive an AI-assisted diagnosis")
        
        # Reset button
        if st.button("🔄 Start New Session"):
            restart_session()


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