from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# Load the JSON data from a file
def load_json():
    with open('more_info.json', 'r') as file:
        return json.load(file)

# Define the home route
@app.route('/')
def home():
    data = load_json()
    return render_template('index.html', data=data)

# API endpoint to filter data
@app.route('/filter', methods=['GET'])
def filter_data():
    category = request.args.get('category', '').lower()
    topic_name = request.args.get('topicname', '').lower()
    
    data = load_json()
    filtered_data = [item for item in data if 
                     (not category or category in item.get('category_name', '').lower()) and
                     (not topic_name or topic_name in item.get('topic_name', '').lower())]
    return jsonify(filtered_data)

if __name__ == '__main__':
    app.run(debug=True)
