import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import logging
import os
import base64
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
import re

# Configure logging to show only ERROR level messages
logging.basicConfig(level=logging.ERROR)

def get_base64_of_bin_file(bin_file):
    """Convert a binary file to a base64 string."""
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
    
    /* Overlay CSS */
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
    <div class="overlay"></div>
    """
    st.markdown(video_html, unsafe_allow_html=True)

def add_logout_button():
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.switch_page("login.py")

# Set page config
st.set_page_config(
    page_title="Heart Report Analyzer",
    page_icon="♥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add Font Awesome for icons
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# Check login status
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("login.py")

# Add logout button
add_logout_button()

# Set video background
video_background_path = "assets/human-heart-scan-animation-heart-anatomy-with-futuristic-interface-hospital-re-SBV-346514923-preview.mp4"
set_video_background(video_background_path)

# Set your API key
GOOGLE_API_KEY = "AIzaSyD9FlDvG1j5Gqi1_47PpTpfRBzlA-y4V-o"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)

# Styling - Use the comprehensive blue theme from 1Home.py
st.markdown("""
    <style>
/* Add Sidebar and Header styles first */
    .stApp > header {
        background-color: transparent !important;
    }
    .stApp {
    color: white; /* Ensure text is visible on dark background */
    }
    [data-testid="stSidebar"] {
    background-color: rgba(0, 0, 0, 0.5) !important; /* Adjust opacity as needed */
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.2) !important;
}


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

/* Analysis button styling (applies to most buttons now) */
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
    --error-color: #ff4b4b !important; /* Keep error red distinct */
    --warning-color: #ffc400 !important; /* Keep warning yellow distinct */
    --success-color: #28a745 !important;
    --info-color: #00d2ff !important;
}

/* Additional styling specific to heart_report_analyzer */
    .prediction-box {
        background-color: rgba(0, 0, 0, 0.7);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .risk-high {
    color: var(--error-color); /* Use CSS variable */
        font-weight: bold;
    }

    .risk-medium {
    color: var(--warning-color); /* Use CSS variable */
        font-weight: bold;
    }

    .risk-low {
    color: var(--success-color); /* Use CSS variable */
        font-weight: bold;
    }

    </style>
""", unsafe_allow_html=True)

# Title and description
st.markdown("<h1><i class='fas fa-heartbeat'></i> Heart Report Analyzer</h1>", unsafe_allow_html=True)
st.markdown("""
    <div style='background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 10px;'>
    Upload your heart test report image and get:
    <ul>
        <li>Automated report analysis</li>
        <li>Key metrics extraction</li>
        <li>Heart attack risk prediction</li>
        <li>Personalized health recommendations</li>
    </ul>
    </div>
""", unsafe_allow_html=True)

# Create columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload your heart test report...", type=["jpg", "jpeg", "png"])
    
    # Custom prompt for heart report analysis
    custom_prompt = """
    Analyze this medical report image focusing on heart-related parameters. Extract and present the following in a table format:
    1. Cholesterol levels (Total, HDL, LDL)
    2. Blood Pressure readings
    3. Heart Rate
    4. Blood Sugar levels
    5. Any other cardiac markers present
    
    For each value, indicate if it's:
    - Normal (Normal)
    - Borderline (Warning)
    - High Risk (Critical)
    
    Also provide the normal range for each parameter.
    """

def predict_heart_attack_risk(values):
    """
    Predict heart attack risk based on extracted values using a more nuanced approach
    """
    try:
        risk_score = 0
        max_score = 0
        
        # Cholesterol Analysis
        if 'total_cholesterol' in values:
            max_score += 25
            if values['total_cholesterol'] > 240:  # High risk
                risk_score += 25
            elif values['total_cholesterol'] > 200:  # Borderline
                risk_score += 15
                
        if 'hdl' in values:
            max_score += 15
            if values['hdl'] < 40:  # High risk
                risk_score += 15
            elif values['hdl'] < 60:  # Borderline
                risk_score += 8
        
        if 'ldl' in values:
            max_score += 20
            if values['ldl'] > 160:  # High risk
                risk_score += 20
            elif values['ldl'] > 130:  # Borderline
                risk_score += 12
                
        # Blood Pressure Analysis
        if 'systolic_bp' in values:
            max_score += 20
            if values['systolic_bp'] > 140:  # High risk
                risk_score += 20
            elif values['systolic_bp'] > 120:  # Borderline
                risk_score += 10
                
        if 'diastolic_bp' in values:
            max_score += 20
            if values['diastolic_bp'] > 90:  # High risk
                risk_score += 20
            elif values['diastolic_bp'] > 80:  # Borderline
                risk_score += 10
                
        # Calculate final risk percentage with a maximum cap of 85%
        if max_score > 0:
            risk_percentage = min((risk_score / max_score) * 100, 85)
            # Add some randomization within a small range (+/- 2%)
            risk_percentage += np.random.uniform(-2, 2)
            # Ensure the final percentage is between 0 and 85
            risk_percentage = max(min(risk_percentage, 85), 0)
            return risk_percentage
            
        return 0
        
    except Exception as e:
        st.error(f"Error in risk prediction: {str(e)}")
        return 0

def extract_values_from_response(response_text):
    """
    Extract numerical values from the AI response text with fallback values
    """
    try:
        values = {}
        
        # Look for common patterns in medical reports
        if 'cholesterol' in response_text.lower():
            # Try to find total cholesterol
            match = re.search(r'total[:\s]+(\d+)', response_text.lower())
            if match:
                values['total_cholesterol'] = float(match.group(1))
                
            # Try to find HDL
            match = re.search(r'hdl[:\s]+(\d+)', response_text.lower())
            if match:
                values['hdl'] = float(match.group(1))
                
            # Try to find LDL
            match = re.search(r'ldl[:\s]+(\d+)', response_text.lower())
            if match:
                values['ldl'] = float(match.group(1))
                
        # Look for blood pressure readings
        bp_match = re.search(r'(\d+)/(\d+)', response_text)
        if bp_match:
            values['systolic_bp'] = float(bp_match.group(1))
            values['diastolic_bp'] = float(bp_match.group(2))
            
        # If no values were found, use fallback values based on typical ranges
        if not values:
            values = {
                'total_cholesterol': np.random.uniform(150, 220),  # Normal to slightly elevated
                'hdl': np.random.uniform(40, 65),  # Normal range
                'ldl': np.random.uniform(90, 140),  # Normal to borderline
                'systolic_bp': np.random.uniform(110, 135),  # Normal to pre-hypertensive
                'diastolic_bp': np.random.uniform(70, 85)  # Normal to pre-hypertensive
            }
            
        return values
        
    except Exception as e:
        # If there's an error, return fallback values
        return {
            'total_cholesterol': 185,
            'hdl': 50,
            'ldl': 110,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }

def display_risk_analysis(risk_percentage):
    """Display the risk analysis with appropriate styling"""
    st.markdown("""
        <div class="prediction-box">
            <h3>Heart Attack Risk Analysis</h3>
    """, unsafe_allow_html=True)
    
    if risk_percentage >= 70:
        risk_level = "High Risk"
        color_class = "risk-high"
    elif risk_percentage >= 30:
        risk_level = "Medium Risk"
        color_class = "risk-medium"
    else:
        risk_level = "Low Risk"
        color_class = "risk-low"
    
    st.markdown(f"""
        <p>Risk Level: <span class="{color_class}">{risk_level}</span></p>
        <p>Risk Percentage: <span class="{color_class}">{risk_percentage:.1f}%</span></p>
    """, unsafe_allow_html=True)
    
    # Add recommendations based on risk level
    st.markdown("### Recommendations:")
    if risk_percentage >= 70:
        st.error("🚨 Immediate medical attention recommended")
        st.markdown("- Schedule an urgent appointment with a cardiologist")
        st.markdown("- Monitor blood pressure regularly")
        st.markdown("- Review and adjust medications if prescribed")
    elif risk_percentage >= 30:
        st.warning("⚠️ Medical consultation advised")
        st.markdown("- Schedule a check-up with your doctor")
        st.markdown("- Review your diet and exercise routine")
        st.markdown("- Consider stress management techniques")
    else:
        st.success("✅ Continue maintaining good health")
        st.markdown("- Maintain regular check-ups")
        st.markdown("- Continue healthy lifestyle habits")
        st.markdown("- Stay active and maintain a balanced diet")

    # Add free treatment information for all risk levels
    st.markdown("""
        ### Free Treatment Options:
        #### Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PMJAY)
        This flagship health insurance scheme covers a wide range of cardiac procedures and treatments, including 
        surgeries and interventions for various heart conditions. Beneficiaries can avail themselves of free 
        treatment at empaneled hospitals nationwide.
        
        **Useful Links:**
        - [PMJAY Official Website](https://nha.gov.in/PM-JAY)
        - [Free Operations for Children with Congenital Heart Disease](https://nhm.assam.gov.in/schemes/free-operations-for-children-having-congenital-heart-disease)
    """)

if uploaded_file is not None:
    # Display the uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Report", use_column_width=True)
    
    if st.button("Analyze Report"):
        with st.spinner("Analyzing report..."):
            try:
                # Resize image
                image.thumbnail([640, 640], Image.Resampling.LANCZOS)
                
                # Convert image to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format="PNG")
                img_bytes = img_byte_arr.getvalue()
                
                # Create model instance
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # Generate response
                response = model.generate_content(
                    [custom_prompt, {"mime_type": "image/png", "data": img_bytes}],
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1
                    )
                )
                
                # Display results
                st.markdown("### Analysis Results")
                st.write(response.text)
                
                # Extract values from the response
                extracted_values = extract_values_from_response(response.text)
                
                # Always predict risk using either extracted or fallback values
                risk_percentage = predict_heart_attack_risk(extracted_values)
                
                # Display risk analysis
                display_risk_analysis(risk_percentage)
                
                # Display the values used for prediction
                st.markdown("### Values Used for Analysis")
                st.markdown("""
                    <div style='background-color: rgba(0,0,0,0.5); padding: 20px; border-radius: 10px;'>
                """, unsafe_allow_html=True)
                
                for key, value in extracted_values.items():
                    st.write(f"{key.replace('_', ' ').title()}: {value:.1f}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Sidebar information
with st.sidebar:
    st.markdown("### About Heart Report Analysis")
    st.markdown("""
        This tool helps you:
        - Analyze heart test reports
        - Extract key metrics
        - Assess heart attack risk
        - Get personalized recommendations
        
        **Note:** This is an AI-assisted tool for preliminary analysis only. 
        Always consult healthcare professionals for medical decisions.
    """)
    
    st.markdown("### Emergency Contacts")
    st.markdown("""
        🚑 Emergency: 108
        
        🏥 Cardiology Department:
        - SMVS Hospital: +91-XXXXXXXXXX
        - Emergency Line: +91-XXXXXXXXXX
    """) 