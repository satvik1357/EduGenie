from flask import Flask, render_template, request, send_file
from utils.text_extractor import extract_text
from utils.prompts import get_prompt
import os
import uuid
from dotenv import load_dotenv # Keep this for loading GEMINI_API_KEY

# Import the Google Generative AI library
import google.generativeai as genai

# Load our secret API key from the .env file
load_dotenv()
# Configure the Google Gemini API with our key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create our Flask web application
app = Flask(__name__)

# Define a folder where we'll save the generated results
UPLOAD_FOLDER = 'generated_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the generative AI model (using gemini-1.5-flash as it's generally good for text tasks)
model = genai.GenerativeModel('gemini-1.5-flash')

# This function talks to the Google Gemini AI
def call_ai_api(prompt):
    try:
        # Send our instruction (prompt) to the AI and get its response
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        else:
            print(f"Gemini API returned an empty response for prompt: {prompt}")
            return "Sorry, the AI did not return any content for that request."
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "Oops! EduGenie ran into a problem generating content. Please try again with different input or feature."

# --- Web Pages (Routes) ---

# This is the homepage of our EduGenie app
@app.route('/')
def index():
    # No login system, so no user_id or clerk_publishable_key to pass
    return render_template('index.html')

# This runs when you click the "Generate" button
@app.route('/generate', methods=['POST'])
def generate():
    file = request.files.get('file')
    feature = request.form.get('feature')
    # NEW: Get the dynamic number of items
    num_items = request.form.get('num_items')

    if not file or file.filename == '':
        return render_template('result.html', content="Error: No file selected.", filename="")
    if not feature:
        return render_template('result.html', content="Error: No feature selected.", filename="")

    text = extract_text(file)

    if "Unsupported file format." in text:
        return render_template('result.html', content=text, filename="")

    # Pass the dynamic number of items to get_prompt
    prompt = get_prompt(text, feature, num_items=num_items)

    result = call_ai_api(prompt)

    filename = f"{uuid.uuid4()}.txt"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result)
    except Exception as e:
        print(f"Error saving generated file: {e}")
        return render_template('result.html', content=result, filename="")

    return render_template('result.html', content=result, filename=filename)

# This runs when you click the "Download" button
@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

# --- Run the App ---
if __name__ == "__main__":
    app.run(debug=True)