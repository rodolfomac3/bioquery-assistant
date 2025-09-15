"""
BioQuery Assistant - Flask Backend
AI-powered research assistant for molecular biology queries.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import json
import re

# Import our custom modules
from prompts.bio_prompts import get_prompt, classify_query_type
from services.ncbi_service import NCBIService

# Load environment variables
load_dotenv('.env')

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize NCBI service
ncbi_service = NCBIService()

def format_response(response_text):
    """Format AI responses to look more professional and structured."""
    
    # Add proper spacing around numbered lists
    response_text = re.sub(r'(\d+\.)\s*\*\*([^*]+)\*\*:', r'\n\1 **\2**:\n', response_text)
    
    # Format mathematical formulas
    response_text = re.sub(r'\\?\[([^]]+)\\?\]', r'<div class="formula">\1</div>', response_text)
    
    # Format step numbers
    response_text = re.sub(r'^(\d+)\.\s+\*\*([^*]+)\*\*:', r'<span class="step-number">\1</span>**\2**:', response_text, flags=re.MULTILINE)
    
    # Format notes and warnings
    response_text = re.sub(r'\*Note:([^*]+)\*', r'<div class="note">📝 **Note:** \1</div>', response_text)
    response_text = re.sub(r'\*Warning:([^*]+)\*', r'<div class="warning">⚠️ **Warning:** \1</div>', response_text)
    response_text = re.sub(r'\*Tip:([^*]+)\*', r'<div class="tip">💡 **Tip:** \1</div>', response_text)
    
    # Add better spacing
    response_text = re.sub(r'\n\n+', '\n\n', response_text)
    
    return response_text.strip()

def call_openai_api(messages, max_tokens=1000, temperature=0.7):
    user_message = messages[-1]['content'] if messages else "No message"
    print(f"DEBUG: Processing query: '{user_message[:50]}...'")
    """
    Call OpenAI API using requests with fallback to mock responses.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    use_mock = False  # FORCE DISABLE MOCK MODE
    
    print(f"DEBUG: use_mock={use_mock}, has_api_key={bool(api_key)}")
    
    # If using mock mode or no API key, return mock response
    if use_mock or not api_key:
        return get_mock_response(messages)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-4o-mini',  # Fast and cost-effective
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature
    }
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Response Text: {response.text[:200]}")
        
        if response.status_code != 200:
            print(f"REAL API ERROR: {response.status_code} - {response.text}")
            return get_mock_response(messages)
        
        return response.json()
        
    except Exception as e:
        print(f"REQUEST EXCEPTION: {e}")
        return get_mock_response(messages)

def get_mock_response(messages):
    """Generate a simple mock response (only used for API failures)."""
    user_message = messages[-1]['content'] if messages else "No message"
    
    mock_content = f"""I'm currently experiencing technical difficulties connecting to the AI service. 

Your question: "{user_message}"

This is a temporary fallback response. Please try again in a moment, or check that the backend service is running properly.

*Note: This is a temporary mock response due to API connectivity issues.*"""
    
    return {
        'choices': [{
            'message': {'content': mock_content}
        }],
        'usage': {
            'prompt_tokens': len(' '.join([m['content'] for m in messages])) // 4,
            'completion_tokens': len(mock_content) // 4,
            'total_tokens': (len(' '.join([m['content'] for m in messages])) + len(mock_content)) // 4
        }
    }

@app.route('/')
def health_check():
    """Basic health check endpoint."""
    return jsonify({
        "status": "healthy",
        "message": "BioQuery Assistant API is running",
        "version": "1.0.0"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for biological queries."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        include_literature = data.get('include_literature', False)
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        # Classify the query to use appropriate prompt
        query_type = classify_query_type(user_message)
        system_prompt = get_prompt(query_type)
        
        # For non-biology questions, use a general assistant prompt
        if query_type == "general_bio" and not any(keyword in user_message.lower() for keyword in [
            'biology', 'dna', 'rna', 'protein', 'gene', 'pcr', 'crispr', 'cell', 'molecular', 
            'biochemistry', 'genetics', 'experiment', 'lab', 'assay', 'culture', 'western',
            'blot', 'electrophoresis', 'cloning', 'transfection', 'molarity', 'concentration',
            'primer', 'sequencing', 'plasmid', 'vector', 'enzyme', 'antibody', 'microscopy'
        ]):
            system_prompt = """You are a helpful AI assistant. Answer questions accurately and helpfully across all topics. Be concise but thorough in your responses. When dealing with scientific or technical questions, provide clear explanations with proper formatting."""
        
        # Optionally include recent literature
        literature_context = ""
        if include_literature:
            try:
                # Extract key terms for literature search
                search_terms = extract_search_terms(user_message)
                if search_terms:
                    papers = ncbi_service.get_recent_papers(search_terms, max_results=3)
                    literature_context = ncbi_service.format_articles_for_llm(papers)
            except Exception as e:
                print(f"Literature search failed: {e}")
                literature_context = "Literature search unavailable at the moment."
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add literature context if available
        if literature_context:
            enhanced_message = f"{user_message}\n\nRelevant recent literature:\n{literature_context}"
            messages.append({"role": "user", "content": enhanced_message})
        else:
            messages.append({"role": "user", "content": user_message})
        
        # Get response from OpenAI using our custom function
        response_data = call_openai_api(messages)
        
        # Format the response for better presentation
        raw_message = response_data['choices'][0]['message']['content']
        assistant_message = format_response(raw_message)
        usage = response_data.get('usage', {})
        
        return jsonify({
            "response": assistant_message,
            "query_type": query_type,
            "literature_included": bool(literature_context),
            "usage": {
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0)
            }
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.route('/api/search-literature', methods=['POST'])
def search_literature():
    """Dedicated endpoint for literature searches."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = min(data.get('max_results', 5), 10)  # Cap at 10 for performance
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Search PubMed
        papers = ncbi_service.search_pubmed(query, max_results)
        
        return jsonify({
            "query": query,
            "results": papers,
            "count": len(papers)
        })
        
    except Exception as e:
        print(f"Error in literature search: {e}")
        return jsonify({"error": "Literature search failed"}), 500

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example queries for different categories."""
    examples = {
        "pcr_troubleshooting": [
            "My PCR isn't working - I'm trying to amplify a 1.2kb fragment from mouse genomic DNA",
            "I'm getting multiple bands in my PCR, how can I optimize for specificity?",
            "What's the optimal annealing temperature for primers with 60% GC content?"
        ],
        "experimental_design": [
            "I want to study gene expression changes after drug treatment, what controls should I include?",
            "How many biological replicates do I need for RNA-seq experiment?",
            "I'm designing a CRISPR knockout experiment, what validation steps should I plan?"
        ],
        "protocol_help": [
            "What's the best method for isolating high-quality RNA from tissue samples?",
            "I need to optimize my Western blot protocol for a low-abundance protein",
            "How should I prepare competent cells for electroporation?"
        ],
        "literature_search": [
            "Find recent papers about CRISPR applications in cancer therapy",
            "What are the latest developments in mRNA vaccine technology?",
            "Show me studies comparing different DNA extraction methods"
        ]
    }
    
    return jsonify(examples)

def extract_search_terms(query):
    """Extract key biological terms from user query for literature search."""
    # Simple keyword extraction - could be enhanced with NLP
    biological_keywords = [
        'CRISPR', 'PCR', 'qPCR', 'RNA-seq', 'DNA', 'RNA', 'protein', 'gene',
        'cloning', 'transfection', 'knockout', 'overexpression', 'primer',
        'sequencing', 'gel electrophoresis', 'Western blot', 'immunofluorescence',
        'cell culture', 'bacterial culture', 'plasmid', 'vector', 'enzyme'
    ]
    
    query_lower = query.lower()
    found_keywords = [kw for kw in biological_keywords if kw.lower() in query_lower]
    
    # Return the first few keywords or the original query if no keywords found
    if found_keywords:
        return " ".join(found_keywords[:3])
    else:
        # Extract the first few words as a fallback
        words = query.split()[:5]
        return " ".join(words)

if __name__ == '__main__':
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
    else:
        print(f"OpenAI API key loaded: {api_key[:10]}...")
    
    app.run(debug=True, host='0.0.0.0', port=5002)