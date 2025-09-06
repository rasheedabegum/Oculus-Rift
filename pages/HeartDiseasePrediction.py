import streamlit as st
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import base64

# Add these functions for consistent styling with other pages
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

def get_feature_icon(feature):
    """Return appropriate Font Awesome icon for each feature"""
    icons = {
        "Age": "calendar-alt",
        "Gender": "venus-mars",
        "Cholesterol": "vial",
        "BloodPressure": "heart",
        "HeartRate": "heartbeat",
        "BMI": "weight",
        "Smoker": "smoking",
        "FamilyHistory": "users",
        "PhysicalActivity": "running",
        "AlcoholConsumption": "wine-glass-alt",
        "StressLevel": "brain"
    }
    return icons.get(feature, "dot-circle")

# Page configuration
st.set_page_config(
    page_title="Cardiac Risk Assessment",
    page_icon="♥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add Font Awesome for professional icons
st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)

# Add the same CSS styling as other pages with refinements
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
        background-color: rgba(0, 0, 0, 0.7) !important;
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

    /* Modern button styling */
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
    
    /* Style for number inputs and selectboxes */
    .stNumberInput, .stSelectbox {
        background-color: rgba(0, 0, 0, 0.5) !important;
    }
    
    /* Input fields styling */
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
    [data-baseweb*="select"] *:hover {
        border-color: #00d2ff !important;
        outline-color: #00d2ff !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
    }

    /* Style for the results container */
    .prediction-container {
        background-color: rgba(0, 0, 0, 0.7);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Override focus styles */
    *:focus {
        outline-color: #00d2ff !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
    }
    
    /* Set CSS variables for the whole document */
    :root {
        --primary: #00d2ff !important;
        --primary-color: #00d2ff !important;
        --accent-color: #00d2ff !important;
        --hover-color: #00c4f0 !important;
        --active-color: #3040c0 !important;
        --focus-color: #00d2ff !important;
        --error-color: #ff4b4b !important;
        --warning-color: #ffc400 !important;
        --success-color: #28a745 !important;
        --info-color: #00d2ff !important;
    }
    
    /* Professional card styling */
    .card {
        background-color: rgba(0, 0, 0, 0.6);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .card-header {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 10px;
        margin-bottom: 15px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    .title-with-icon {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .title-with-icon i {
        margin-right: 10px;
        color: #00d2ff;
        font-size: 28px;
    }
    
    .title-with-icon h1 {
        margin: 0;
        font-size: 32px;
    }
    
    /* Feature input styling */
    .feature-header {
        font-size: 18px;
        font-weight: 500;
        margin-bottom: 5px;
        color: #00d2ff;
    }
    
    /* Results styling */
    .risk-high {
        color: var(--error-color);
        font-weight: bold;
    }
    
    .risk-medium {
        color: var(--warning-color);
        font-weight: bold;
    }
    
    .risk-low {
        color: var(--success-color);
        font-weight: bold;
    }
    
    .disclaimer {
        font-style: italic;
        opacity: 0.8;
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(0, 0, 0, 0.5);
        margin-top: 20px;
    }

    /* Professional sidebar styling */
    .sidebar-section {
        padding: 15px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar-section:last-child {
        border-bottom: none;
    }
    
    .sidebar-header {
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Check login status
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("login.py")

# Add logout button
add_logout_button()

# Set video background
video_background_path = "assets/heartbeat-human-chest-with-beating-heart-medical-animation-SBV-347758189-preview.mp4"
set_video_background(video_background_path)

# Load the dataset with error handling
try:
    df = pd.read_csv("assets/heart_attack_dataset_processed.csv")
    X = df.drop(columns=["Outcome"])
    y = df["Outcome"]
except FileNotFoundError:
    st.error("Dataset file not found. Please make sure 'heart_attack_dataset_processed.csv' exists in the assets directory.")
    st.stop()
except Exception as e:
    st.error(f"Error loading dataset: {str(e)}")
    st.stop()

# Define selected features based on the provided dataset
selected_features = [
    "Age", "Gender", "Cholesterol", "BloodPressure", "HeartRate", "BMI",
    "Smoker", "FamilyHistory", "PhysicalActivity", "AlcoholConsumption", "StressLevel"
]

# Standardize only the selected features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X[selected_features])

# Train Logistic Regression model
model = LogisticRegression(C=1, solver='liblinear', max_iter=500, random_state=42)
model.fit(X_scaled, y)

def predict_cardiac_arrest(input_data):
    input_array = np.array(input_data).reshape(1, -1)
    input_scaled = scaler.transform(input_array)
    prediction = model.predict(input_scaled)[0]
    probability = model.predict_proba(input_scaled)[0][1]
    return prediction, probability

# Define feature ranges
feature_ranges = {
    "Age": (20, 100),
    "Gender": (0, 1),  # 0 = Female, 1 = Male
    "Cholesterol": (100, 400),
    "BloodPressure": (80, 200),
    "HeartRate": (50, 150),
    "BMI": (15, 40),
    "Smoker": (0, 1),  # 0 = Non-smoker, 1 = Smoker
    "FamilyHistory": (0, 1),  # 0 = No, 1 = Yes
    "PhysicalActivity": (1, 5),  # 1 = Sedentary, 5 = Highly Active
    "AlcoholConsumption": (0, 7),  # 0 = Never, 7 = Daily
    "StressLevel": (1, 10)
}

# Update the UI section with professional styling
st.markdown("""
    <div class="title-with-icon">
        <i class="fas fa-heartbeat"></i>
        <h1>Cardiac Risk Assessment</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="card">
        <div class="card-header">
            <i class="fas fa-info-circle"></i> Health Information Form
        </div>
        <p>Complete this assessment to evaluate your cardiac health based on key risk factors. The algorithm will analyze your information to provide a personalized risk assessment.</p>
    </div>
""", unsafe_allow_html=True)

# Create two columns for inputs
col1, col2 = st.columns(2)

inputs = []
for i, (feature, (min_val, max_val)) in enumerate(feature_ranges.items()):
    with col1 if i % 2 == 0 else col2:
        st.markdown(f"""<div class="feature-header"><i class="fas fa-{get_feature_icon(feature)}"></i> {feature}</div>""", unsafe_allow_html=True)
        if feature == "Gender":
            value = st.selectbox("Select", options=["Male", "Female"], key=f"select_{feature}")
            value = 1 if value == "Male" else 0
        elif feature == "AlcoholConsumption":
            value = st.selectbox("Times per week", options=list(range(min_val, max_val + 1)), key=f"select_{feature}")
        else:
            value = st.number_input(f"Range: {min_val}-{max_val}", min_value=min_val, max_value=max_val, 
                                  value=(min_val + max_val) // 2, key=f"input_{feature}")
        inputs.append(value)

# Center the predict button
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("<i class='fas fa-search'></i> Analyze Risk", use_container_width=True):
        prediction, probability = predict_cardiac_arrest(inputs)
        
        # Style the results
        st.markdown("""
            <div class='prediction-container'>
            <div class="card-header">
                <i class="fas fa-clipboard-check"></i> Assessment Results
            </div>
            """, unsafe_allow_html=True)
        
        if prediction == 1:
            st.markdown(f"""
                <div class="risk-high">
                    <i class="fas fa-exclamation-triangle"></i> High Risk Detected
                    <p>Risk Probability: {probability:.2%}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <h3><i class="fas fa-clipboard-list"></i> Recommendations:</h3>
                <ul>
                    <li><i class="fas fa-user-md"></i> Schedule an appointment with a cardiologist</li>
                    <li><i class="fas fa-heartbeat"></i> Monitor your blood pressure regularly</li>
                    <li><i class="fas fa-apple-alt"></i> Consider lifestyle modifications</li>
                </ul>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="risk-low">
                    <i class="fas fa-check-circle"></i> Low Risk Level
                    <p>Risk Probability: {probability:.2%}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
                <h3><i class="fas fa-clipboard-list"></i> Keep up the good work:</h3>
                <ul>
                    <li><i class="fas fa-heart"></i> Maintain your healthy lifestyle</li>
                    <li><i class="fas fa-calendar-check"></i> Continue regular check-ups</li>
                    <li><i class="fas fa-running"></i> Stay active and eat well</li>
                </ul>
                """, unsafe_allow_html=True)
            
        # Show free treatment information for both cases
        st.markdown("""
            <h3><i class="fas fa-hand-holding-medical"></i> Free Treatment Options:</h3>
            <h4>Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PMJAY)</h4>
            <p>This flagship health insurance scheme covers a wide range of cardiac procedures and treatments, including 
            surgeries and interventions for various heart conditions. Beneficiaries can avail themselves of free 
            treatment at empaneled hospitals nationwide.</p>
            
            <p><strong>Useful Links:</strong></p>
            <ul>
                <li><a href="https://nha.gov.in/PM-JAY"><i class="fas fa-external-link-alt"></i> PMJAY Official Website</a></li>
                <li><a href="https://nhm.assam.gov.in/schemes/free-operations-for-children-having-congenital-heart-disease"><i class="fas fa-external-link-alt"></i> Free Operations for Children with Congenital Heart Disease</a></li>
            </ul>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Add disclaimer at the bottom
st.markdown("""
    <div class="disclaimer">
        <i class="fas fa-stethoscope"></i> This is a screening tool only. Always consult healthcare professionals for medical advice.
    </div>
    """, unsafe_allow_html=True)
