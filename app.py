import os, json
from flask import Flask, render_template, request, jsonify, send_from_directory, session
import google.generativeai as genai
from gtts import gTTS

# --- Use fake Gemini response if DEBUG_MODE is True ---
DEBUG_MODE = False  # Set to False to use the actual Gemini API

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '978c48350df18bcae20ebae4be05950129ef8c32897ca0dd')


if not DEBUG_MODE:
    # Get API key from environment variable
    API_KEY = os.environ.get('GEMINI_API_KEY')

    if not API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    genai.configure(api_key=API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_form', methods=['POST'])
def process_form():

    if 'session_id' not in session:
        session['session_id'] = os.urandom(24)  # Generate a unique session ID

    exercise_type = request.form['exercise_type']
    motivation_style = request.form['motivation_style']
    heroes = request.form['heroes']
    voice_preference = request.form['voice']

    # Construct the LLM prompt
    prompt = f"""
        You are a motivational coach for a workout app designed to entertain and motivate users with varying fitness levels and general tech and web savvy. 
        Your task is to generate short, engaging messages that are delivered at random intervals during a {exercise_type} workout.

        The user prefers a {motivation_style} motivation style. 

        Here are some of the user's heroes: {heroes}. 

        The user wants this level of spiciness in the hot takes: {motivation_style}. Moderate your messsages to this. 

        You will use a contemprorary gen z style. No hashtags.

        Return the 8 motivational messages in the following JSON format:

        {{
          "messages": [
            {{
              "text": "Motivational message 1",
              "category": "Category of message 1",
              "spiciness": "Spiciness level of message 1" 
            }},
            {{
              "text": "Motivational message 2",
              "category": "Category of message 2",
              "spiciness": "Spiciness level of message 2" 
            }},
            // ... more messages
          ]
        }}

        For each message, include the "text", "category" (e.g., "General encouragement", "Distance/Progress focused", "Humorous", etc.), and "spiciness" (e.g., "mild", "medium", "hot", "extra spicy").

        Ensure that the JSON response contains only the "messages" array with the motivational messages and their details. Do not include any additional text or explanations.
    """
   

    if DEBUG_MODE:
        motivational_text = """
        {
          "messages": [
            {
              "text": "You're doing great! Keep pushing!",
              "category": "General encouragement",
              "spiciness": "mild"
            },
            {
              "text": "Almost there! You've got this!",
              "category": "Distance/Progress focused",
              "spiciness": "mild"
            },
            {
              "text": "Way to go! You're a rockstar!",
              "category": "General encouragement",
              "spiciness": "medium"
            }

          ]
        }
        """
        print("DEBUG MODE RESPONSE")
    else:    
        # Use the Gemini API
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)

        # Get the generated text directly from the response
        motivational_text = response.text
        #print(f"Raw response from Gemini:\n{motivational_text}\n")  # Debug: Print the raw response

        #to fix the markdown repsonse
        # Remove markdown backticks
        motivational_text = motivational_text.replace("`", "").replace("json","")
    
    #print(f"Input response:\n{motivational_text}\n")  # Debug: Print the raw response
    # Initialize the session if it doesn't exist
   
    try:
        motivational_json = json.loads(motivational_text)
        messages_data = motivational_json.get("messages", [])  # Extract the messages array
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Problematic JSON string: {motivational_text}")
        messages_data = []

    filtered_messages = [message_data["text"] for message_data in messages_data if message_data.get("text")]
    audio_urls = []

    if DEBUG_MODE: 
      print(f"Raw response from Gemini:\n{motivational_text}\n")
      for message_data in messages_data:
          if message_data:
              print(f"Extracted message: {message_data.get("text")}")  # Debug: Print the extracted message
              print(f"Category: {message_data.get("category")}")  # Debug: Print the category
              print(f"Spiciness: {message_data.get("spiciness")}")  # Debug: Print the spiciness level
              
  
    for message in filtered_messages:
      # Generate audio for the message
      tts = gTTS(text=message, lang='en', tld='com')
      audio_file_path = f"tmp/{session['session_id'].hex()}_{hash(message)}.mp3"  

      os.makedirs('tmp', exist_ok=True)
      tts.save(audio_file_path)
      audio_urls.append(f"/tmp/{hash(message)}.mp3") 

    print(f"Filtered messages:\n{filtered_messages}\n")  # Debug: Print the filtered messages
    print(f"Audio URLs:\n{audio_urls}\n")  # Debug: Print the audio URLs
    print(f"Repsonse", jsonify({'message': filtered_messages, 'audiourl': audio_urls}))
    # Return the motivational messages and audio URLs
    return jsonify({'message': filtered_messages, 'audiourl': audio_urls})


@app.route('/tmp/<filename>')
def serve_tmp_file(filename):
    # Check if the user has a valid session
    if 'session_id' in session:
        # Construct the expected filename using the session ID
        expected_filename = f"{session['session_id'].hex()}_{filename}"
        file_path = os.path.join('tmp', expected_filename)

        if os.path.exists(file_path):
            return send_from_directory('tmp', expected_filename)

    return "Access denied", 403  # Return 403 Forbidden if no valid session or file not found


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')