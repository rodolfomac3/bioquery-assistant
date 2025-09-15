from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "BioQuery Assistant API is running",
        "version": "1.0.0"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    return jsonify({
        "response": f"Echo: {user_message} (OpenAI integration coming soon!)",
        "query_type": "test",
        "literature_included": False
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)