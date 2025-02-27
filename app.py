from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import requests
import os
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("GEMINI_API_KEY")  # Store API key in .env file
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Token Limit Configuration
TOKEN_LIMIT = 200  # Prevents excessive token usage

print(f"Loaded API Key: {'HIDDEN' if API_KEY else 'NOT FOUND'}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()
    image_data = data.get('image', None)

    # Base Payload
    payload = {
        "contents": [{
            "parts": [{"text": message}]
        }],
        "generationConfig": {
            "maxOutputTokens": TOKEN_LIMIT  # Enforce token limit
        }
    }

    # If an image is provided, add system prompt and process image
    if image_data and image_data.startswith('data:image'):
        try:
            image_content = image_data.split(',')[1]  # Extract base64 content
            mime_type = image_data.split(';')[0].split(':')[1]  # Extract MIME type
        except IndexError:
            return jsonify({'error': 'Invalid image format'}), 400
        
        system_prompt = 'You are a Medical expert. Analyze the image and provide a concise, accurate response with relevant links.'

        payload = {
            "contents": [{
                "parts": [
                    {"text": system_prompt},
                    {"text": message},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_content
                        }
                    }
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": TOKEN_LIMIT
            }
        }

    # Stream the response
    def generate():
        url = f"{API_URL}?key={API_KEY}"

        if request.args.get('stream', 'true').lower() == 'true':
            url += "&alt=sse"

        headers = {'Content-Type': 'application/json'}

        try:
            print(f"Sending request to: {url}")
            print(f"Payload: {json.dumps(payload, default=str)[:200]}...")  # Log only a snippet for debugging

            response = requests.post(url, json=payload, headers=headers, stream=True)

            if response.status_code != 200:
                error_detail = response.text
                print(f"API Error {response.status_code}: {error_detail}")
                yield f"data: {json.dumps({'error': f'API Error {response.status_code}. Details: {error_detail}'})}\n\n"
                return

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        yield f"{decoded_line}\n\n"
                    else:
                        yield f"data: {json.dumps({'text': decoded_line})}\n\n"

        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {str(e)}")
            yield f"data: {json.dumps({'error': 'Request failed. Please try again.'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)
