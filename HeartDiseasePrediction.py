import streamlit as st
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import base64

# Add these functions for consistent styling with other pages
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
    </style>
    
    <div class="video-container">
        <video autoplay loop muted playsinline>
            <source src="data:video/mp4;base64,{get_base64_of_bin_file(video_path)}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </div>
    """
    st.markdown(video_html, unsafe_allow_html=True)

def add_logout_button():
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.switch_page("login.py")

# Page configuration
st.set_page_config(
    page_title="Cardiac Risk Predictor",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the CSS styling for sidebar and header
st.markdown("""
    <style>
    /* Make header transparent */
    .stApp > header {
        background-color: transparent !important;
    }
    
    .stApp {
        color: white; /* Ensure text is visible */
    }
    
    /* Make sidebar background semi-transparent black */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.7) !important; /* Using 0.7 as in original file, adjust if needed */
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Style sidebar content */
    [data-testid="stSidebar"] > div:first-child {
        background-color: transparent !important;
    }

    /* Make the sidebar text more visible */
    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Style the markdown separator */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* Keep existing page-specific styles */
    .stNumberInput input, .stSelectbox select {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }}
    .stNumberInput input:focus, .stSelectbox select:focus {{
        border-color: #00d2ff !important;
        box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important;
    }}
    .stButton > button {{
        background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%) !important;
        color: black;
        font-weight: bold;
        border-radius: 8px !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3) !important;
    }}
    .prediction-container {{
        background-color: rgba(0, 0, 0, 0.7);
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
    }}
    </style>
""", unsafe_allow_html=True)

# Check login status
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("login.py")

# Add logout button
add_logout_button()

# Set video background
video_background_path = "assets/dark-heart-of-space.3840x2160.mp4"
set_video_background(video_background_path)

# Load dataset for preprocessing reference
df = pd.read_csv(r"/Users/sreemadhav/SreeMadhav/Mhv CODES/MGIT/HealthProjectP7_adding_pages/heart_attack_dataset_processed.csv")
X = df.drop(columns=["Outcome"])
y = df["Outcome"]

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

# Update the UI section with better styling
st.title("🫀 Cardiac Risk Assessment")
st.markdown("""
    <div style='background-color: rgba(0, 0, 0, 0.5); padding: 20px; border-radius: 10px;'>
    <h3>Enter Your Health Information</h3>
    <p>This tool analyzes various health factors to assess your cardiac risk level.</p>
    </div>
""", unsafe_allow_html=True)

# Create two columns for inputs
col1, col2 = st.columns(2)

inputs = []
for i, (feature, (min_val, max_val)) in enumerate(feature_ranges.items()):
    with col1 if i % 2 == 0 else col2:
        st.markdown(f"#### {feature}")
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
    if st.button("🔍 Analyze Risk", use_container_width=True):
        prediction, probability = predict_cardiac_arrest(inputs)
        
        # Style the results
        st.markdown("""
            <div class='prediction-container'>
            """, unsafe_allow_html=True)
        
        if prediction == 1:
            st.error(f"⚠️ High Risk Detected\nRisk Probability: {probability:.2%}")
            st.markdown("""
                ### Recommendations:
                - Schedule an appointment with a cardiologist
                - Monitor your blood pressure regularly
                - Consider lifestyle modifications
                """)
        else:
            st.success(f"✅ Low Risk Level\nRisk Probability: {probability:.2%}")
            st.markdown("""
                ### Keep up the good work:
                - Maintain your healthy lifestyle
                - Continue regular check-ups
                - Stay active and eat well
                """)
            
        # Show free treatment information for both cases
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
        
        st.markdown("</div>", unsafe_allow_html=True)

# Add disclaimer at the bottom
st.markdown("""
    <div style='background-color: rgba(0, 0, 0, 0.5); padding: 10px; border-radius: 5px; margin-top: 20px;'>
    ⚕️ <em>This is a screening tool only. Always consult healthcare professionals for medical advice.</em>
    </div>
    """, unsafe_allow_html=True)
