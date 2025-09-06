# Import necessary libraries
import cv2
import streamlit as st
import numpy as np
import tempfile
import time
from datetime import datetime

# Get reference to the main module save_analysis_to_database function
from main import save_analysis_to_database

def analyze_brain_mri(image):
    """
    Analyze a brain MRI image for tumors
    
    Args:
        image: The MRI image to analyze
        
    Returns:
        tuple: (result_text, confidence)
    """
    # Simulate analysis with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(101):
        status_text.text(f"Analyzing brain MRI... {i}%")
        progress_bar.progress(i)
        time.sleep(0.01)
    
    # For demo, randomly determine if a tumor is detected
    if np.random.random() > 0.5:
        confidence = round(np.random.uniform(0.7, 0.98), 2)
        return "Tumor detected", confidence
    else:
        confidence = round(np.random.uniform(0.8, 0.95), 2)
        return "Normal", confidence

def analyze_chest_xray(image):
    """
    Analyze a chest X-ray for pneumonia
    
    Args:
        image: The X-ray image to analyze
        
    Returns:
        tuple: (result_text, confidence)
    """
    # Simulate analysis with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(101):
        status_text.text(f"Analyzing chest X-ray... {i}%")
        progress_bar.progress(i)
        time.sleep(0.01)
    
    # For demo, randomly determine if pneumonia is detected
    if np.random.random() > 0.6:
        confidence = round(np.random.uniform(0.65, 0.92), 2)
        return "Pneumonia detected", confidence
    else:
        confidence = round(np.random.uniform(0.75, 0.96), 2)
        return "Normal", confidence

def analyze_retina_scan(image):
    """
    Analyze a retinal scan for diabetic retinopathy
    
    Args:
        image: The retinal scan to analyze
        
    Returns:
        tuple: (result_text, confidence)
    """
    # Simulate analysis with progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(101):
        status_text.text(f"Analyzing retina scan... {i}%")
        progress_bar.progress(i)
        time.sleep(0.01)
    
    # For demo, randomly determine if diabetic retinopathy is detected
    if np.random.random() > 0.7:
        confidence = round(np.random.uniform(0.6, 0.9), 2)
        return "Diabetic retinopathy detected", confidence
    else:
        confidence = round(np.random.uniform(0.8, 0.97), 2)
        return "Normal", confidence

def analyze_image(uploaded_file, patient_name, test_type):
    """Process the uploaded image for the selected test type"""
    
    if uploaded_file is None:
        st.warning("Please upload an image to analyze")
        return
    
    # Create a temporary file to store the uploaded image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_file.write(uploaded_file.getvalue())
        temp_file_path = temp_file.name
    
    # Read the image with OpenCV
    img = cv2.imread(temp_file_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Display the uploaded image
    st.image(img_rgb, caption=f"Uploaded {test_type} Image", use_column_width=True)
    
    # Analyze the image based on test type
    if test_type == "Brain MRI":
        result_text, confidence = analyze_brain_mri(img_rgb)
    elif test_type == "Chest X-ray":
        result_text, confidence = analyze_chest_xray(img_rgb)
    elif test_type == "Retina Scan":
        result_text, confidence = analyze_retina_scan(img_rgb)
    else:
        st.error("Unsupported test type")
        return
    
    # Display results
    st.subheader("Analysis Results")
    
    result_color = "green" if result_text == "Normal" else "red"
    st.markdown(f"<h3 style='color: {result_color};'>{result_text}</h3>", unsafe_allow_html=True)
    
    st.write(f"Confidence: {confidence * 100:.1f}%")
    st.write(f"Patient: {patient_name}")
    st.write(f"Test Type: {test_type}")
    st.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save results to database
    save_analysis_to_database({
        "patient_name": patient_name,
        "test_type": test_type,
        "result": result_text,
        "confidence": confidence
    })
    
    # Clean up the temporary file
    import os
    os.unlink(temp_file_path) 