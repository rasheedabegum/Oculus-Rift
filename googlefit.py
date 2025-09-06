import streamlit as st
import base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, timezone, timedelta
import json
import time

# Update scopes to include all fitness data
SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.location.read'
]

# Load credentials and authenticate
def authenticate():
    try:
        client_secrets_path = "/Users/sreemadhav/SreeMadhav/Mhv CODES/MGIT/HealthProjectP7_adding_pages/pages/client_secret_247707654993-570ulm9dcot7tn929ngnci7dl2f6tdp9.apps.googleusercontent.com-2.json"
        
        with open(client_secrets_path, 'r') as f:
            client_secrets = json.load(f)
        
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path,
            SCOPES,
            redirect_uri='http://localhost:8085'  # Specify the exact redirect URI
        )
        
        # Use a single, consistent port that matches your Google Cloud Console settings
        try:
            creds = flow.run_local_server(
                port=8085,
                success_message='The authentication flow has completed. You may close this window.',
                open_browser=True
            )
            return creds
        except Exception as e:
            st.error(f"Server error: {str(e)}")
            return None
                
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

# Fetch fitness data
def get_fitness_data():
    try:
        # Only authenticate once at startup
        if not hasattr(get_fitness_data, 'creds'):
            get_fitness_data.creds = authenticate()
            get_fitness_data.last_hr = None
            get_fitness_data.last_time = None
            print('\033[2J\033[H', end='')  # Clear screen after auth
        
        service = build('fitness', 'v1', credentials=get_fitness_data.creds)

        # Set time range for last 10 seconds
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(seconds=10)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            }],
            "bucketByTime": {"durationMillis": 10000},
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        response = service.users().dataset().aggregate(
            userId="me",
            body=body
        ).execute()

        latest_hr = None
        latest_time = None
        
        # Find the latest heart rate reading
        for bucket in reversed(response.get("bucket", [])):
            bucket_time = datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000, timezone.utc)
            local_time = bucket_time.astimezone()
            
            for dataset in bucket.get("dataset", []):
                points = dataset.get("point", [])
                if points:
                    for point in points:
                        values = point.get("value", [])
                        if values:
                            hr_value = values[0].get('fpVal')
                            if hr_value:
                                latest_hr = hr_value
                                latest_time = local_time
                                break
                if latest_hr:
                    break
            if latest_hr:
                break

        # Only update display if we have new data
        if latest_hr and (latest_hr != get_fitness_data.last_hr or 
                         latest_time != get_fitness_data.last_time):
            print('\033[2J\033[H', end='')  # Clear screen
            print("Real-time Heart Rate Monitor")
            print("--------------------------------------------------------------")
            print(f"Heart Rate: {latest_hr:.0f} BPM at {latest_time.strftime('%I:%M:%S %p')}")
            print("\nMonitoring for new readings...")  # Add status message
            
            # Store latest values
            get_fitness_data.last_hr = latest_hr
            get_fitness_data.last_time = latest_time
            return True  # Indicate we got new data
        
        return False  # No new data

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def monitor_latest_data():
    print('\033[2J\033[H', end='')  # Clear screen once at start
    print("Real-time Heart Rate Monitor")
    print("--------------------------------------------------------------")
    print("Waiting for heart rate data...")
    
    consecutive_failures = 0
    while True:
        if get_fitness_data():
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures > 30:  # After 30 seconds of no data
                print('\033[2J\033[H', end='')
                print("Real-time Heart Rate Monitor")
                print("--------------------------------------------------------------")
                print("Waiting for new heart rate data...")
                consecutive_failures = 0
        
        time.sleep(1)  # Check every second for new data

# Add your existing background and logout functions
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

def add_logout_button():
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.switch_page("login.py")

# Add page config and styling
st.set_page_config(
    page_title="Google Fit Integration",
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
    
    /* Keep existing terminal styling */
    .terminal {
        background-color: rgba(0, 0, 0, 0.9);
        border-radius: 5px;
        padding: 20px;
        font-family: 'Courier New', monospace;
        color: #00ff00;
        margin: 10px 0;
        white-space: pre;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

# Check login status
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.switch_page("login.py")

# Add logout button
add_logout_button()

# Set video background
video_background_path = "assets/looping-heart-ekg-graphic-SBV-300338919-preview.mp4"
set_video_background(video_background_path)

# Add title and description
st.title("Google Fit Integration")
st.markdown("""
    <div style='background-color: rgba(0, 0, 0, 0.5); padding: 20px; border-radius: 10px;'>
    <h3>Welcome to Google Fit Integration</h3>
    <p>Click "Start Monitoring" to connect to Google Fit and view your real-time heart rate data.</p>
    <ul>
        <li>Connects to your Google Fit account</li>
        <li>Shows real-time heart rate monitoring</li>
        <li>Secure and private connection</li>
    </ul>
    </div>
""", unsafe_allow_html=True)

# Initialize session state for monitoring
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

# Create columns for buttons
col1, col2 = st.columns([1, 4])

with col1:
    if not st.session_state.monitoring_active:
        if st.button("Start Monitoring"):
            st.session_state.monitoring_active = True
            try:
                with st.spinner("Connecting to Google Fit..."):
                    creds = authenticate()
                    if creds:
                        st.session_state.creds = creds
                        st.success("Successfully connected to Google Fit!")
            except Exception as e:
                st.error(f"Error connecting to Google Fit: {str(e)}")
                st.session_state.monitoring_active = False
    else:
        if st.button("Stop Monitoring"):
            st.session_state.monitoring_active = False
            st.success("Monitoring stopped")

# Modify the monitoring section
if st.session_state.monitoring_active and hasattr(st.session_state, 'creds'):
    # Create containers for the terminal output
    terminal = st.container()
    with terminal:
        st.markdown("""
        <style>
        .terminal {
            background-color: rgba(0, 0, 0, 0.9);
            border-radius: 5px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            color: #00ff00;
            margin: 10px 0;
            white-space: pre;
            line-height: 1.5;
        }
        </style>
        """, unsafe_allow_html=True)
        
        output_container = st.empty()
        
        try:
            service = build('fitness', 'v1', credentials=st.session_state.creds)
            
            # Get current time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(seconds=10)

            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.heart_rate.bpm",
                    "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
                }],
                "bucketByTime": {"durationMillis": 10000},
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000)
            }
            
            response = service.users().dataset().aggregate(
                userId="me",
                body=body
            ).execute()

            latest_hr = None
            latest_time = None
            
            # Find the latest heart rate reading
            for bucket in reversed(response.get("bucket", [])):
                bucket_time = datetime.fromtimestamp(int(bucket['startTimeMillis'])/1000, timezone.utc)
                local_time = bucket_time.astimezone()
                
                for dataset in bucket.get("dataset", []):
                    points = dataset.get("point", [])
                    if points:
                        for point in points:
                            values = point.get("value", [])
                            if values:
                                hr_value = values[0].get('fpVal')
                                if hr_value:
                                    latest_hr = hr_value
                                    latest_time = local_time
                                    break
                    if latest_hr:
                        break
                if latest_hr:
                    break

            if latest_hr:
                terminal_output = f"""
<div class="terminal">
Real-time Heart Rate Monitor
--------------------------------------------------------------
Heart Rate: {latest_hr:.0f} BPM at {latest_time.strftime('%I:%M:%S %p')}

Monitoring for new readings...
</div>
"""
            else:
                terminal_output = """
<div class="terminal">
Real-time Heart Rate Monitor
--------------------------------------------------------------
Waiting for new heart rate data...
</div>
"""
            
            output_container.markdown(terminal_output, unsafe_allow_html=True)
            
            # Use a button to refresh instead of automatic rerun
            col1, col2, col3 = st.columns([1, 8, 1])
            with col1:
                if st.button("🔄", key="refresh"):
                    st.rerun()
            
            # Add auto-refresh using meta tag instead of JavaScript
            st.markdown("""
                <meta http-equiv="refresh" content="1">
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error in monitoring: {str(e)}")
            st.session_state.monitoring_active = False

# Remove the automatic monitoring start
if __name__ == "__main__":
    pass  # Remove the automatic monitor_latest_data() call