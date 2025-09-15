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

# Import our custom modules
from prompts.bio_prompts import get_prompt, classify_query_type
from services.ncbi_service import NCBIService

# Load environment variables
load_dotenv('../.env')

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Initialize NCBI service
ncbi_service = NCBIService()

def call_openai_api(messages, max_tokens=1000, temperature=0.7):
    """
    Call OpenAI API using requests with fallback to mock responses.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    use_mock = os.getenv('USE_MOCK_AI', 'false').lower() == 'true'
    
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
        
        if response.status_code == 429:  # Quota exceeded
            print("API quota exceeded, falling back to mock response")
            return get_mock_response(messages)
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
        
        return response.json()
        
    except Exception as e:
        print(f"API call failed: {e}, using mock response")
        return get_mock_response(messages)

def get_mock_response(messages):
    """Generate a mock response based on the query type."""
    user_message = messages[-1]['content'].lower()
    
    if 'pcr' in user_message:
        mock_content = """For PCR troubleshooting, here are the most common issues to check:

1. **Primer Issues**: Verify primer concentration (0.1-1 μM final), check for primer dimers, ensure proper annealing temperature (usually Tm - 5°C).

2. **Template Quality**: Check DNA concentration and purity (A260/A280 ratio should be 1.8-2.0). Try diluting template if concentration is too high.

3. **Reaction Components**: 
   - Verify polymerase activity and storage
   - Check dNTP concentrations (200 μM each)
   - Ensure proper buffer and MgCl2 concentration (1.5-2.5 mM)

4. **Thermal Cycling**: 
   - Initial denaturation: 95°C for 3-5 min
   - Denaturation: 95°C for 30 sec
   - Annealing: Primer Tm - 5°C for 30 sec
   - Extension: 72°C for 1 min/kb

5. **Controls**: Always include positive and negative controls.

Try these systematically, changing one variable at a time to identify the issue."""
    
    elif 'crispr' in user_message:
        mock_content = """For CRISPR experiments, consider these key points:

1. **Guide RNA Design**: Use online tools like Benchling or Chopchop for optimal targeting. Ensure 17-20 bp target sequence with NGG PAM.

2. **Off-target Analysis**: Check for potential off-target sites using tools like COSMID or Cas-OFFinder.

3. **Delivery Method**: Choose appropriate method (transfection, electroporation, viral delivery) based on cell type.

4. **Controls**: Include untransfected cells, cells with Cas9 only, and non-targeting guide controls.

5. **Validation**: Plan for PCR amplification and sequencing of target region, plus functional assays if relevant.

6. **Timing**: Harvest cells 48-72 hours post-transfection for analysis."""
    
    elif 'experimental design' in user_message or 'control' in user_message:
        mock_content = """Good experimental design principles:

1. **Define Clear Hypothesis**: State exactly what you're testing.

2. **Controls**:
   - Negative control (no treatment)
   - Positive control (known effect)
   - Vehicle control (if using solvents)
   - Untreated control

3. **Replication**:
   - Biological replicates: Independent samples (n≥3)
   - Technical replicates: Same sample measured multiple times

4. **Randomization**: Randomize sample processing order and placement.

5. **Blinding**: Process samples without knowing treatment groups when possible.

6. **Statistical Power**: Calculate required sample size before starting.

7. **Standardization**: Keep all variables constant except the one being tested."""
    
    else:
        mock_content = f"""Thank you for your question about molecular biology. Here's some general guidance:

Based on your query, I recommend:
1. Reviewing standard protocols for your specific technique
2. Ensuring proper controls are included
3. Checking reagent quality and storage conditions
4. Following established troubleshooting guides

For specific techniques like PCR, Western blotting, or cell culture, there are well-established protocols that can help guide your approach.

*Note: This is a mock response for development. The full AI integration will provide more detailed, personalized advice.*"""
    
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
        
        assistant_message = response_data['choices'][0]['message']['content']
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
    
    app.run(debug=True, host='0.0.0.0', port=5001)