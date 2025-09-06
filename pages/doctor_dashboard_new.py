import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import base64
import time
import os
import requests
import socket
import json
import io
from PIL import Image

# Initialize Supabase client
SUPABASE_URL = "https://xahzxcipqkckawzcyzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhhaHp4Y2lwcWtja2F3emN5emNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI2NTY5ODMsImV4cCI6MjA1ODIzMjk4M30.J_ND_Jl3MwrR_Yy0v_YC7WwTGJE5dmlJuZcmhJwUvtY"

# Create supabase client without immediately connecting
supabase = None

# Create a session state variable to force offline mode if needed
if 'force_offline_mode' not in st.session_state:
    st.session_state.force_offline_mode = False

# Test internet connectivity function - multiple methods
def check_internet():
    if st.session_state.force_offline_mode:
        return False
        
    # Method 1: Socket connection to a reliable DNS
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
        
    # Method 2: HTTP request to a reliable service
    try:
        response = requests.get("https://www.google.com", timeout=3)
        return True
    except:
        pass
    
    # Method 3: Try connecting to Supabase directly
    try:
        requests.get(SUPABASE_URL, timeout=3)
        return True
    except:
        return False

# Create mock data for offline mode
def get_mock_patients():
    """Return mock patient data for offline mode"""
    return [
        {"id": 1, "name": "John Doe", "age": 45, "condition": "Hypertension", "last_visit": "2023-04-15"},
        {"id": 2, "name": "Jane Smith", "age": 32, "condition": "Diabetes", "last_visit": "2023-04-10"},
        {"id": 3, "name": "Robert Johnson", "age": 58, "condition": "Arthritis", "last_visit": "2023-03-22"},
        {"id": 4, "name": "Emily Williams", "age": 27, "condition": "Asthma", "last_visit": "2023-04-05"},
        {"id": 5, "name": "Michael Brown", "age": 41, "condition": "Migraine", "last_visit": "2023-04-18"}
    ]

def get_mock_analysis_results():
    """Return mock analysis results for offline mode"""
    return [
        {
            "id": 1, 
            "patient_name": "John Doe", 
            "test_type": "Brain Tumor Analysis", 
            "result": "Normal", 
            "date": "2023-04-15T14:30:00", 
            "confidence": "0.85",
            "reviewed": True
        },
        {
            "id": 2, 
            "patient_name": "Jane Smith", 
            "test_type": "X-Ray Analysis", 
            "result": "Abnormal", 
            "date": "2023-04-10T09:15:00", 
            "confidence": "0.92",
            "reviewed": True
        },
        {
            "id": 3, 
            "patient_name": "Robert Johnson", 
            "test_type": "CT Scan Analysis", 
            "result": "Normal", 
            "date": "2023-03-22T11:45:00", 
            "confidence": "0.78",
            "reviewed": False
        },
        {
            "id": 4, 
            "patient_name": "guest_patient", 
            "test_type": "Diabetic Retinopathy Analysis", 
            "result": "Abnormal", 
            "date": "2023-04-05T16:20:00", 
            "confidence": "0.88",
            "reviewed": False
        },
        {
            "id": 5, 
            "patient_name": "guest_12345", 
            "test_type": "Skin Disease Analysis", 
            "result": "Normal", 
            "date": "2023-04-18T10:05:00", 
            "confidence": "0.76",
            "reviewed": False
        }
    ]

# Test Supabase connectivity function
def check_supabase():
    if st.session_state.force_offline_mode:
        return False, "Offline mode is enabled"
        
    try:
        # Try a direct HTTP request to Supabase
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/?apikey={SUPABASE_KEY}",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            },
            timeout=5
        )
        if response.status_code < 300:
            return True, "Connected successfully"
        else:
            return False, f"HTTP error: {response.status_code}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

# Try to initialize Supabase
def initialize_supabase():
    global supabase
    
    if st.session_state.force_offline_mode:
        return False, "Offline mode is enabled"
        
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return True, "Connected successfully"
    except Exception as e:
        return False, f"Error initializing Supabase client: {str(e)}"

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

def get_image_from_base64(base64_string):
    """Convert base64 string back to PIL Image for display"""
    try:
        if base64_string:
            image_bytes = base64.b64decode(base64_string)
            return Image.open(io.BytesIO(image_bytes))
        return None
    except Exception as e:
        st.error(f"Error decoding image: {str(e)}")
        return None

def display_schema_update_guidance():
    """Display guidance for updating database schema if needed"""
    st.warning("""
    ⚠️ Database Schema Update Required
    
    To properly store and display analyzed images, you need to add an image_data column to your 'analysis_results' table in Supabase:
    
    1. Go to your Supabase dashboard
    2. Navigate to the SQL Editor
    3. Run the following SQL query:
    
    ```sql
    ALTER TABLE analysis_results 
    ADD COLUMN IF NOT EXISTS image_data TEXT;
    ```
    
    Then refresh this page to see the images in your analysis results.
    """)

def main():
    # Set page configuration to always show the sidebar
    st.set_page_config(
        page_title="Doctor's Dashboard",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"  # Always show the sidebar
    )

    # Add CSS styling for sidebar and header
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
            background-color: rgba(0, 0, 0, 0.7) !important; 
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
        
        /* You might want to add the blue theme CSS variables and button styles here too 
           if you want consistent button/element styling across all pages */
        :root {
            --primary-color: #00d2ff !important;
            /* ... other variables ... */
        }
        [data-testid="stButton"] > button {
             background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%) !important;
             /* ... other button styles ... */
        }
        /* ... other shared styles ... */

        </style>
    """, unsafe_allow_html=True)

    # Check login status and role
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.switch_page("login.py")
    elif st.session_state.get('role') != "Doctor":
        st.error("Unauthorized access")
        st.stop()
    
    # Add logout button
    add_logout_button()
    
    st.title(f"Welcome Dr. {st.session_state.get('full_name', '')}")
    
    # Set video background
    video_background_path = "assets/neurons-structure-sending-electric-impulses-and-communicating-each-other-3d-an-SBV-346464687-preview.mp4"
    set_video_background(video_background_path)

    # Store doctor's email from session state
    doctor_email = st.session_state.get('email', 'test_doctor@example.com')

    # Sidebar
    st.sidebar.title("Doctor's Dashboard")
    
    # Check connectivity silently without showing status
    internet_connected = check_internet()
    if not internet_connected and not st.session_state.force_offline_mode:
        st.warning("Internet connection not available. Switch to offline mode to use the app with mock data.")
    
    # Initialize Supabase silently without showing status
    if internet_connected and not st.session_state.force_offline_mode:
        supabase_direct, direct_msg = check_supabase()
        supabase_client, client_msg = initialize_supabase()
    
    # Menu selection - reordered with Analysis Results first
    menu = st.sidebar.selectbox(
        "Menu",
        ["Analysis Results", "Patient Records", "Download Report", "Settings"]
    )
    
    if menu == "Patient Records":
        st.header("Patient Records")
        
        # Get patients data - either from Supabase or mock data
        if st.session_state.force_offline_mode or not internet_connected or not supabase:
            st.info("📱 Working in OFFLINE MODE with mock data")
            patients = get_mock_patients()
        else:
            try:
                response = supabase.table('patients').select('*').execute()
                patients = response.data
            except Exception as e:
                st.error(f"Error retrieving patients: {str(e)}")
                st.info("Falling back to offline mode with mock data")
                patients = get_mock_patients()

        # Display patients data
        if patients:
            df_patients = pd.DataFrame(patients)
            st.dataframe(df_patients)
            
            # Only show delete functionality if there are patients and not in offline mode
            if not st.session_state.force_offline_mode and internet_connected and supabase:
                delete_patient_id = st.number_input("Delete Patient ID", min_value=1, max_value=len(patients), step=1)
                if st.button("Delete Patient"):
                    try:
                        if delete_patient_id <= len(patients):
                            patient_id = patients[delete_patient_id - 1]['id']
                            supabase.table('patients').delete().eq('id', patient_id).execute()
                            st.success("Patient deleted successfully!")
                            st.rerun()  # Refresh the page to show updated data
                        else:
                            st.error("Invalid Patient ID.")
                    except Exception as e:
                        st.error(f"Error deleting patient: {str(e)}")
        else:
            st.info("No patient records found. Add a patient using the form below.")

        # Form to add a new patient
        with st.form("Add Patient"):
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=0)
            condition = st.text_input("Condition")
            last_visit = st.date_input("Last Visit", datetime.today())
            submit_button = st.form_submit_button("Add Patient")
            if submit_button:
                if st.session_state.force_offline_mode or not internet_connected or not supabase:
                    st.info("In offline mode, data is not saved to the database")
                    st.success("(Mock) Patient added successfully!")
                else:
                    try:
                        new_patient = {
                            "name": name,
                            "age": age,
                            "condition": condition,
                            "last_visit": last_visit.isoformat()  # Convert date to string
                        }
                        supabase.table('patients').insert(new_patient).execute()
                        st.success("Patient added successfully!")
                        st.rerun()  # Refresh the page to show updated data
                    except Exception as e:
                        st.error(f"Error adding patient: {str(e)}")

    elif menu == "Analysis Results":
        st.header("Analysis Results")
        
        # Get analysis results - either from Supabase or mock data
        if st.session_state.force_offline_mode or not internet_connected or not supabase:
            st.info("📱 Working in OFFLINE MODE with mock data")
            analysis_results = get_mock_analysis_results()
        else:
            try:
                # Get all analysis results, ordered by date (newest first) with additional columns
                response = supabase.table('analysis_results').select('*').order('date', desc=True).execute()
                analysis_results = response.data
                
                # Check if image_data column exists in the schema
                missing_columns = []
                sample_result = analysis_results[0] if analysis_results else {}
                if 'image_data' not in sample_result:
                    missing_columns.append("image_data")
                    display_schema_update_guidance()
                
            except Exception as e:
                st.error(f"Error retrieving analysis results: {str(e)}")
                st.info("Falling back to offline mode with mock data")
                analysis_results = get_mock_analysis_results()

        # Display analysis results with improved UI
        if analysis_results:
            # Add filter options
            st.subheader("Filter Results")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filter by patient type (guest or registered)
                patient_filter = st.selectbox(
                    "Patient Type",
                    ["All", "Guest", "Registered"],
                    key="patient_filter"
                )
            
            with col2:
                # Filter by test type
                test_types = ["All"] + list(set(result.get('test_type', '') for result in analysis_results))
                test_filter = st.selectbox(
                    "Test Type",
                    test_types,
                    key="test_filter"
                )
                
            with col3:
                # Filter by review status
                review_filter = st.selectbox(
                    "Review Status",
                    ["All", "Reviewed", "Not Reviewed"],
                    key="review_filter"
                )
            
            # Apply filters
            filtered_results = []
            for result in analysis_results:
                # Check if it's a guest user
                is_guest = "guest" in str(result.get('patient_name', '')).lower()
                
                # Patient type filter
                if patient_filter == "Guest" and not is_guest:
                    continue
                if patient_filter == "Registered" and is_guest:
                    continue
                
                # Test type filter
                if test_filter != "All" and result.get('test_type', '') != test_filter:
                    continue
                
                # Review status filter
                reviewed = result.get('reviewed', False)
                if review_filter == "Reviewed" and not reviewed:
                    continue
                if review_filter == "Not Reviewed" and reviewed:
                    continue
                
                filtered_results.append(result)
            
            # Convert to DataFrame for display
            if filtered_results:
                # Create a more informative DataFrame
                df_data = []
                for result in filtered_results:
                    # Format date
                    date_str = result.get('date', '')
                    if date_str:
                        try:
                            # Try to parse ISO format
                            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_date = date_str
                    else:
                        formatted_date = "Unknown"
                    
                    # Determine patient type
                    patient_name = result.get('patient_name', '')
                    patient_type = "Guest" if "guest" in str(patient_name).lower() else "Registered"
                    
                    # Confidence score (handle missing field)
                    confidence = result.get('confidence', 'N/A')
                    if confidence != 'N/A' and not isinstance(confidence, str):
                        confidence = f"{confidence:.2f}"
                    
                    # Review status (handle missing field)
                    if 'reviewed' in result:
                        reviewed = "✅" if result.get('reviewed', False) else "❌"
                    else:
                        reviewed = "⚠️"
                    
                    df_data.append({
                        "ID": result.get('id', ''),
                        "Date": formatted_date,
                        "Patient": patient_name,
                        "Type": patient_type,
                        "Test Type": result.get('test_type', ''),
                        "Result": result.get('result', ''),
                        "Confidence": confidence,
                        "Reviewed": reviewed
                    })
                
                df_analysis = pd.DataFrame(df_data)
                st.dataframe(df_analysis, use_container_width=True)
                
                # Check if table schema needs updates
                missing_columns = []
                sample_result = filtered_results[0] if filtered_results else {}
                if 'confidence' not in sample_result:
                    missing_columns.append("confidence")
                if 'reviewed' not in sample_result:
                    missing_columns.append("reviewed")
                    
                if missing_columns:
                    st.warning(f"""
                    ⚠️ Your database schema is missing some columns: {', '.join(missing_columns)}
                    
                    To fix this issue, you need to add these columns to your 'analysis_results' table in Supabase:
                    1. Go to your Supabase dashboard
                    2. Navigate to the SQL Editor
                    3. Run the following SQL query:
                    
                    ```sql
                    ALTER TABLE analysis_results 
                    ADD COLUMN IF NOT EXISTS confidence TEXT,
                    ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE;
                    ```
                    """)
                
                # Toggle review status only if the column exists
                # Show detail view and mark as reviewed
                st.subheader("Review Analysis")
                selected_id = st.selectbox(
                    "Select Analysis ID to Review",
                    [result.get('id', '') for result in filtered_results],
                    format_func=lambda x: f"ID: {x}"
                )
                
                # Find selected result
                selected_result = next((r for r in filtered_results if r.get('id', '') == selected_id), None)
                if selected_result:
                    # Create two columns for image and details
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # Display analysis details
                        st.write("### Analysis Details")
                        
                        # Format the details for better display
                        display_data = {
                            "Patient Name": selected_result.get('patient_name', 'Unknown'),
                            "Test Type": selected_result.get('test_type', 'Unknown'),
                            "Result": selected_result.get('result', 'Unknown'),
                            "Date": selected_result.get('date', 'Unknown'),
                            "Confidence": selected_result.get('confidence', 'N/A')
                        }
                        
                        # Display as a clean table
                        for key, value in display_data.items():
                            st.markdown(f"**{key}:** {value}")
                        
                        # Toggle review status if column exists
                        if 'reviewed' in selected_result:
                            is_reviewed = selected_result.get('reviewed', False)
                            review_label = "Mark as Unreviewed" if is_reviewed else "Mark as Reviewed"
                            
                            if st.button(review_label):
                                try:
                                    # Update review status in database
                                    supabase.table('analysis_results').update(
                                        {"reviewed": not is_reviewed}
                                    ).eq('id', selected_id).execute()
                                    
                                    st.success(f"Successfully marked as {'unreviewed' if is_reviewed else 'reviewed'}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating review status: {str(e)}")
                                    
                                    # Show guidance if there's a column error
                                    if "Could not find" in str(e) and "column" in str(e):
                                        st.warning("""
                                        ⚠️ Your database schema is missing the 'reviewed' column.
                                        
                                        To fix this issue, you need to add this column to your 'analysis_results' table in Supabase:
                                        1. Go to your Supabase dashboard
                                        2. Navigate to the SQL Editor
                                        3. Run the following SQL query:
                                        
                                        ```sql
                                        ALTER TABLE analysis_results 
                                        ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE;
                                        ```
                                        """)
                        else:
                            st.warning("""
                            ⚠️ Cannot toggle review status because the 'reviewed' column is missing in your database.
                            
                            To fix this issue, add the column using SQL (see warning above).
                            """)
                    
                    with col2:
                        # Display the analysis image if available
                        st.write("### Analysis Image")
                        
                        if 'image_data' in selected_result and selected_result['image_data']:
                            # Convert base64 string back to image and display
                            image = get_image_from_base64(selected_result['image_data'])
                            if image:
                                st.image(image, caption="Patient Analysis Image", use_container_width=True)
                            else:
                                st.warning("Could not decode the image data")
                        else:
                            st.info("No image available for this analysis")
                
                # Only show delete functionality if not in offline mode
                if not st.session_state.force_offline_mode and internet_connected and supabase:
                    st.subheader("Delete Analysis")
                    delete_test_id = st.selectbox(
                        "Select Analysis ID to Delete",
                        [result.get('id', '') for result in filtered_results],
                        format_func=lambda x: f"ID: {x}",
                        key="delete_analysis_select"
                    )

                    if st.button("Delete Analysis Result"):
                        try:
                            # Delete from database
                            supabase.table('analysis_results').delete().eq('id', delete_test_id).execute()
                            st.success("Analysis result deleted successfully!")
                            st.rerun()  # Refresh the page to show updated data
                        except Exception as e:
                            st.error(f"Error deleting analysis result: {str(e)}")
                else:
                    st.info("No analysis results match the selected filters.")
        else:
            st.info("No analysis results found.")
        
        # Form to add a new analysis result manually
        st.subheader("Add Analysis Result Manually")
        with st.form("Add Analysis Result"):
            patient_name = st.text_input("Patient Name")
            test_type = st.text_input("Test Type")
            result = st.selectbox("Result", ["Normal", "Abnormal"])
            
            # Add confidence slider but note it may not be saved if column is missing
            confidence = st.slider("Confidence (may not be saved if column doesn't exist)", 0.0, 1.0, 0.5, 0.01)
            test_date = st.date_input("Test Date", datetime.today())
            submit_button = st.form_submit_button("Add Analysis Result")
            
            if submit_button:
                if st.session_state.force_offline_mode or not internet_connected or not supabase:
                    st.info("In offline mode, data is not saved to the database")
                    st.success("(Mock) Analysis result added successfully!")
                else:
                    try:
                        # Create basic record with required fields
                        new_analysis_result = {
                            "patient_name": patient_name,
                            "test_type": test_type,
                            "result": result,
                            "date": test_date.isoformat()
                        }

                        # Check if we can first get schema information
                        schema_check = supabase.table('analysis_results').select('*').limit(1).execute()

                        # Add confidence field if it exists in schema
                        if schema_check.data and 'confidence' in schema_check.data[0]:
                            new_analysis_result["confidence"] = f"{confidence:.2f}"

                        # Add reviewed field if it exists in schema
                        if schema_check.data and 'reviewed' in schema_check.data[0]:
                            new_analysis_result["reviewed"] = False

                        # Insert the record
                        response = supabase.table('analysis_results').insert(new_analysis_result).execute()

                        if response.data:
                            st.success("Analysis result added successfully!")

                            # Check if any columns were missing
                            missing = []
                            if 'confidence' not in new_analysis_result:
                                missing.append("confidence")
                            if 'reviewed' not in new_analysis_result:
                                missing.append("reviewed")

                            if missing:
                                st.warning(f"""
                                ⚠️ Your database schema is missing some columns: {', '.join(missing)}

                                The analysis was saved, but without these fields. To fix this issue,
                                add these columns using SQL (see guidance above).
                                """)

                            st.rerun()  # Refresh the page to show updated data
                        else:
                            st.error("Failed to add analysis result. Database returned no data.")

                    except Exception as e:
                        st.error(f"Error adding analysis result: {str(e)}")

                        # If there's a column error, guide the user
                        if "Could not find" in str(e) and "column" in str(e):
                            st.warning("""
                            ⚠️ Your database schema is missing columns that this application needs.

                            To fix this issue, you need to add these columns to your 'analysis_results' table in Supabase:
                            1. Go to your Supabase dashboard
                            2. Navigate to the SQL Editor
                            3. Run the following SQL query:

                            ```sql
                            ALTER TABLE analysis_results 
                            ADD COLUMN IF NOT EXISTS confidence TEXT,
                            ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE;
                            ```
                            """)

    elif menu == "Download Report":
        st.header("Analysis Reports")
        
        # Get analysis results for report generation
        if st.session_state.force_offline_mode or not internet_connected or not supabase:
            st.info("📱 Working in OFFLINE MODE with mock data")
            analysis_results = get_mock_analysis_results()
        else:
            try:
                # Get all analysis results, ordered by date (newest first)
                response = supabase.table('analysis_results').select('*').order('date', desc=True).execute()
                analysis_results = response.data
            except Exception as e:
                st.error(f"Error retrieving analysis results: {str(e)}")
                st.info("Falling back to offline mode with mock data")
                analysis_results = get_mock_analysis_results()

        # Create a selection box for the analysis to report on
        if analysis_results:
            # Format options for better display
            analysis_options = {}
            for result in analysis_results:
                # Format patient name and date
                patient_name = result.get('patient_name', 'Unknown Patient')
                date_str = result.get('date', '')
                test_type = result.get('test_type', 'Unknown Test')
                
                if date_str:
                    try:
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = date_str
                else:
                    formatted_date = "Unknown Date"
                
                # Create a descriptive label
                label = f"{patient_name} - {test_type} ({formatted_date})"
                analysis_options[label] = result
            
            # Create the selection dropdown
            selected_analysis_label = st.selectbox(
                "Select Analysis for Report",
                list(analysis_options.keys())
            )
            
            # Get the selected analysis data
            selected_analysis = analysis_options[selected_analysis_label]
            
            # Display a preview of the report content
            st.subheader("Report Preview")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### Patient Information")
                st.markdown(f"**Patient Name:** {selected_analysis.get('patient_name', 'Unknown')}")
                st.markdown(f"**Date of Analysis:** {selected_analysis.get('date', 'Unknown')}")
                st.markdown(f"**Test Type:** {selected_analysis.get('test_type', 'Unknown')}")
                st.markdown(f"**Result:** {selected_analysis.get('result', 'Unknown')}")
                st.markdown(f"**Confidence:** {selected_analysis.get('confidence', 'N/A')}")
                reviewed = "Yes" if selected_analysis.get('reviewed', False) else "No"
                st.markdown(f"**Reviewed by Doctor:** {reviewed}")
            
            with col2:
                st.markdown("### Analysis Image")
                if 'image_data' in selected_analysis and selected_analysis['image_data']:
                    image = get_image_from_base64(selected_analysis['image_data'])
                    if image:
                        st.image(image, caption="Patient Analysis Image", use_container_width=True)
                    else:
                        st.info("Image could not be loaded")
                else:
                    st.info("No image available")
            
            # Report generation options
            st.subheader("Report Options")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                include_letterhead = st.checkbox("Include Oculus Rift Healthcare AI Letterhead", value=True)
                include_doctor_signature = st.checkbox("Include Doctor Signature", value=True)
                include_recommendations = st.checkbox("Include Recommendations", value=True)
            
            with col2:
                doctor_name = st.text_input("Doctor Name", value=st.session_state.get('full_name', 'Consulting Doctor'))
                report_date = st.date_input("Report Date", datetime.today())
                report_format = st.radio("Report Format", ["PDF"], horizontal=True)
            
            # Generate additional recommendations based on test type and result
            recommendations = []
            if include_recommendations:
                test_type = selected_analysis.get('test_type', '').lower()
                result = selected_analysis.get('result', '').lower()
                
                if 'brain' in test_type:
                    if 'abnormal' in result:
                        recommendations = [
                            "Schedule a follow-up MRI scan within 2 weeks",
                            "Consult with a neurologist for further evaluation",
                            "Monitor for any changes in symptoms",
                            "Consider additional diagnostic tests as needed"
                        ]
                    else:
                        recommendations = [
                            "Routine follow-up in 6 months",
                            "Maintain healthy lifestyle habits",
                            "Report any new neurological symptoms immediately"
                        ]
                elif 'retinopathy' in test_type or 'eye' in test_type:
                    if 'abnormal' in result:
                        recommendations = [
                            "Refer to ophthalmologist for comprehensive evaluation",
                            "Consider laser photocoagulation therapy if appropriate",
                            "Monitor blood sugar levels closely",
                            "Follow-up examination in 3 months"
                        ]
                    else:
                        recommendations = [
                            "Continue regular diabetic management",
                            "Annual eye examination recommended",
                            "Monitor blood sugar control"
                        ]
                elif 'skin' in test_type:
                    if 'abnormal' in result:
                        recommendations = [
                            "Refer to dermatologist for evaluation and possible biopsy",
                            "Avoid sun exposure to affected area",
                            "Follow-up within 2 weeks",
                            "Consider additional imaging if needed"
                        ]
                    else:
                        recommendations = [
                            "Continue regular skin self-examinations",
                            "Use sun protection when outdoors",
                            "Follow up at next annual checkup"
                        ]
                else:
                    # Default recommendations
                    if 'abnormal' in result:
                        recommendations = [
                            "Follow-up consultation within 2 weeks recommended",
                            "Additional diagnostic tests may be necessary",
                            "Monitor symptoms closely"
                        ]
                    else:
                        recommendations = [
                            "No immediate follow-up necessary",
                            "Continue routine healthcare",
                            "Next scheduled check-up as planned"
                        ]
            
            # Generate report button
            if st.button("Generate Report"):
                with st.spinner("Generating medical report..."):
                    # Create PDF report using ReportLab
                    pdf_buffer = create_medical_report(
                        selected_analysis,
                        doctor_name=doctor_name,
                        report_date=report_date,
                        include_letterhead=include_letterhead,
                        include_signature=include_doctor_signature,
                        recommendations=recommendations
                    )
                    
                    # Format filename based on patient and date
                    patient_name = selected_analysis.get('patient_name', 'patient').replace(" ", "_")
                    date_str = datetime.now().strftime("%Y%m%d")
                    filename = f"OculusRiftHealthcare_MedicalReport_{patient_name}_{date_str}.pdf"
                    
                    st.success("Medical report generated successfully!")
                    
                    # Provide download button for the PDF
                st.download_button(
                        label="Download Medical Report (PDF)",
                        data=pdf_buffer,
                        file_name=filename,
                        mime="application/pdf"
                    )
        else:
            st.info("No analysis results available for report generation. Please perform analysis or add results first.")

    elif menu == "Settings":
        st.header("Settings")
        st.write("Settings functionality can be implemented here.")
        # Placeholder for settings options
        st.text_input("Change Password")
        st.text_input("Update Profile")
        if st.button("Save Changes"):
            st.success("Changes saved successfully!")

def create_medical_report(analysis_data, doctor_name, report_date, include_letterhead=True, include_signature=True, recommendations=None):
    """
    Create a professional medical report as PDF with analysis results and images
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    import io
    
    # Create a buffer for the PDF
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create a list to hold the document elements
    elements = []
    
    # Add custom styles
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
    
    # Add letterhead if requested
    if include_letterhead:
        # Create a title with the logo and hospital name
        elements.append(Paragraph("Oculus Rift Healthcare AI Medical Center", title_style))
        elements.append(Paragraph("Advanced AI-Powered Healthcare", ParagraphStyle(
            'Subtitle',
            parent=styles['Heading2'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            spaceAfter=6
        )))
        
        # Add address and contact info
        contact_info = """
        <para alignment="center">
        123 AI Healthcare Road, Medical District<br/>
        Tel: +91-1234567890 | Email: care@oculusrifthealthcare.com<br/>
        www.oculusrifthealthcare.com
        </para>
        """
        elements.append(Paragraph(contact_info, ParagraphStyle(
            'ContactInfo',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        )))
    
    # Add a line to separate letterhead from content
    elements.append(Spacer(1, 20))
    
    # Add report title
    elements.append(Paragraph("MEDICAL ANALYSIS REPORT", title_style))
    elements.append(Spacer(1, 10))
    
    # Format the report date
    formatted_report_date = report_date.strftime("%B %d, %Y")
    elements.append(Paragraph(f"Report Date: {formatted_report_date}", normal_style))
    
    # Add patient information section
    elements.append(Paragraph("Patient Information", section_title_style))
    
    # Format patient information as a table
    patient_name = analysis_data.get('patient_name', 'Unknown')
    
    # Format the analysis date
    analysis_date = analysis_data.get('date', '')
    if analysis_date:
        try:
            date_obj = datetime.fromisoformat(analysis_date.replace('Z', '+00:00'))
            formatted_analysis_date = date_obj.strftime("%B %d, %Y at %H:%M")
        except:
            formatted_analysis_date = analysis_date
    else:
        formatted_analysis_date = "Unknown"
    
    # Create patient info table data
    patient_data = [
        ["Patient Name:", patient_name],
        ["Analysis Date:", formatted_analysis_date],
        ["Test Type:", analysis_data.get('test_type', 'Unknown')],
    ]
    
    # Create the table
    patient_table = Table(patient_data, colWidths=[1.5*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightskyblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(patient_table)
    elements.append(Spacer(1, 15))
    
    # Add analysis results section
    elements.append(Paragraph("Analysis Results", section_title_style))
    
    # Format the results
    result = analysis_data.get('result', 'Unknown')
    confidence = analysis_data.get('confidence', 'N/A')
    reviewed = "Yes" if analysis_data.get('reviewed', False) else "No"
    
    # Create results table data
    results_data = [
        ["Result:", result],
        ["Confidence Score:", confidence],
        ["Reviewed by Doctor:", reviewed],
    ]
    
    # Create the table with colored background based on result
    results_table = Table(results_data, colWidths=[1.5*inch, 4*inch])
    
    # Set background color based on result
    if result.lower() == 'abnormal':
        result_color = colors.lightcoral
    else:
        result_color = colors.lightgreen
        
    results_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightskyblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('BACKGROUND', (1, 0), (1, 0), result_color),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(results_table)
    elements.append(Spacer(1, 15))
    
    # Add the analysis image if available
    if 'image_data' in analysis_data and analysis_data['image_data']:
        elements.append(Paragraph("Analysis Image", section_title_style))
        try:
            # Convert base64 to image
            image_data = base64.b64decode(analysis_data['image_data'])
            img_io = io.BytesIO(image_data)
            
            # Add the image with appropriate width
            img = Image(img_io, width=5*inch, height=3.5*inch)
            elements.append(img)
            elements.append(Spacer(1, 10))
        except Exception as e:
            elements.append(Paragraph(f"Image could not be included: {str(e)}", normal_style))
    
    # Add recommendations if provided
    if recommendations:
        elements.append(Paragraph("Medical Recommendations", section_title_style))
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec}", normal_style))
        elements.append(Spacer(1, 15))
    
    # Add doctor's signature if requested
    if include_signature:
        elements.append(Spacer(1, 30))
        
        # Create signature line and doctor information
        signature_data = [
            ["_______________________", ""],
            [f"Dr. {doctor_name}", "Date: " + formatted_report_date],
            ["Oculus Rift Healthcare AI Medical Center", ""]
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 2.5*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
            ('FONT', (0, 1), (0, 1), 'Helvetica-Bold'),
        ]))
        
        elements.append(signature_table)
    
    # Add disclaimer
    elements.append(Spacer(1, 30))
    disclaimer_text = """
    <para><i>Disclaimer: This report contains AI-assisted analysis and should be interpreted by qualified healthcare professionals only. 
    The results are not a definitive diagnosis and should be considered in the context of the patient's clinical presentation and other diagnostic information.
    Oculus Rift Healthcare AI employs state-of-the-art technology, but results should be validated by appropriate medical specialists.</i></para>
    """
    elements.append(Paragraph(disclaimer_text, ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey
    )))
    
    # Build the PDF
    doc.build(elements)
    
    # Move to the beginning of the buffer
    buffer.seek(0)
    
    return buffer

if __name__ == "__main__":
    main() 