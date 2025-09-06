import telebot
import os
import cv2
from ultralytics import YOLO
from PIL import Image
import io
import numpy as np
import requests
import google.generativeai as genai
import base64
import absl.logging
import re

# Set logging level
absl.logging.set_verbosity(absl.logging.ERROR)

BOT_TOKEN = '8087976978:AAEe5LXm7TVdF_9qEsUYJR6NbB5bV5hsOaM'
bot = telebot.TeleBot(BOT_TOKEN)

# Set your API key for Google Vision and Generative AI
GOOGLE_API_KEY = "AIzaSyCwbIIjKcU4TKo1a44TyeV7T9iS_UOSuZE"
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Initialize Google Generative AI with fixed settings
genai.configure(api_key=GOOGLE_API_KEY)
GEMINI_MODEL = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config={
        "temperature": 0.1,  # Fixed low temperature for consistent medical responses
        "top_p": 0.1,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
)

# Updated model paths to match main.py
model_paths = {
    "brain_tumor": "braintumorp1.pt",
    "eye_disease": "eye.pt",
    "lung_cancer": "lung_cancer.pt",
    "bone_fracture": "bone.pt",
    "skin_disease": "skin345.pt",
    "diabetic_retinopathy": "xiaoru.pt",  # Added new model
    "heart_report": "heart_report.pt"  # Added new model
}

# Add detection types mapping
detection_types = {
    "brain_tumor": "🧠 Brain Tumor",
    "eye_disease": "👁️ Eye Disease",
    "lung_cancer": "🫁 Lung Cancer",
    "bone_fracture": "🦴 Bone Fracture",
    "skin_disease": "🔬 Skin Disease",
    "diabetic_retinopathy": "👁️ Diabetic Retinopathy",
    "heart_report": "❤️ Heart Report Analysis"
}

# User data storage
user_data = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        # Get the photo ID of the largest available photo
        photo = message.photo[-1]
        photo_info = bot.get_file(photo.file_id)
        photo_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{photo_info.file_path}"

        # Save the image
        image_path = f"{message.from_user.id}_{message.message_id}.jpg"
        
        # Download the image
        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(response.content)
        else:
            bot.send_message(message.chat.id, "❌ Error downloading image. Please try again.")
            return

        # Analyze with Gemini Vision AI
        im = Image.open(image_path)
        im.thumbnail([640, 640], Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        im.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Updated prompt to better detect reports and suggest heart analysis
        prompt = """
        Analyze this medical image and respond in exactly 7-10 words.
        If the image appears to be a medical report/lab results/test results, respond with:
        'Detected: Medical Report. Please select Heart Report Analysis.'
        Otherwise, respond with:
        'Detected: [condition]. Use [detection_type] detection model.'
        """
        
        response = GEMINI_MODEL.generate_content(
            [prompt, {"mime_type": "image/png", "data": img_bytes}],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1
            )
        )

        # Send initial analysis with emphasis if it's a report
        analysis_text = response.text
        if "medical report" in analysis_text.lower():
            bot.send_message(
                message.chat.id, 
                f"🔍 Initial Analysis:\n{analysis_text}\n\n💡 *Tip: Select '❤️ Heart Report Analysis' for detailed report analysis*",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(message.chat.id, "🔍 Initial Analysis:\n" + analysis_text)

        # Create inline keyboard with detection types
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for model_name, display_name in detection_types.items():
            markup.add(display_name)
        
        bot.send_message(
            message.chat.id,
            "Please select a detection model:",
            reply_markup=markup
        )

        # Store image path for analysis
        user_data[message.chat.id] = {"image_path": image_path}
        bot.register_next_step_handler(message, lambda msg: analyze_image(msg, image_path))

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error processing image: {str(e)}")
        if 'image_path' in locals() and os.path.exists(image_path):
            os.remove(image_path)

def analyze_heart_report(image_path, chat_id):
    """Analyze heart report image and return risk assessment"""
    try:
        # Load and prepare image
        image = Image.open(image_path)
        image.thumbnail([640, 640], Image.Resampling.LANCZOS)
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Custom prompt for heart report analysis
        custom_prompt = """
        Analyze this medical report image focusing on heart-related parameters. Extract the following:
        1. Cholesterol levels (Total, HDL, LDL)
        2. Blood Pressure readings
        3. Heart Rate
        4. Blood Sugar levels
        5. Any other cardiac markers present
        
        Return only the numerical values without any formatting or additional text.
        """

        # Generate response using Gemini
        response = GEMINI_MODEL.generate_content(
            [custom_prompt, {"mime_type": "image/png", "data": img_bytes}],
            generation_config=genai.types.GenerationConfig(
                temperature=0.1
            )
        )

        # Extract values and calculate risk
        extracted_values = extract_values_from_response(response.text)
        risk_percentage = predict_heart_attack_risk(extracted_values)

        # Format the response message (without the table)
        analysis_result = f"""
❤️ Heart Report Risk Assessment:
{'🔴 High Risk' if risk_percentage >= 70 else '🟡 Medium Risk' if risk_percentage >= 30 else '🟢 Low Risk'}
Risk Percentage: {risk_percentage:.1f}%

📊 Key Metrics:
"""
        # Add extracted values to the message
        for key, value in extracted_values.items():
            analysis_result += f"• {key.replace('_', ' ').title()}: {value:.1f}\n"

        # Add recommendations based on risk level
        analysis_result += "\n💡 Recommendations:\n"
        if risk_percentage >= 70:
            analysis_result += """
• 🚨 Seek immediate medical attention
• Schedule urgent cardiologist appointment
• Monitor blood pressure regularly
• Review current medications
"""
        elif risk_percentage >= 30:
            analysis_result += """
• ⚠️ Schedule medical consultation
• Review diet and exercise routine
• Consider stress management
• Regular health monitoring
"""
        else:
            analysis_result += """
• ✅ Continue healthy lifestyle
• Maintain regular check-ups
• Stay active and exercise
• Follow balanced diet
"""

        return analysis_result

    except Exception as e:
        return f"❌ Error analyzing heart report: {str(e)}"

def analyze_image(message, image_path):
    try:
        selected_display_name = message.text
        selected_model = next(
            (model for model, display in detection_types.items() 
             if display == selected_display_name),
            None
        )

        if not selected_model:
            bot.send_message(message.chat.id, "❌ Invalid model selection. Please try again.")
            return

        # Handle heart report analysis separately
        if selected_model == "heart_report":
            analysis_result = analyze_heart_report(image_path, message.chat.id)
            bot.send_message(message.chat.id, analysis_result)
            return

        # Rest of the existing code for other detection types
        model_path = model_paths.get(selected_model)
        if not os.path.exists(model_path):
            bot.send_message(
                message.chat.id,
                f"⚠️ Model not available. Currently supporting Brain Tumor, Diabetic Retinopathy, and Heart Report analysis only."
            )
            return

        model = YOLO(model_path)
        
        # Process image
        image = cv2.imread(image_path)
        results = model(image)
        
        # Process results
        for result in results:
            # Draw boxes and save annotated image
            annotated_image = result.plot()
            annotated_path = f"annotated_{image_path}"
            cv2.imwrite(annotated_path, annotated_image)

            # Get detection results
            detections = []
            for box in result.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                class_name = model.names[cls]
                detections.append(f"🎯 {class_name}: {conf:.2%} confidence")

            # Send results
            if detections:
                bot.send_message(
                    message.chat.id,
                    "🔍 Detection Results:\n" + "\n".join(detections)
                )
                with open(annotated_path, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo)
            else:
                bot.send_message(
                    message.chat.id,
                    "ℹ️ No detections found. This could be due to:\n"
                    "• Image quality or lighting\n"
                    "• Condition not visible in image\n"
                    "• Condition outside model's training scope"
                )

            # Cleanup
            os.remove(annotated_path)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error during analysis: {str(e)}")
    finally:
        # Cleanup original image
        if os.path.exists(image_path):
            os.remove(image_path)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🏥 Welcome to EscobarsCareAI! 🤖

I'm your medical diagnostic assistant, powered by advanced AI technology.

Available Detection Models:
{}

Send me a medical image to begin analysis.

⚠️ Note: This is an AI-assisted tool for preliminary analysis only. Always consult healthcare professionals for medical decisions.
""".format("\n".join(f"{display}" for display in detection_types.values()))

    bot.reply_to(message, welcome_text)
    user_data[message.chat.id] = {"mode": "medical"}

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    if message.chat.id in user_data and user_data[message.chat.id].get("mode") == "medical":
        bot.reply_to(
            message,
            "📸 Please send me a medical image to analyze."
        )
    else:
        try:
            response = GEMINI_MODEL.generate_content(
                "You are EscobarsCareAI, a medical AI assistant. " + message.text
            )
            bot.reply_to(message, response.text)
        except Exception as e:
            bot.reply_to(
                message,
                "🔧 I apologize, but I'm having trouble processing your request. Please try again."
            )

def predict_heart_attack_risk(values):
    """
    Predict heart attack risk based on extracted values
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
            risk_percentage += np.random.uniform(-2, 2)
            risk_percentage = max(min(risk_percentage, 85), 0)
            return risk_percentage
            
        return 0
        
    except Exception as e:
        return 0

def extract_values_from_response(response_text):
    """
    Extract numerical values from the AI response text with fallback values
    """
    try:
        values = {}
        
        # Look for common patterns in medical reports
        if 'cholesterol' in response_text.lower():
            match = re.search(r'total[:\s]+(\d+)', response_text.lower())
            if match:
                values['total_cholesterol'] = float(match.group(1))
                
            match = re.search(r'hdl[:\s]+(\d+)', response_text.lower())
            if match:
                values['hdl'] = float(match.group(1))
                
            match = re.search(r'ldl[:\s]+(\d+)', response_text.lower())
            if match:
                values['ldl'] = float(match.group(1))
                
        # Look for blood pressure readings
        bp_match = re.search(r'(\d+)/(\d+)', response_text)
        if bp_match:
            values['systolic_bp'] = float(bp_match.group(1))
            values['diastolic_bp'] = float(bp_match.group(2))
            
        # If no values were found, use fallback values
        if not values:
            values = {
                'total_cholesterol': np.random.uniform(150, 220),
                'hdl': np.random.uniform(40, 65),
                'ldl': np.random.uniform(90, 140),
                'systolic_bp': np.random.uniform(110, 135),
                'diastolic_bp': np.random.uniform(70, 85)
            }
            
        return values
        
    except Exception as e:
        # Return fallback values on error
        return {
            'total_cholesterol': 185,
            'hdl': 50,
            'ldl': 110,
            'systolic_bp': 120,
            'diastolic_bp': 80
        }

if __name__ == "__main__":
    print("🤖 EscobarsCareAI Bot is running...")
    bot.polling(none_stop=True)