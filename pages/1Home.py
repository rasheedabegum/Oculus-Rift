import os
import cv2
import streamlit as st
from ultralytics import YOLO
import numpy as np
from PIL import Image
import google.generativeai as genai
import io
import warnings
import logging
import base64
from pathlib import Path
import folium
from streamlit_folium import folium_static
import requests
from geopy.geocoders import Nominatim
from datetime import datetime
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
# Import Supabase client for database operations
from supabase import create_client, Client
import uuid
from deep_translator import GoogleTranslator
import speech_recognition as sr
import pyttsx3

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Supabase configuration
SUPABASE_URL = "https://xahzxcipqkckawzcyzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaHp4Y2lwcWtja2F3emN5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2NTY5ODMsImV4cCI6MjA1ODIzMjk4M30.J_ND_Jl3MwrR_Yy0v_YC7WwTGJE5dmlJuZcmhJwUvtY"

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {str(e)}")
    supabase = None

# Suppress warnings
warnings.filterwarnings('ignore')

# Add base64 encoding function needed for video background
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_video_background(video_path):
    """Set a video as the background for the Streamlit app."""
    video_html = f"""
    <style>
    .stApp {{
        background: transparent;
    }}
    
    .video-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        overflow: hidden;
    }}
    
    video {{
        position: absolute;
        min-width: 100%;
        min-height: 100%;
        width: auto;
        height: auto;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        object-fit: cover;
        opacity: 1.0; 
    }}
    
    /* ADDED: Overlay CSS */
    .overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8); /* Set opacity to 0.8 */
        z-index: -1;
    }}
    </style>
    
    <div class="video-container">
        <video autoplay loop muted playsinline>
            <source src="data:video/mp4;base64,{get_base64_of_bin_file(video_path)}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    <!-- ADDED: Overlay div -->
    <div class="overlay"></div>
    """
    st.markdown(video_html, unsafe_allow_html=True)

GOOGLE_API_KEY = "AIzaSyCwbIIjKcU4TKo1a44TyeV7T9iS_UOSuZE"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY


detection_types = {
    "brain_tumor": "<i class='fas fa-brain'></i> Brain Tumor",
    "eye_disease": "<i class='fas fa-eye'></i> Eye Disease",
    "lung_cancer": "<i class='fas fa-lungs'></i> Lung Cancer",
    "bone_fracture": "<i class='fas fa-bone'></i> Bone Fracture",
    "skin_disease": "<i class='fas fa-microscope'></i> Skin Disease",
    "diabetic_retinopathy": "<i class='fas fa-eye'></i> Diabetic Retinopathy",
    "tongue": "<i class='fas fa-tongue'></i> Tongue Analysis",
    "ulcer": "<i class='fas fa-band-aid'></i> Ulcer Detection",
    "nail": "<i class='fas fa-hand'></i> Nail Analysis"
}

genai.configure(api_key=GOOGLE_API_KEY)


st.set_page_config(
    page_title="AI Medical Assistant",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add Font Awesome for icons
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# Add modern styling for camera and upload buttons
st.markdown("""
<style>
/* Modern button styling for camera and file upload */
.camera-button-container button,
[data-testid="stFileUploader"] > section > .css-1offfwp > button {
    background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 15px rgba(0, 210, 255, 0.25) !important;
    transition: all 0.3s ease !important;
    margin-bottom: 1rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.camera-button-container button:hover,
[data-testid="stFileUploader"] > section > .css-1offfwp > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(0, 210, 255, 0.4) !important;
    background: linear-gradient(135deg, #00c4f0 0%, #3040c0 100%) !important;
}

.camera-button-container button::before,
[data-testid="stFileUploader"] > section > .css-1offfwp > button::before {
    content: "<i class='fas fa-camera'></i> " !important;
    margin-right: 8px !important;
    font-size: 1.2rem !important;
}

[data-testid="stFileUploader"] > section > .css-1offfwp > button::before {
    content: "<i class='fas fa-file-upload'></i> " !important;
}

/* File drag area styling */
[data-testid="stFileUploader"] > section {
    border: 2px dashed rgba(0, 210, 255, 0.4) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    background: rgba(0, 0, 0, 0.2) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploader"] > section:hover {
    border-color: #00d2ff !important;
    background: rgba(0, 210, 255, 0.05) !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px !important;
    margin-bottom: 0.8rem !important;
}

.stTabs [data-baseweb="tab"] {
    background-color: rgba(0, 0, 0, 0.2) !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0, 210, 255, 0.2) 0%, rgba(58, 71, 213, 0.2) 100%) !important;
    border: 1px solid rgba(0, 210, 255, 0.4) !important;
    color: #00d2ff !important;
}

/* Camera container */
.stCamera {
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
    border: 1px solid rgba(0, 210, 255, 0.3) !important;
}

/* Analysis button styling */
[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 4px 15px rgba(0, 210, 255, 0.25) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 20px rgba(0, 210, 255, 0.4) !important;
    background: linear-gradient(135deg, #00c4f0 0%, #3040c0 100%) !important;
}

/* Override Streamlit's default red focus borders with blue */
*:focus {
    outline-color: #00d2ff !important;
    box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
}

/* Override ALL Streamlit component focus/hover states */
/* This is more comprehensive to catch any missed elements */
[data-baseweb*="input"]:focus,
[data-baseweb*="input"]:active,
[data-baseweb*="input"]:hover,
[data-baseweb*="input"]:focus-within,
[data-baseweb*="input"] *:focus,
[data-baseweb*="input"] *:active,
[data-baseweb*="input"] *:hover,
[data-baseweb*="dropdown"]:focus,
[data-baseweb*="dropdown"]:active,
[data-baseweb*="dropdown"]:hover,
[data-baseweb*="dropdown"]:focus-within,
[data-baseweb*="dropdown"] *:focus,
[data-baseweb*="dropdown"] *:active,
[data-baseweb*="dropdown"] *:hover,
[data-baseweb*="select"]:focus,
[data-baseweb*="select"]:active,
[data-baseweb*="select"]:hover,
[data-baseweb*="select"]:focus-within,
[data-baseweb*="select"] *:focus,
[data-baseweb*="select"] *:active,
[data-baseweb*="select"] *:hover,
[data-baseweb*="button"]:focus,
[data-baseweb*="button"]:active,
[data-baseweb*="button"]:hover,
[role="button"]:focus,
[role="button"]:active,
[role="button"]:hover,
button:focus,
button:active,
button:hover,
input:focus,
input:active,
input:hover,
select:focus,
select:active,
select:hover,
textarea:focus,
textarea:active,
textarea:hover,
[data-testid*="Input"]:focus,
[data-testid*="Input"]:active,
[data-testid*="Input"]:hover,
[data-testid*="Input"]:focus-within,
[data-testid*="Input"] *:focus,
[data-testid*="Input"] *:active,
[data-testid*="Input"] *:hover {
    border-color: #00d2ff !important;
    outline-color: #00d2ff !important;
    box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
}

/* Override red accents in Streamlit */
.css-r421ms {
    border-color: #00d2ff !important;
}

/* Target specific hover/focus styles with !important to override defaults */
.element-container:hover button,
.element-container button:hover,
.element-container button:focus,
.element-container input:focus,
.element-container select:focus,
.stButton button:hover,
.stButton button:focus,
.stTextInput input:focus,
.stNumberInput input:focus,
.stSelectbox select:focus,
.stFileUploader button:hover,
.stFileUploader button:focus {
    border-color: #00d2ff !important;
    outline-color: #00d2ff !important;
    box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
}

/* Override specific red accent in Streamlit that might be coming from React components */
[role="button"]:hover,
[role="button"]:focus {
    background-color: rgba(0, 210, 255, 0.1) !important;
    color: #00d2ff !important;
}

/* Ensure all active and focused states use blue */
div[data-baseweb*="active"],
div[aria-selected="true"],
div[data-baseweb*="selected"],
[role="checkbox"][aria-checked="true"],
[role="radio"][aria-checked="true"],
[role="switch"][aria-checked="true"],
[role="tab"][aria-selected="true"],
[role="tabpanel"][aria-selected="true"],
.st-dk.st-df.st-dg.st-cs.st-df.st-dg {
    background-color: #00d2ff !important;
    border-color: #00d2ff !important;
    color: white !important;
}

/* All focus rings should be blue */
*:focus-visible {
    outline-color: #00d2ff !important;
}

/* Override progressbar and slider colors */
progress::-webkit-progress-value,
progress::-moz-progress-bar,
progress,
[role="progressbar"] > div,
[data-testid="stSlider"] div[role="slider"] {
    background-color: #00d2ff !important;
}

/* Set CSS variables for the whole document */
:root {
    --primary: #00d2ff !important;
    --primary-color: #00d2ff !important;
    --accent-color: #00d2ff !important;
    --hover-color: #00c4f0 !important;
    --active-color: #3040c0 !important;
    --focus-color: #00d2ff !important;
    --error-color: #00d2ff !important; /* Override error red with blue */
    --warning-color: #00a0c7 !important; /* Use darker blue for warnings */
}
</style>
""", unsafe_allow_html=True)

# Update the CSS styling section with these specific sidebar selectors
st.markdown("""
    <style>
    .stApp > header {
        background-color: transparent !important;
    }
    
    .stApp {
        color: white;  /* Makes text white for better visibility */
    }
    
    /* Make sidebar background semi-transparent black */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.5) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Style sidebar content */
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }

    /* Make the sidebar text more visible */
    [data-testid="stSidebar"] .st-emotion-cache-16idsys p,
    [data-testid="stSidebar"] .st-emotion-cache-16idsys span,
    [data-testid="stSidebar"] .st-emotion-cache-16idsys div,
    [data-testid="stSidebar"] .st-emotion-cache-16idsys label {
        color: white !important;
    }

    /* Style the markdown separator */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* Style for the GIF container */
    [data-testid="stImage"] {
        background: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_language' not in st.session_state:
    st.session_state.current_language = 'en'
if 'models' not in st.session_state:
    st.session_state.models = {}

# Initialize Gemini model globally
try:
    # Use gemini-2.0-flash model with fixed settings (removed temperature/creativity controls)
    GEMINI_MODEL = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        generation_config={
            "temperature": 0.1,  # Fixed to low temperature for consistent medical responses
            "top_p": 0.1,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
    )

    # Test the model initialization with a simple prompt
    test_response = GEMINI_MODEL.generate_content("Hello")
    if not test_response.text:
        raise Exception("Failed to get response from model")

except Exception as e:
    st.error(f"Error initializing Gemini API: {str(e)}")
    GEMINI_MODEL = None

# Move sidebar outside of the try-except block
# Sidebar with simplified layout
with st.sidebar:
    # Logo
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1><i class='fas fa-hospital'></i></h1>", unsafe_allow_html=True)  # Fallback to icon

    # Welcome Message - Keep only the markdown part
    st.markdown(f"### Welcome, {st.session_state.get('full_name', 'User')}!") # Changed to markdown header
    st.markdown("Your AI Medical Assistant")

    st.markdown("---")

    # Language selector
    st.markdown("### <i class='fas fa-globe'></i> Language", unsafe_allow_html=True)
    languages = {
        'en': '🇺🇸 English',
        'hi': '🇮🇳 हिंदी'
    }
    selected_lang = st.selectbox("Select Language", options=list(languages.keys()),
                                format_func=lambda x: languages[x],
                                key='language',
                                label_visibility="collapsed") # Hide label for cleaner look

    st.markdown("---")

    # Quick Guide
    st.markdown("### Quick Use")
    st.markdown("""
    1.  Use **Camera** or **Upload** tab for image analysis.
    2.  Select the correct **detection model**.
    3.  Click **Analyze**.
    4.  Use the **Chat Assistant** for questions.
    """)

    st.markdown("---")

    # Important Note
    st.warning("<i class='fas fa-exclamation-triangle'></i> AI analysis is for information only. Always consult a doctor.", icon="⚠️")

def load_model(model_type):
    """Load YOLO model based on type"""
    try:
        # Initialize models dict if not exists
        if 'models' not in st.session_state:
            st.session_state.models = {}

        model_paths = {
            'brain_tumor': "braintumorp1.pt",
            'eye_disease': "eye.pt",
            'lung_cancer': "lung_cancer.pt",
            'bone_fracture': "bone.pt",
            'skin_disease': "skin345.pt",
            'diabetic_retinopathy': "xiaoru.pt",
            'tongue': "tongue(2).pt",
            'ulcer': "ulcer.pt",
            'nail': "nails.pt"
        }

        # If model not loaded yet
        if model_type not in st.session_state.models:
            model_path = model_paths.get(model_type)
            
            # Debug info
            st.write(f"Attempting to load model: {model_type}")
            st.write(f"Model path: {model_path}")
            
            # Check if file exists
            if model_path and os.path.exists(model_path):
                st.write(f"Loading model from path: {model_path}")
                try:
                    # Try loading with different YOLO configurations
                    try:
                        st.session_state.models[model_type] = YOLO(model_path)
                    except:
                        # Try with legacy mode if normal loading fails
                        st.session_state.models[model_type] = YOLO(model_path, task='detect', legacy=True)
                    st.write(f"Successfully loaded model: {model_type}")
                except Exception as model_error:
                    st.error(f"Error loading model {model_type}: {str(model_error)}")
                    return None
            else:
                st.error(f"Model file not found: {model_path}")
                # List all files in current directory for debugging
                st.write("Available files in directory:")
                for file in os.listdir():
                    if file.endswith('.pt'):
                        st.write(f"- {file}")
                return None

        return st.session_state.models.get(model_type)
    except Exception as e:
        st.error(f"Error in load_model function: {str(e)}")
        return None


def translate_text(text, target_lang):
    """Translate text to target language"""
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        st.error(f"Translation error: {str(e)}")
        return text  # Return original text if translation fails


def text_to_speech(text, language='en'):
    """Convert text to speech"""
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def speech_to_text():
    """Convert speech to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio)
        except:
            return None


def get_gemini_response(prompt, image=None):
    """Get response from Gemini API"""
    try:
        if image:
            # For image analysis, use gemini-2.0-flash
            response = GEMINI_MODEL.generate_content([prompt, image])
        else:
            # For text chat, use the same model
            response = GEMINI_MODEL.generate_content(prompt)

        if hasattr(response, 'text') and response.text:
            return response.text
        return "I apologize, but I couldn't generate a response."

    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        return "I apologize, but I'm having trouble generating a response right now."


def process_chat_response(prompt):
    """Process chat responses with streaming"""
    try:
        response = GEMINI_MODEL.send_message(prompt, stream=True)

        # Create a placeholder for streaming response
        message_placeholder = st.empty()
        full_response = ""

        # Stream the response
        for chunk in response:
            full_response += chunk.text
            message_placeholder.markdown(full_response + "▌")

        # Replace the placeholder with the complete response
        message_placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I apologize, but I'm having trouble generating a response right now."


def analyze_image_with_google_vision(image):
    """Analyze the image using Google Vision API."""
    image = vision.Image(content=image)
    response = vision_client.label_detection(image=image)
    labels = response.label_annotations
    results = [(label.description, label.score) for label in labels]
    return results


def process_image(image):
    """Process the uploaded image and return analysis results."""
    try:
        # Ensure the image is in a valid format
        if isinstance(image, bytes):
            image = Image.open(io.BytesIO(image))
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Analyze the image using Google Vision API
        analysis_results = analyze_image_with_google_vision(img_byte_arr)
        return analysis_results
    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
        return None  # Return None if there's an error


def display_prediction(class_name, conf):
    """Legacy function maintained for compatibility"""
    return f"""
    <div style="
        background-color: rgba(0, 0, 0, 0.5);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid rgba(0, 210, 255, 0.3);
    ">
        <h4 style="color: #00d2ff; margin: 0 0 10px 0;">{class_name}</h4>
        <div style="
            background-color: rgba(0, 210, 255, 0.2);
            height: 25px;
            border-radius: 5px;
            position: relative;
            width: 100%;
        ">
            <div style="
                background-color: #00d2ff;
                width: {conf * 100}%;
                height: 100%;
                border-radius: 5px;
            "></div>
            <p style="
                color: white;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                margin: 0;
            ">Confidence: {conf:.2%}</p>
        </div>
    </div>
    """


def initialize_chat_if_needed():
    """Initialize or get existing chat session"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'gemini_chat' not in st.session_state and GEMINI_MODEL:
        st.session_state.gemini_chat = GEMINI_MODEL.start_chat(history=[])


def get_chat_response(prompt):
    """Get chat response from Gemini"""
    try:
        if not GEMINI_MODEL:
            return "AI model not initialized properly. Please check your API key."

        medical_prompt = f"""
        You are an Oculus Rift Healthcare AI medical AI assistant. Please provide helpful medical information and advice while keeping in mind:
        1. Be clear and professional
        2. Include relevant medical terminology with explanations
        3. Always encourage consulting healthcare professionals
        4. Provide evidence-based information when possible
        5. use only 100-200 words

        User question: {prompt}
        """

        # Generate response (removed creativity settings)
        response = GEMINI_MODEL.generate_content(medical_prompt)

        # Check if response is blocked
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            return "I apologize, but I cannot provide a response to that query. Please try rephrasing your question."

        if hasattr(response, 'text') and response.text:
            return response.text.strip()  # Trim the response

        return "I apologize, but I couldn't generate a response."

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I apologize, but I'm having trouble generating a response."


def chat_interface(selected_lang):
    """Render chat interface"""
    st.subheader(translate_interface_text("💬 Medical Assistant Chat", selected_lang))

    # Chat input at the top
    if prompt := st.chat_input(translate_interface_text("Ask me anything about your health...", selected_lang)):
        # Add user message
        with st.chat_message("user"):
            st.markdown(translate_interface_text(prompt, selected_lang))
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner(translate_interface_text("Thinking...", selected_lang)):
                # Call the actual function to get the response
                response = get_chat_response(prompt)
                st.markdown(response)

                # Add assistant response to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            content = translate_text(message["content"], selected_lang) if selected_lang != 'en' else message["content"]
            st.markdown(content)

    # Add chat guidelines in expandable section at the bottom
    with st.expander(translate_interface_text("ℹ️ Chat Guidelines", selected_lang), expanded=False):
        guidelines = [
            "Ask about medical conditions",
            "Get general health advice",
            "Learn about prevention",
            "Understand detection results"
        ]
        for guideline in guidelines:
            st.markdown(f"- {translate_interface_text(guideline, selected_lang)}")

        st.markdown(f"**{translate_interface_text('Note:', selected_lang)}** " +
                    translate_interface_text(
                        "This is an AI assistant and not a replacement for professional medical advice.",
                        selected_lang))

    # Clear chat button at the bottom
    if st.session_state.chat_history:
        if st.button(translate_interface_text("🗑️ Clear Chat History", selected_lang), key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()


def translate_interface_text(text, target_lang):
    """Translate interface text if not in English"""
    if target_lang != 'en':
        try:
            translator = GoogleTranslator(source='en', target=target_lang)
            return translator.translate(text)
        except Exception as e:
            st.error(f"Translation error: {str(e)}")
    return text


def translate_page_content(selected_lang):
    """Translate all static page content"""
    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        # Initialize img_file variable
        img_file = None

        # Translate tab labels
        tab_labels = [
            translate_interface_text(x, selected_lang)
            for x in ["📸 Camera", "📁 Upload"]
        ]
        tab1, tab2 = st.tabs(tab_labels)

        with tab1:
            # Use session state for language
            camera_label = translate_interface_text("Take a picture", st.session_state.current_language)
            
            # Add custom CSS for camera
            st.markdown("""
                <style>
                .stCamera > video {
                    width: 100%;
                    aspect-ratio: 16/9 !important;
                    border-radius: 12px !important;
                }
                .stCamera > img {
                    width: 100%;
                    aspect-ratio: 16/9 !important;
                    object-fit: cover;
                    border-radius: 12px !important;
                }
                </style>
                <div class="camera-button-container">
                </div>
            """, unsafe_allow_html=True)
            
            # Camera input with custom styling
            img_file_camera = st.camera_input(
                camera_label,
                key="camera_input",
                help="Please capture the image in landscape orientation"
            )
            
            if img_file_camera:
                try:
                    # Read the image from camera
                    image = Image.open(img_file_camera)
                    
                    # Display captured image
                    st.image(image, caption="Captured Image", use_container_width=True)
                    
                    # Generate description using Google Vision API
                    description = generate_image_description(image)
                    st.markdown(f"<h1 style='color: #00d2ff;'>{description}</h1>", unsafe_allow_html=True)

                    # Model selection
                    selected_model = st.selectbox(
                        "Select Model for Analysis", 
                        list(detection_types.keys()),
                        key="camera_model_select"
                    )
                    
                    if st.button("Analyze", key="camera_analyze_button"):
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_bytes = img_byte_arr.getvalue()
                        
                        analyze_with_model(selected_model, img_bytes)

                except Exception as e:
                    st.error(f"Error processing camera image: {str(e)}")

        with tab2:
            # Custom upload message
            st.markdown("""
            <style>
            .modern-upload-text {
                text-align: center;
                padding: 0 0 10px 0;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 500;
            }
            </style>
            <div class="modern-upload-text">
                📁 Upload a medical image (X-ray, MRI, CT, etc.)
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(" ", type=["jpg", "png", "jpeg"])  # Empty label as we've added custom text
            if uploaded_file:
                try:
                    # Read the file content first
                    file_bytes = uploaded_file.read()
                    
                    # Create PIL Image from bytes
                    image = Image.open(io.BytesIO(file_bytes))
                    
                    # Display the image
                    st.image(image, caption="Uploaded Image", use_container_width=True)
                    
                    # Generate description using Google Vision API
                    description = generate_image_description(image)
                    st.markdown(f"<h1 style='color: #00d2ff;'>{description}</h1>", unsafe_allow_html=True)

                    # Model selection
                    selected_model = st.selectbox(
                        "Select Model for Analysis", 
                        list(detection_types.keys()),
                        key="upload_model_select"
                    )
                    
                    if st.button("Analyze", key="upload_analyze_button"):
                        analyze_with_model(selected_model, file_bytes)

                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")

        # Process image if available
        if img_file:
            image = Image.open(img_file)
            st.image(image, caption=translate_interface_text("Uploaded Image", selected_lang), use_container_width=True)

            check_button = st.button(
                translate_interface_text("🔍 Check for Detection", selected_lang),
                key="check_detection_button",
                use_container_width=True
            )

            if check_button:
                process_detection(image, selected_lang)

    with col2:
        st.markdown("## AI Chat Assistant")

        # Initialize chat history if needed (still needed for other potential uses? Let's keep initialization for now)
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Chat input
        if prompt := st.chat_input("Ask me anything about your health..."):
            # Display current user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display current assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_chat_response(prompt)
                    st.markdown(response)


def show_hospital_info(diagnosis):
    # Get current location
    location = get_current_location()
    
    # Find nearby hospitals
    hospitals = find_nearby_hospitals(location['lat'], location['lon'])
    
    # Create map centered on user's location
    m = folium.Map(
        location=[location['lat'], location['lon']], 
        zoom_start=12
    )
    
    # Add user's location marker
    folium.Marker(
        [location['lat'], location['lon']],
        popup='Your Location',
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add nearby hospitals to map
    for hospital in hospitals:
        folium.Marker(
            [hospital['lat'], hospital['lon']],
            popup=hospital['name'],
            icon=folium.Icon(color='green', icon='plus')
        ).add_to(m)
    
    # Return map and data
    return {
        'location': location,
        'hospitals': hospitals,
        'map': m
    }


def create_pdf_report(report_data, image=None):
    """Create a PDF report using reportlab"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.navy,
        spaceAfter=6
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.navy,
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )

    # Add letterhead
    story.append(Paragraph("Oculus Rift Healthcare AI Medical Center", title_style))
    story.append(Paragraph("Advanced AI-Powered Healthcare", ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.darkblue,
        spaceAfter=6
    )))
    
    # Add contact info
    contact_info = """
    <para alignment="center">
    123 AI Healthcare Road, Medical District<br/>
    Tel: +91-1234567890 | Email: care@oculusrifthealthcare.com<br/>
    www.oculusrifthealthcare.com
    </para>
    """
    story.append(Paragraph(contact_info, ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey
    )))
    
    # Add a line to separate letterhead from content
    story.append(Spacer(1, 20))
    
    # Add report title
    story.append(Paragraph("MEDICAL ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 10))
    
    # Add date
    story.append(Paragraph(f"<b>Date:</b> {report_data['date']}", normal_style))
    story.append(Spacer(1, 12))

    # Create patient info table if available
    if 'patient_name' in report_data and report_data['patient_name']:
        story.append(Paragraph("Patient Information", section_title_style))
        patient_data = [
            ["Patient Name:", report_data.get('patient_name', 'Not Specified')],
        ]
        patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightskyblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 12))

    # Add analysis results section
    story.append(Paragraph("Analysis Results", section_title_style))
    
    # Format the results
    result_color = colors.lightcoral if "abnormal" in report_data['diagnosis'].lower() else colors.lightgreen
    
    # Create results table data with detection count
    results_data = [
        ["Diagnosis:", report_data['diagnosis']],
        ["Highest Confidence:", report_data['confidence']],
        ["Total Detections:", str(report_data.get('detection_count', 0))]
    ]
    
    # Create table with colored background based on result
    results_table = Table(results_data, colWidths=[1.5*inch, 4*inch])
    results_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightskyblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('BACKGROUND', (1, 0), (1, 0), result_color),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(results_table)
    story.append(Spacer(1, 15))
    
    # Add detailed detection information if available
    if 'detections' in report_data and report_data['detections']:
        story.append(Paragraph("Detailed Detection Information", section_title_style))
        
        # Create table headers
        detection_data = [["Detection", "Confidence Score"]]
        
        # Add each detection to the table
        for detection in report_data['detections']:
            # Each detection should be a tuple of (class_name, confidence)
            if isinstance(detection, tuple) and len(detection) == 2:
                class_name, conf = detection
                # Format confidence as percentage
                conf_str = f"{conf:.2%}" if isinstance(conf, float) else str(conf)
                detection_data.append([class_name, conf_str])
        
        # Create the detections table
        if len(detection_data) > 1:  # Only create table if we have data beyond headers
            detections_table = Table(detection_data, colWidths=[3*inch, 2.5*inch])
            
            # Style the table
            table_style = [
                ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightskyblue),  # Header row
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Header text
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),  # Center confidence column
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
                ('PADDING', (0, 0), (-1, -1), 6),
            ]
            
            # Add alternating row colors
            for i in range(1, len(detection_data)):
                if i % 2 == 1:
                    table_style.append(('BACKGROUND', (0, i), (-1, i), colors.lavender))
            
            detections_table.setStyle(TableStyle(table_style))
            story.append(detections_table)
            story.append(Spacer(1, 15))

    # Add the analyzed image if available (this should be the image with detection markings)
    if image is not None:
        story.append(Paragraph("Analysis Image with Detected Areas", section_title_style))
        try:
            # Convert numpy array to PIL Image if necessary
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image)
            
            # Save image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Add image to PDF
            img = RLImage(img_byte_arr, width=5*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 12))
        except Exception as e:
            story.append(Paragraph(f"Image could not be included: {str(e)}", normal_style))

    # Add recommendations if provided
    if 'recommendations' in report_data and report_data['recommendations']:
        story.append(Paragraph("Medical Recommendations", section_title_style))
        for rec in report_data['recommendations']:
            story.append(Paragraph(f"• {rec}", normal_style))
        story.append(Spacer(1, 15))
    
    # Add doctor's signature
    story.append(Spacer(1, 30))
    signature_data = [
        ["_______________________", ""],
        ["Consulting Physician", f"Date: {report_data['date']}"],
        ["Oculus Rift Healthcare AI Medical Center", ""]
    ]
    
    signature_table = Table(signature_data, colWidths=[3*inch, 2.5*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
        ('FONT', (0, 1), (0, 1), 'Helvetica-Bold'),
    ]))
    story.append(signature_table)

    # Add disclaimer
    story.append(Spacer(1, 30))
    disclaimer_text = """
    <para><i>Disclaimer: This report contains AI-assisted analysis and should be interpreted by qualified healthcare professionals only. 
    The results are not a definitive diagnosis and should be considered in the context of the patient's clinical presentation and other diagnostic information.
    Oculus Rift Healthcare AI employs state-of-the-art technology, but results should be validated by appropriate medical specialists.</i></para>
    """
    story.append(Paragraph(disclaimer_text, ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    )))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def show_report_section(diagnosis, confidence, image, detections=None, detection_count=0):
    # Generate recommendations based on diagnosis
    recommendations = get_recommendations(diagnosis)
    
    # Use email from session state as patient name instead of asking user to input it
    patient_name = st.session_state.get('email', 'guest_patient')
    
    # Create report
    report = create_medical_report(
        diagnosis=diagnosis, 
        confidence=confidence, 
        recommendations=recommendations, 
        patient_name=patient_name,
        detections=detections,
        detection_count=detection_count
    )
    
    # Display minimized UI but keep download functionality
    pdf_buffer = create_pdf_report(report, image)
    
    st.download_button(
        label="Download PDF Report",
        data=pdf_buffer,
        file_name=f"medical_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )
    
    # Return the report data
    return report


def get_recommendations(diagnosis):
    """Generate recommendations based on diagnosis"""
    recommendations = {
        "brain_tumor": [
            "Schedule an immediate consultation with a neurologist",
            "Get a follow-up MRI scan",
            "Monitor for any new symptoms"
        ],
        "eye_disease": [
            "Visit an ophthalmologist",
            "Protect eyes from bright light",
            "Regular eye check-ups"
        ],
        # Add more conditions and recommendations
    }
    
    # Get default recommendations if specific ones aren't found
    default_recs = [
        "Consult with a specialist",
        "Schedule regular check-ups",
        "Maintain a healthy lifestyle"
    ]
    
    return recommendations.get(diagnosis.lower(), default_recs)


def generate_image_description(image_data):
    """Generate a concise description for the given image using Google Generative AI."""
    try:
        # If image_data is already bytes, convert it to PIL Image
        if isinstance(image_data, bytes):
            image = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, Image.Image):
            image = image_data
        else:
            raise ValueError("Unsupported image format")

        # Resize image if needed
        image.thumbnail([640, 640], Image.Resampling.LANCZOS)

        # Convert to bytes for API processing
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Create model instance and generate description
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Updated prompt to match available models and improve selection
        prompt = """
        Analyze this medical image and respond in exactly 7 words following this format:
        'Detected: [condition]. Use [model] detection.'
        
        Choose the most appropriate model from this list only:
        1. Brain tumor detection - for brain MRI/CT scans
        2. Eye disease detection - for eye/retinal images
        3. Lung cancer detection - for chest X-rays/CT
        4. Bone fracture detection - for bone X-rays
        5. Skin disease detection - for skin conditions
        6. Diabetic retinopathy detection - for retinal scans
        7. Tongue detection - for tongue analysis
        8. Ulcer detection - for wound/ulcer images
        9. Nail detection - for nail condition analysis

        Example responses:
        'Detected: Brain mass. Use brain tumor detection.'
        'Detected: Retinal abnormality. Use eye disease detection.'
        'Detected: Chest mass. Use lung cancer detection.'
        'Detected: Broken bone. Use bone fracture detection.'
        'Detected: Skin lesion. Use skin disease detection.'
        'Detected: Retinal damage. Use diabetic retinopathy detection.'
        'Detected: Tongue condition. Use tongue detection.'
        'Detected: Foot ulcer. Use ulcer detection.'
        'Detected: Nail infection. Use nail detection.'
        if you see nail then say dail detection
        if you see skin ulcer type then say ulcer detection
        dont messup the model name with other disease
        Analyze the image carefully and choose the MOST appropriate model from the list above. Do not suggest any other models except if there is no other disease then say you are healthy and no disease detected.
        """
        
        response = model.generate_content(
            [prompt, {"mime_type": "image/png", "data": img_bytes}],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Low temperature for consistent model selection
                max_output_tokens=30,
                top_p=0.1,
            )
        )

        # Get the response and ensure it's concise
        result = response.text.strip()
        
        # If response is too long, truncate it
        words = result.split()
        if len(words) > 7:
            result = ' '.join(words[:7])

        return result

    except Exception as e:
        st.error(f"Error generating image description: {str(e)}")
        return "Unable to analyze image. Please try again."


def get_current_location():
    """Get user's current location using IP address"""
    try:
        # Use a public IP geolocation API
        response = requests.get('https://ipinfo.io/json', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # Check if we got rate limited
            if data.get('error') and 'rate limit' in data.get('reason', '').lower():
                # Fallback to alternative IP geolocation service
                response = requests.get('https://ipinfo.io/json', timeout=5)
                data = response.json()
            
            # Extract location data with validation
            try:
                coords = data.get('loc', '17.4065,78.4772').split(',')
                location_data = {
                    'lat': float(coords[0]),
                    'lon': float(coords[1]),
                    'city': data.get('city', 'Hyderabad')
                }
                st.success(f"Location found: {location_data['city']}")
                return location_data
            except (IndexError, ValueError):
                st.warning("Could not parse location coordinates. Using default location.")
                return {'lat': 17.4065, 'lon': 78.4772, 'city': 'Hyderabad'}
                
        else:
            st.warning(f"Location service returned status code: {response.status_code}")
            return {'lat': 17.4065, 'lon': 78.4772, 'city': 'Hyderabad'}
            
    except requests.RequestException as e:
        st.warning(f"Network error while fetching location: {str(e)}")
        return {'lat': 17.4065, 'lon': 78.4772, 'city': 'Hyderabad'}
    except Exception as e:
        st.warning(f"Unexpected error getting location: {str(e)}")
        return {'lat': 17.4065, 'lon': 78.4772, 'city': 'Hyderabad'}


def find_nearby_hospitals(lat, lon, radius=5000):
    """Find nearby hospitals using OpenStreetMap"""
    try:
        # Using Overpass API to get hospitals
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          way["amenity"="hospital"](around:{radius},{lat},{lon});
          relation["amenity"="hospital"](around:{radius},{lat},{lon});
        );
        out center;
        """
        response = requests.post(overpass_url, data=query)
        data = response.json()
        
        hospitals = []
        for element in data['elements']:
            if 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            else:
                lat = element.get('lat', 0)
                lon = element.get('lon', 0)
            
            name = element.get('tags', {}).get('name', 'Unknown Hospital')
            hospitals.append({
                'name': name,
                'lat': lat,
                'lon': lon
            })
        
        return hospitals
    except Exception as e:
        st.error(f"Error finding hospitals: {str(e)}")
        return []


def save_analysis_to_database(analysis_data):
    """
    Save analysis results to the database, handling potential missing columns.
    
    Args:
        analysis_data (dict): Dictionary containing analysis results
    
    Returns:
        bool: Success status of the database operation
    """
    if not supabase:
        st.warning("Database connection not available. Analysis results will not be saved.")
        return False
        
    try:
        # Prepare the data for saving
        data_to_save = {
            "patient_name": analysis_data.get("patient_name", "guest_patient"),
            "test_type": analysis_data.get("test_type", "Unknown Test"),
            "result": analysis_data.get("result", "No result"),
            "date": datetime.now().isoformat()
        }
        
        # Add confidence if it exists in analysis_data
        if "confidence" in analysis_data:
            data_to_save["confidence"] = analysis_data["confidence"]
            
        # Always try to set initial review status to false if the column exists
        data_to_save["reviewed"] = False
        
        # Add image data if it exists
        if "image_data" in analysis_data and analysis_data["image_data"] is not None:
            # Convert image to base64 if it's not already encoded
            if isinstance(analysis_data["image_data"], np.ndarray):
                # Convert numpy array to PIL Image
                pil_img = Image.fromarray(analysis_data["image_data"])
                # Convert PIL Image to base64
                buffer = io.BytesIO()
                pil_img.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                data_to_save["image_data"] = img_str
            elif isinstance(analysis_data["image_data"], str):
                # Image is already a base64 string
                data_to_save["image_data"] = analysis_data["image_data"]
            
        # Insert the data
        response = supabase.table('analysis_results').insert(data_to_save).execute()
        
        if not response.data:
            st.error("Failed to save analysis results")
            return False
            
        st.success("Analysis results saved successfully!")
        return True
        
    except Exception as e:
        st.error(f"Error saving analysis results: {str(e)}")
        
        # Provide helpful guidance if specific columns are missing
        error_message = str(e).lower()
        
        if "confidence" in error_message:
            st.info("""
            The 'confidence' column needs to be added to your database schema.
            Run this SQL in your Supabase dashboard:
            ```
            ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS confidence FLOAT;
            ```
            """)
            
        if "reviewed" in error_message:
            st.info("""
            The 'reviewed' column needs to be added to your database schema.
            Run this SQL in your Supabase dashboard:
            ```
            ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE;
            ```
            """)
            
        if "image_data" in error_message:
            st.info("""
            The 'image_data' column needs to be added to your database schema.
            Run this SQL in your Supabase dashboard:
            ```
            ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS image_data TEXT;
            ```
            """)
            
        return False


def create_medical_report(diagnosis, confidence, recommendations, patient_name="", detections=None, detection_count=0):
    """Generate a medical report"""
    now = datetime.now()
    report = {
        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
        "diagnosis": diagnosis,
        "confidence": f"{confidence:.2%}",
        "recommendations": recommendations,
        "patient_name": patient_name,
        "detections": detections or [],  # List of all detections with confidence scores
        "detection_count": detection_count,  # Total number of detections
        "disclaimer": "This is an AI-generated report for preliminary analysis only. Please consult a healthcare professional."
    }
    return report


def analyze_with_model(selected_model, image_data):
    """Simple prediction function following strict pattern"""
    try:
        # Define model paths
        model_paths = {
            "brain_tumor": "brain123.pt",
            "eye_disease": "eye.pt",
            "lung_cancer": "lung_cancer.pt",
            "bone_fracture": "bone.pt",
            "skin_disease": "skin345.pt",
            "diabetic_retinopathy": "xiaoru.pt",
            "tongue": "tongue(2).pt",
            "ulcer": "ulcer.pt",
            "nail": "nails.pt"
        }

        # Convert image data to numpy array
        if isinstance(image_data, bytes):
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif isinstance(image_data, Image.Image):
            image = np.array(image_data)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif isinstance(image_data, np.ndarray):
            image = image_data
        else:
            raise ValueError("Unsupported image format")

        # Load the model
        try:
            # First try loading with legacy mode
            model = YOLO(model_paths[selected_model], task='detect')
        except Exception as e1:
            try:
                # If that fails, try loading with custom config
                model = YOLO(model_paths[selected_model], task='detect', legacy=True)
            except Exception as e2:
                st.error(f"Error loading model: {str(e2)}")
                return None

        # Run inference with the numpy array
        try:
            results = model(image, verbose=False)  # Disable verbose output
        except Exception as e:
            st.error(f"Error running inference: {str(e)}")
            return None

        # Process results and save without labels
        for result in results:
            img = result.plot(labels=False)  # Draw results without labels
            
            # For Streamlit display, convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Display result image
            st.image(img_rgb, caption="Detection Result")

            # Display detection information in separate widgets
            if len(result.boxes) > 0:
                # Get all detections
                detections = []
                for box in result.boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    class_name = model.names[cls]
                    detections.append((class_name, conf))
                
                # Sort by confidence and get the highest confidence detection
                detections.sort(key=lambda x: x[1], reverse=True)
                best_detection = detections[0]
                
                # Count unique classes
                unique_classes = len(set(d[0] for d in detections))
                
                # Create columns for display
                col1, col2 = st.columns(2)
                
                # Display class information
                with col1:
                    st.metric(
                        label=f"Detected Diseases (Total: {unique_classes})",
                        value=best_detection[0],  # Show highest confidence class
                        delta=f"{len(detections)} Detection(s)"
                    )
                
                # Display confidence for the highest confidence detection
                with col2:
                    st.metric(
                        label="Highest Confidence Score",
                        value=f"{best_detection[1]:.2%}",
                        delta="Confidence Level"
                    )
                    st.progress(best_detection[1])
                
                # If there are multiple detections, show a summary
                if len(detections) > 1:
                    with st.expander("View All Detections"):
                        for class_name, conf in detections:
                            st.text(f"{class_name}: {conf:.2%}")
                
                # Save to database
                patient_name = st.session_state.get('email', 'guest_patient')
                test_type = f"{selected_model.replace('_', ' ').title()} Analysis"
                result_text = "Abnormal" if best_detection[1] > 0.5 else "Normal"
                
                # Save to database
                save_analysis_to_database(
                    {
                        "patient_name": patient_name,
                        "test_type": test_type,
                        "result": result_text,
                        "confidence": best_detection[1],
                        "image_data": img_rgb  # Add the analyzed image with detection boxes
                    }
                )
                
                # Add a section for generating PDF report
                st.subheader("Generate Medical Report")
                
                # Create a report section with detection information
                show_report_section(
                    diagnosis=f"{test_type}: {result_text}",
                    confidence=best_detection[1],
                    image=img_rgb,  # Use the annotated image with detection marks
                    detections=detections,
                    detection_count=len(detections)
                )
                
                # Hospital information section
                st.markdown("### 🏥 Nearby Hospitals")
                st.info("Location services are available based on your IP address.")
                
                # Get hospital info and display map
                hospital_info = show_hospital_info(result_text)
                folium_static(hospital_info['map'])
                
                # Emergency contacts section
                st.markdown("""
                ### 🚨 Emergency Contacts
                - **Ambulance**: 108
                - **Police**: 100
                - **Fire**: 101
                - **National Emergency**: 112
                - **SMVS Hospital**: +91-XXXXXXXXXX
                """)
                
            else:
                st.warning("No detections found")
                
                # Even if no detections, save a "Normal" result to database
                patient_name = st.session_state.get('email', 'guest_patient')
                test_type = f"{selected_model.replace('_', ' ').title()} Analysis"
                
                # Save to database with 0.0 confidence (no detection)
                save_analysis_to_database(
                    {
                        "patient_name": patient_name,
                        "test_type": test_type,
                        "result": "Normal",
                        "confidence": 0.0,
                        "image_data": img_rgb  # Add the analyzed image even though no detections were found
                    }
                )
                
                # Add a section for generating PDF report for normal case
                st.subheader("Generate Medical Report")
                
                # Create a report section for normal case with empty detections
                show_report_section(
                    diagnosis=f"{test_type}: Normal",
                    confidence=0.0,
                    image=img_rgb,
                    detections=[],
                    detection_count=0
                )

            return img_rgb

    except Exception as e:
        st.error(f"Error in prediction: {str(e)}")
        return None

# Add this at the beginning of main.py, after imports
def add_logout_button():
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.switch_page("login.py")

def main():
    # Check login status and role
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.switch_page("login.py")
    elif st.session_state.get('role') != "Patient":
        st.error("Unauthorized access")
        st.stop()
    
    # Show logout button
    add_logout_button()
    
    # Set video background
    video_background_path = "assets/journey-through-a-neuron-cell-network-inside-the-brain-SBV-337862610-preview.mp4"
    set_video_background(video_background_path)
    
    # Add welcome message in sidebar (already handled in sidebar logic)
    # st.sidebar.title(f"Welcome, {st.session_state.get('full_name', '')}")
    
    # Initialize language selection (already handled in sidebar logic)
    # if 'current_language' not in st.session_state:
    #     st.session_state.current_language = 'en'
    
    # Main content area
    st.markdown("## Medical Image Analysis")
    col1, col2 = st.columns([5, 3])

    with col1:
        # Input method tabs
        tab1, tab2 = st.tabs(["📸 Camera", "📁 Upload"])

        with tab1:
            # Camera input with custom styling
            img_file_camera = st.camera_input(
                "Take a picture",
                key="camera_input",
                help="Please capture the image in landscape orientation"
            )
            
            if img_file_camera:
                try:
                    # Read the image from camera
                    image = Image.open(img_file_camera)
                    
                    # Display captured image
                    st.image(image, caption="Captured Image", use_container_width=True)
                    
                    # Generate description using Google Vision API
                    description = generate_image_description(image)
                    st.markdown(f"<h1 style='color: #00d2ff;'>{description}</h1>", unsafe_allow_html=True)

                    # Model selection
                    selected_model = st.selectbox(
                        "Select Model for Analysis", 
                        list(detection_types.keys()),
                        key="camera_model_select"
                    )
                    
                    if st.button("Analyze", key="camera_analyze_button"):
                        img_byte_arr = io.BytesIO()
                        image.save(img_byte_arr, format='PNG')
                        img_bytes = img_byte_arr.getvalue()
                        
                        analyze_with_model(selected_model, img_bytes)

                except Exception as e:
                    st.error(f"Error processing camera image: {str(e)}")

        with tab2:
            # Custom upload message
            st.markdown("""
            <style>
            .modern-upload-text {
                text-align: center;
                padding: 0 0 10px 0;
                color: rgba(255, 255, 255, 0.9);
                font-weight: 500;
            }
            </style>
            <div class="modern-upload-text">
                📁 Upload a medical image (X-ray, MRI, CT, etc.)
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(" ", type=["jpg", "png", "jpeg"])  # Empty label as we've added custom text
            if uploaded_file:
                try:
                    # Read the file content
                    file_bytes = uploaded_file.read()
                    
                    # Create PIL Image from bytes
                    image = Image.open(io.BytesIO(file_bytes))
                    
                    # Display the image
                    st.image(image, caption="Uploaded Image", use_container_width=True)
                    
                    # Generate description using Google Vision API
                    description = generate_image_description(image)
                    st.markdown(f"<h1 style='color: #00d2ff;'>{description}</h1>", unsafe_allow_html=True)

                    # Model selection
                    selected_model = st.selectbox(
                        "Select Model for Analysis", 
                        list(detection_types.keys()),
                        key="upload_model_select"
                    )
                    
                    if st.button("Analyze", key="upload_analyze_button"):
                        analyze_with_model(selected_model, file_bytes)

                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")

    with col2:
        st.markdown("## AI Chat Assistant")

        # Chat input
        if prompt := st.chat_input("Ask me anything about your health..."):
            # Display current user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display current assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_chat_response(prompt)
                    st.markdown(response)


if __name__ == "__main__":
    main()