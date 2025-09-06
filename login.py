import streamlit as st
import base64
from supabase import create_client
from datetime import datetime

# Must be the first Streamlit command
st.set_page_config(
    page_title="Oculus Rift Healthcare AI",
    page_icon="❤️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Supabase configuration
SUPABASE_URL = "https://xahzxcipqkckawzcyzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaHp4Y2lwcWtja2F3emN5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2NTY5ODMsImV4cCI6MjA1ODIzMjk4M30.J_ND_Jl3MwrR_Yy0v_YC7WwTGJE5dmlJuZcmhJwUvtY"

# Initialize Supabase client
try:
    supabase = create_client(
        supabase_url=SUPABASE_URL,
        supabase_key=SUPABASE_KEY
    )
except Exception as e:
    st.error(f"Failed to initialize Supabase client: {str(e)}")

def get_base64_of_bin_file(bin_file):
    """Convert a binary file to a base64 string."""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_video_background(video_path):
    """Set a video as the background for the Streamlit app."""
    try:
        video_base64 = get_base64_of_bin_file(video_path)
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
            background-color: rgba(0, 0, 0, 0.8);
            z-index: -1;
        }}
        </style>
        
        <div class="video-container">
            <video autoplay loop muted playsinline>
                <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        <div class="overlay"></div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Unable to load video background. Using default background.")
        # Set a fallback background color
        st.markdown("""
            <style>
            .stApp {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            }
            </style>
        """, unsafe_allow_html=True)

def get_image_base64(image_path):
    """Get base64 encoded image"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string

def send_otp(email):
    try:
        # Send OTP via email
        auth_response = supabase.auth.sign_in_with_otp({
            "email": email,
            "options": {
                "email_redirect_to": None,  # Disable magic links
                "data": {
                    "role": st.session_state.temp_role
                }
            }
        })
        return True, "OTP code sent to your email!"
    except Exception as e:
        return False, f"Error sending OTP: {str(e)}"

def verify_otp(email, otp_code):
    try:
        # Verify the OTP code
        auth_response = supabase.auth.verify_otp({
            "email": email,
            "token": otp_code,
            "type": "email"
        })
        
        if auth_response.user:
            try:
                # Try to get existing profile
                profile_response = supabase.table('profiles').select("*").eq('id', auth_response.user.id).execute()
                
                if not profile_response.data or len(profile_response.data) == 0:
                    # Create new profile if it doesn't exist
                    profile_data = {
                        "id": auth_response.user.id,
                        "email": email,
                        "role": st.session_state.get('temp_role', 'Patient'),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Insert new profile
                    insert_response = supabase.table('profiles').insert(profile_data).execute()
                    if insert_response.data:
                        return True, insert_response.data[0]
                    return False, "Failed to create profile"
                else:
                    # Return existing profile
                    return True, profile_response.data[0]
            except Exception as e:
                return False, f"Profile error: {str(e)}"
        return False, "Invalid OTP code"
    except Exception as e:
        return False, f"Verification error: {str(e)}"

def show_login_page():
    # Set video background first inside the function
    video_background_path = "assets/dark-heart-of-space.3840x2160.mp4"
    set_video_background(video_background_path)
    
    # Custom CSS
    st.markdown("""
        <style>
        /* Set CSS variables for blue theme */
        :root {{
            --primary-color: #00d2ff !important;
            --text-color: white !important;
            --background-color: transparent !important; /* Allow video background */
            --secondary-background-color: rgba(255, 255, 255, 0.1) !important;
            --error-color: #ff4b4b !important; /* Keep error red distinct, or change to blue if preferred: #00a0c7 */
            --warning-color: #ffc400 !important; /* Keep warning yellow distinct, or change to blue if preferred: #00d2ff */
            --success-color: #28a745 !important;
            --info-color: #00d2ff !important;
        }}

        /* Global styles */
        .stApp {{
            background: transparent !important; 
            color: var(--text-color);
        }}
        
        /* Make header fully invisible */
        .stApp > header {{
            display: none !important;
        }}
        
        /* Remove header completely */
        header[data-testid="stHeader"],
        [data-testid="stHeader"] {
            display: none !important;
            height: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }
        
        /* Ensure top toolbar is invisible */
        .st-emotion-cache-1dp5vir,
        .st-emotion-cache-z5fcl4,
        [data-testid="stToolbar"] {
            display: none !important;
            height: 0 !important;
            opacity: 0 !important;
            visibility: hidden !important;
        }

        /* Remove top decoration/separator line */
        .st-emotion-cache-7ym5gk,
        .st-emotion-cache-19rxjzo {
            display: none !important;
        }
        
        /* Fully transparent container */
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stAppViewContainer"],
        .st-emotion-cache-1wrcr25,
        .st-emotion-cache-6qob1r,
        .st-emotion-cache-uf99v8,
        .element-container,
        div.block-container,
        main[data-testid="stDecoration"],
        div[data-testid="StyledLinkIconContainer"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
        }

        /* Hide default Streamlit elements */
        #MainMenu, footer {{
            display: none !important;
        }}

        /* Make sidebar background semi-transparent black */
        [data-testid="stSidebar"] {{
            background-color: rgba(0, 0, 0, 0.5) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        [data-testid="stSidebar"] > div:first-child {{
             background-color: transparent !important;
        }}
        [data-testid="stSidebar"] * {{
             color: white !important; /* Ensure all sidebar text is white */
        }}
        [data-testid="stSidebar"] hr {{
             border-color: rgba(255, 255, 255, 0.2) !important;
        }}

        /* Input fields styling */
        [data-testid="stTextInput"] input,
        [data-testid="stPassword"] input,
        [data-testid="stTextArea"] textarea {{
            background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
        }}
        [data-testid="stTextInput"] input:focus,
        [data-testid="stPassword"] input:focus,
        [data-testid="stTextArea"] textarea:focus {{
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important; 
        }}

        /* Button styling */
        .stButton>button {{
            background: linear-gradient(90deg, #00d2ff 0%, #3a47d5 100%) !important; /* Blue gradient */
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }}
        .stButton>button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3) !important;
        }}
        .stButton>button:focus {{
             box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important; 
        }}

        /* Navigation buttons specific styling (lighter background) */
        [data-testid="column"] button {
            background: transparent !important;
            border: none !important;
            color: #808080 !important; /* Dimmed color for inactive */
            transition: color 0.3s ease !important;
            padding: 0.5rem 0 !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }
        [data-testid="column"] button:hover {
            color: #ffffff !important; /* White on hover */
            background: rgba(0, 210, 255, 0.1) !important;
            transform: none !important; /* Disable hover effect for nav buttons */
            box-shadow: none !important;
        }
        /* Add focus style for nav buttons */
        [data-testid="column"] button:focus {
           box-shadow: 0 0 0 0.2rem rgba(0, 210, 255, 0.25) !important; /* Blue shadow on focus */
           outline: none !important; /* Optional: remove default browser outline */
        }
        
        /* Highlight active navigation button */
        /* Requires logic to add 'active-nav-btn' class or similar */

        /* Radio button styling */
        [data-testid="stRadio"] label {{
            color: var(--text-color) !important;
        }}
        [data-testid="stRadio"] span[data-baseweb="radio"] > div:first-of-type {{
             border-color: rgba(255, 255, 255, 0.5) !important; 
        }}
        [data-testid="stRadio"] span[data-baseweb="radio"][data-checked="true"] > div:first-of-type {{
             border-color: var(--primary-color) !important;
             background-color: var(--primary-color) !important;
        }}
        
        /* Alert/Message styling (ensure blue theme) */
        [data-testid="stAlert"] {{
            border-radius: 8px !important;
        }}
        [data-baseweb="alert"][data-kind="error"] {{
            background-color: rgba(255, 75, 75, 0.2) !important; /* Keep subtle red background */
            color: #ff4b4b !important;
            border: 1px solid rgba(255, 75, 75, 0.5) !important;
        }}
         [data-baseweb="alert"][data-kind="warning"] {{
            background-color: rgba(255, 196, 0, 0.2) !important; /* Keep subtle yellow background */
            color: #ffc400 !important;
            border: 1px solid rgba(255, 196, 0, 0.5) !important;
        }}
         [data-baseweb="alert"][data-kind="success"] {{
            background-color: rgba(40, 167, 69, 0.2) !important; 
            color: #28a745 !important;
            border: 1px solid rgba(40, 167, 69, 0.5) !important;
        }}
         [data-baseweb="alert"][data-kind="info"] {{
            background-color: rgba(0, 210, 255, 0.1) !important; 
            color: var(--primary-color) !important;
            border: 1px solid rgba(0, 210, 255, 0.3) !important;
        }}
        
        /* Other elements */
        .main-container, .logo-container, .login-form {{
             background: transparent !important; /* Ensure containers don't block video */
        }}
        .logo-container img {{ width: 250px; }}
        .subtitle {{ color: rgba(255, 255, 255, 0.7); }}
        .form-label {{ color: var(--text-color); }}

        </style>
    """, unsafe_allow_html=True)

    # Initialize session state
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "login"
    if 'verification_sent' not in st.session_state:
        st.session_state.verification_sent = False
    if 'email' not in st.session_state:
        st.session_state.email = ""

    # Show logo
    st.markdown(f"""
        <div class="main-container">
            <div class="logo-container">
                <img src="data:image/png;base64,{get_image_base64('logo.png')}" alt="FireML Logo">
                <p class="subtitle">Your Health, Our Priority</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Login", key="login_btn", use_container_width=True):
            st.session_state.active_tab = "login"
    with col2:
        if st.button("Register", key="register_btn", use_container_width=True):
            st.session_state.active_tab = "register"
    with col3:
        if st.button("Guest", key="guest_btn", use_container_width=True):
            st.session_state.active_tab = "guest"

    # Show different content based on active tab
    if st.session_state.active_tab in ["login", "register"]:
        st.markdown('<p class="form-label">Choose your role</p>', unsafe_allow_html=True)
        role = st.radio("Select Role", ["Patient", "Doctor"], horizontal=True, label_visibility="collapsed")
        st.session_state.temp_role = role
        
        if not st.session_state.verification_sent:
            email = st.text_input("Email Address", key="email_input", value=st.session_state.email, 
                             label_visibility="collapsed", placeholder="Enter your email")
            # Moved OTP input box here to show it regardless of verification status
            otp_code = st.text_input("OTP Code", label_visibility="collapsed", 
                                   placeholder="Enter 6-digit OTP code")
            
            if role == "Doctor":
                if st.button("Login as Doctor (Test Mode)", use_container_width=True):
                    # Simulate successful login for Doctor
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = "test_doctor_id"  # Simulated user ID
                    st.session_state['role'] = "Doctor"
                    st.session_state['email'] = email
                    st.session_state['full_name'] = "Test Doctor"  # Simulated full name
                    st.switch_page("pages/doctor_dashboard_new.py")
            
            if st.button("Send OTP Code", use_container_width=True):
                if email:
                    success, message = send_otp(email)
                    if success:
                        st.session_state.verification_sent = True
                        st.session_state.email = email
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter your email")
        else:
            otp_code = st.text_input("OTP Code", label_visibility="collapsed", 
                                   placeholder="Enter 6-digit OTP code")
            
            col1, col2 = st.columns([2,1])
            with col1:
                if st.button("Verify OTP", use_container_width=True):
                    if otp_code:
                        success, result = verify_otp(st.session_state.email, otp_code)
                        if success:
                            st.success(f"Welcome, {st.session_state.email}!")
                            st.session_state['logged_in'] = True
                            st.session_state['user_id'] = result['id']
                            st.session_state['role'] = result['role']
                            st.session_state['email'] = result['email']
                            
                            # Redirect to the appropriate dashboard based on role
                            if result['role'] == "Doctor":
                                st.session_state['full_name'] = result.get('full_name', 'Doctor')  # Assuming full_name is part of the profile
                                st.switch_page("pages/doctor_dashboard_new.py")
                            else:
                                st.switch_page("pages/1Home.py")
                        else:
                            st.error(result)
                    else:
                        st.warning("Please enter the OTP code")
            
            with col2:
                if st.button("Resend OTP", use_container_width=True):
                    success, message = send_otp(st.session_state.email)
                    if success:
                        st.success("New OTP code sent!")
                    else:
                        st.error(message)

    elif st.session_state.active_tab == "guest":
        st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h3 style="color: white;">Quick Access</h3>
                <p style="color: rgba(255,255,255,0.8);">
                    Experience basic features without registration
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Continue as Guest", use_container_width=True):
            st.session_state['logged_in'] = True
            st.session_state['email'] = 'guest'
            st.session_state['role'] = 'Patient'
            st.switch_page("pages/1Home.py")

    st.markdown("""
    <div class='prediction-container'>
    <div class="card-header">
        Assessment Results
    </div>
    """, unsafe_allow_html=True)

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    
    if not st.session_state['logged_in']:
        show_login_page()

if __name__ == '__main__':
    main() 