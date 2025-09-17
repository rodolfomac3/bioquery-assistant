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

from prompts.bio_prompts import get_prompt, classify_query_type
from services.ncbi_service import NCBIService

load_dotenv('.env')

app = Flask(__name__)

# CORS for frontend (Render + local dev)
CORS(
    app,
    resources={r"/*": {"origins": [
        "https://bioquery-frontend.onrender.com",
        "http://localhost:3000"
    ]}},
    supports_credentials=False
)

ncbi_service = NCBIService()


def format_response(response_text):
    """Enhanced response formatting with professional markdown rendering."""
    
    # Enhanced step formatting with better visual hierarchy
    response_text = re.sub(r'(\d+\.)\s*\*\*([^*]+)\*\*:', r'\n\n### \1 \2\n', response_text)
    
    # Formula and equation formatting - use code blocks for better rendering
    response_text = re.sub(r'\\?\[([^]]+)\\?\]', r'`\1`', response_text)
    
    # Enhanced step number formatting for better readability
    response_text = re.sub(r'^(\d+)\.\s+\*\*([^*]+)\*\*:', r'#### **Step \1: \2**', response_text, flags=re.MULTILINE)
    
    # Enhanced note formatting with better visual distinction
    response_text = re.sub(r'\*Note:([^*]+)\*', r'\n> 📝 **Note:** \1\n', response_text)
    
    # Enhanced warning formatting
    response_text = re.sub(r'\*Warning:([^*]+)\*', r'\n> ⚠️ **Warning:** \1\n', response_text)
    
    # Enhanced tip formatting
    response_text = re.sub(r'\*Tip:([^*]+)\*', r'\n> 💡 **Tip:** \1\n', response_text)
    
    # Add success/validation formatting
    response_text = re.sub(r'\*Success:([^*]+)\*', r'\n> ✅ **Success:** \1\n', response_text)
    
    # Add critical information formatting
    response_text = re.sub(r'\*Critical:([^*]+)\*', r'\n> 🚨 **Critical:** \1\n', response_text)
    
    # Add protocol step formatting
    response_text = re.sub(r'\*Protocol:([^*]+)\*', r'\n> 🧪 **Protocol:** \1\n', response_text)
    
    # Add troubleshooting formatting
    response_text = re.sub(r'\*Troubleshoot:([^*]+)\*', r'\n> 🔧 **Troubleshoot:** \1\n', response_text)
    
    # Add validation formatting
    response_text = re.sub(r'\*Validate:([^*]+)\*', r'\n> ✓ **Validate:** \1\n', response_text)
    
    # Enhanced section header formatting - use proper markdown headers
    response_text = re.sub(r'\*\*([A-Z][A-Z\s]+):\*\*', r'\n\n## \1\n', response_text)
    
    # Enhanced subsection formatting
    response_text = re.sub(r'\*\*([A-Z][a-z\s]+):\*\*', r'\n\n### \1\n', response_text)
    
    # Add parameter highlighting - use bold for emphasis
    response_text = re.sub(r'(\w+):\s*([0-9.-]+[°μM%x\s]*[A-Za-z]*)', r'**\1:** `\2`', response_text)
    
    # Add concentration highlighting - use inline code for better visibility
    response_text = re.sub(r'(\d+\.?\d*)\s*(mM|μM|nM|pM|mg/mL|μg/mL|ng/mL|U/μL|units/mL)', r'`\1 \2`', response_text)
    
    # Add temperature highlighting
    response_text = re.sub(r'(\d+\.?\d*)\s*°C', r'`\1°C`', response_text)
    
    # Add time highlighting
    response_text = re.sub(r'(\d+\.?\d*)\s*(min|minute|hr|hour|sec|second|day|week)', r'`\1 \2`', response_text)
    
    # Clean up excessive whitespace
    response_text = re.sub(r'\n\n+', '\n\n', response_text)
    
    # Add confidence level indicators - use badges
    response_text = re.sub(r'\(High confidence\)', r'`🔴 High Confidence`', response_text)
    response_text = re.sub(r'\(Medium confidence\)', r'`🟡 Medium Confidence`', response_text)
    response_text = re.sub(r'\(Low confidence\)', r'`🟢 Low Confidence`', response_text)
    
    # Add bullet point formatting for lists
    response_text = re.sub(r'^- ', r'• ', response_text, flags=re.MULTILINE)
    
    # Add numbered list formatting
    response_text = re.sub(r'^(\d+)\. ', r'\1. ', response_text, flags=re.MULTILINE)
    
    # Add code block formatting for protocols
    response_text = re.sub(r'```\n(.*?)\n```', r'```\n\1\n```', response_text, flags=re.DOTALL)
    
    return response_text.strip()


def call_openai_api(messages, max_tokens=2000, temperature=0.3):
    """Enhanced API call with optimized parameters for scientific accuracy."""
    api_key = os.getenv('OPENAI_API_KEY')
    use_mock = False

    if use_mock or not api_key:
        return get_mock_response(messages)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': 'gpt-4o-mini',  # Using gpt-4o-mini for better performance
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,  # Lower temperature for more consistent, factual responses
        'top_p': 0.9,  # Focus on most likely tokens
        'frequency_penalty': 0.1,  # Slight penalty to avoid repetition
        'presence_penalty': 0.1,  # Encourage diverse topics
        'stop': None  # No stop sequences for scientific content
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            return get_mock_response(messages)

        return response.json()

    except Exception:
        return get_mock_response(messages)


def get_mock_response(messages):
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
    return jsonify({
        "status": "healthy",
        "message": "BioQuery Assistant API is running",
        "version": "1.0.0"
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        include_literature = data.get('include_literature', False)

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        query_type = classify_query_type(user_message)
        system_prompt = get_prompt(query_type)

        if query_type == "general_bio" and not any(keyword in user_message.lower() for keyword in [
            'biology', 'dna', 'rna', 'protein', 'gene', 'pcr', 'crispr', 'cell', 'molecular',
            'biochemistry', 'genetics', 'experiment', 'lab', 'assay', 'culture', 'western',
            'blot', 'electrophoresis', 'cloning', 'transfection', 'molarity', 'concentration',
            'primer', 'sequencing', 'plasmid', 'vector', 'enzyme', 'antibody', 'microscopy'
        ]):
            system_prompt = """
You are a helpful biology research assistant. 
When providing step-by-step instructions, use this format:

**Step 1: Symptoms**
Your content here...

**Step 2: Template** 
Your content here...

Do NOT use HTML tags. Use Markdown formatting instead.
"""

        literature_context = ""
        if include_literature:
            try:
                search_terms = extract_search_terms(user_message)
                if search_terms:
                    papers = ncbi_service.get_recent_papers(search_terms, max_results=3)
                    literature_context = ncbi_service.format_articles_for_llm(papers)
            except Exception:
                literature_context = "Literature search unavailable at the moment."

        messages = [{"role": "system", "content": system_prompt}]
        if literature_context:
            enhanced_message = f"{user_message}\n\nRelevant recent literature:\n{literature_context}"
            messages.append({"role": "user", "content": enhanced_message})
        else:
            messages.append({"role": "user", "content": user_message})

        response_data = call_openai_api(messages)

        raw_message = response_data['choices'][0]['message']['content']
        
        # Quality control checks
        quality_score = assess_response_quality(raw_message, query_type)
        
        # Apply quality-based formatting
        if quality_score < 0.7:
            # Add quality warning to response
            raw_message = f"*Note: This response may need additional validation. Please cross-reference with primary literature.*\n\n{raw_message}"
        
        assistant_message = format_response(raw_message)
        usage = response_data.get('usage', {})

        return jsonify({
            "response": assistant_message,
            "query_type": query_type,
            "literature_included": bool(literature_context),
            "quality_score": quality_score,
            "confidence_level": get_confidence_level(quality_score),
            "usage": {
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0)
            }
        })

    except Exception:
        return jsonify({"error": "An error occurred processing your request"}), 500


@app.route('/api/search-literature', methods=['POST'])
def search_literature():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = min(data.get('max_results', 5), 10)

        if not query:
            return jsonify({"error": "Query is required"}), 400

        papers = ncbi_service.search_pubmed(query, max_results)

        return jsonify({
            "query": query,
            "results": papers,
            "count": len(papers)
        })

    except Exception:
        return jsonify({"error": "Literature search failed"}), 500


@app.route('/api/examples', methods=['GET'])
def get_examples():
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


def assess_response_quality(response_text, query_type):
    """Assess the quality of AI response based on scientific rigor and completeness."""
    quality_indicators = {
        'specificity': 0,
        'scientific_rigor': 0,
        'completeness': 0,
        'actionability': 0,
        'structure': 0
    }
    
    # Check for specific parameters and values
    if re.search(r'\d+\.?\d*\s*(mM|μM|nM|°C|min|hr)', response_text):
        quality_indicators['specificity'] += 0.3
    
    # Check for scientific terminology and methodology
    scientific_terms = ['control', 'replicate', 'validation', 'protocol', 'optimization', 'troubleshooting']
    if sum(1 for term in scientific_terms if term.lower() in response_text.lower()) >= 3:
        quality_indicators['scientific_rigor'] += 0.3
    
    # Check for structured format
    if re.search(r'\*\*[A-Z][A-Z\s]+:\*\*', response_text):
        quality_indicators['structure'] += 0.2
    
    # Check for step-by-step instructions
    if re.search(r'\d+\.\s+', response_text):
        quality_indicators['actionability'] += 0.2
    
    # Check for completeness based on query type
    if query_type == "pcr_troubleshooting":
        if all(term in response_text.lower() for term in ['temperature', 'primer', 'template']):
            quality_indicators['completeness'] += 0.3
    elif query_type == "experimental_design":
        if all(term in response_text.lower() for term in ['control', 'replicate', 'sample']):
            quality_indicators['completeness'] += 0.3
    elif query_type == "literature_synthesis":
        if all(term in response_text.lower() for term in ['study', 'research', 'evidence']):
            quality_indicators['completeness'] += 0.3
    else:
        if len(response_text) > 500:  # General bio responses should be comprehensive
            quality_indicators['completeness'] += 0.3
    
    # Calculate overall quality score
    total_score = sum(quality_indicators.values())
    return min(total_score, 1.0)  # Cap at 1.0


def get_confidence_level(quality_score):
    """Convert quality score to confidence level."""
    if quality_score >= 0.8:
        return "High"
    elif quality_score >= 0.6:
        return "Medium"
    else:
        return "Low"


def extract_search_terms(query):
    biological_keywords = [
        'CRISPR', 'PCR', 'qPCR', 'RNA-seq', 'DNA', 'RNA', 'protein', 'gene',
        'cloning', 'transfection', 'knockout', 'overexpression', 'primer',
        'sequencing', 'gel electrophoresis', 'Western blot', 'immunofluorescence',
        'cell culture', 'bacterial culture', 'plasmid', 'vector', 'enzyme'
    ]

    query_lower = query.lower()
    found_keywords = [kw for kw in biological_keywords if kw.lower() in query_lower]

    if found_keywords:
        return " ".join(found_keywords[:3])
    else:
        words = query.split()[:5]
        return " ".join(words)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
