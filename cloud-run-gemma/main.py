#!/usr/bin/env python3
"""
ORCAST Gemma 3 Cloud Run GPU Service
For Google Cloud Hackathon - Agentic AI Trip Planning

This service hosts Gemma 3 model on Cloud Run GPU for orca trip planning inference.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
import google.cloud.logging

# Configure logging
client = google.cloud.logging.Client()
client.setup_logging()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global model and tokenizer
model = None
tokenizer = None

# Configuration
MODEL_NAME = os.getenv('MODEL_NAME', 'google/gemma-2-2b-it')
PORT = int(os.getenv('PORT', 8080))
MAX_LENGTH = 2048
TEMPERATURE = 0.3

class GemmaInferenceService:
    """Gemma 3 inference service for ORCAST trip planning"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.load_model()
    
    def _get_device(self) -> str:
        """Detect and return appropriate device (GPU/CPU)"""
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            device = "cpu"
            logger.warning("GPU not available, using CPU")
        return device
    
    def load_model(self):
        """Load Gemma 3 model and tokenizer"""
        try:
            logger.info(f"Loading model: {MODEL_NAME}")
            start_time = time.time()
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            
            # Load model with GPU optimization
            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    torch_dtype=torch.float16,  # Use half precision for memory efficiency
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    trust_remote_code=True
                )
                self.model.to(self.device)
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def generate_response(self, prompt: str, max_length: int = MAX_LENGTH, temperature: float = TEMPERATURE) -> str:
        """Generate response using Gemma 3 model"""
        try:
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove input prompt from response
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise

# Initialize service
inference_service = GemmaInferenceService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': MODEL_NAME,
        'device': inference_service.device,
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/generate', methods=['POST'])
def generate():
    """Main inference endpoint for ORCAST trip planning"""
    try:
        # Parse request
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Missing prompt in request'}), 400
        
        prompt = data['prompt']
        max_length = data.get('max_length', MAX_LENGTH)
        temperature = data.get('temperature', TEMPERATURE)
        
        logger.info(f"Generating response for prompt length: {len(prompt)}")
        
        # Generate response
        start_time = time.time()
        response = inference_service.generate_response(prompt, max_length, temperature)
        generation_time = time.time() - start_time
        
        logger.info(f"Response generated in {generation_time:.2f} seconds")
        
        return jsonify({
            'response': response,
            'generation_time': generation_time,
            'model': MODEL_NAME,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/extract-constraints', methods=['POST'])
def extract_constraints():
    """Extract trip planning constraints from natural language"""
    try:
        data = request.get_json()
        user_input = data.get('input', '')
        
        # ORCAST-specific prompt for constraint extraction
        prompt = f"""Extract trip planning constraints from the following user input and return as JSON.

User input: "{user_input}"

Please extract the following constraints if mentioned:
- timeframe: weekend, weekday, specific dates
- duration: number of days  
- preferredTime: morning, afternoon, evening, all-day
- viewingType: land, boat, ferry, mixed
- accommodation: balcony, waterfront, budget, luxury
- region: san_juan_islands, puget_sound, seattle_area, specific_location
- budget: low, medium, high, specific_amount
- groupSize: number of people
- accessibility: mobility, dietary, other special needs
- interests: photography, education, relaxation, adventure

Return only valid JSON in this format:
{{
  "timeframe": "string or null",
  "duration": number or null,
  "preferredTime": "string or null",
  "viewingType": "string or null", 
  "accommodation": "string or null",
  "region": "string or null",
  "budget": "string or null",
  "groupSize": number or null,
  "accessibility": ["array of strings"] or null,
  "interests": ["array of strings"] or null,
  "confidence": number between 0 and 1
}}

JSON:"""

        response = inference_service.generate_response(prompt, 1024, 0.1)
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                constraints = json.loads(json_str)
            else:
                # Fallback to rule-based extraction
                constraints = fallback_constraint_extraction(user_input)
        except json.JSONDecodeError:
            constraints = fallback_constraint_extraction(user_input)
        
        return jsonify(constraints)
        
    except Exception as e:
        logger.error(f"Constraint extraction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def fallback_constraint_extraction(text: str) -> Dict:
    """Fallback rule-based constraint extraction"""
    constraints = {}
    lower_text = text.lower()
    
    # Time constraints
    if 'weekend' in lower_text:
        constraints['timeframe'] = 'weekend'
    if 'weekday' in lower_text:
        constraints['timeframe'] = 'weekday'
    if 'morning' in lower_text:
        constraints['preferredTime'] = 'morning'
    if 'afternoon' in lower_text:
        constraints['preferredTime'] = 'afternoon'
    if 'evening' in lower_text:
        constraints['preferredTime'] = 'evening'
    
    # Duration
    import re
    duration_match = re.search(r'(\d+)\s?(day|days)', lower_text)
    if duration_match:
        constraints['duration'] = int(duration_match.group(1))
    
    # Viewing preferences
    if 'land' in lower_text or 'shore' in lower_text:
        constraints['viewingType'] = 'land'
    if 'boat' in lower_text or 'ferry' in lower_text:
        constraints['viewingType'] = 'boat'
    if 'balcony' in lower_text:
        constraints['accommodation'] = 'balcony'
    
    # Location preferences
    if 'san juan' in lower_text:
        constraints['region'] = 'san_juan_islands'
    if 'seattle' in lower_text:
        constraints['region'] = 'puget_sound'
    
    # Group size
    group_match = re.search(r'(\d+)\s?(people|person|adults?|guests?)', lower_text)
    if group_match:
        constraints['groupSize'] = int(group_match.group(1))
    
    # Interests
    interests = []
    if 'photo' in lower_text:
        interests.append('photography')
    if 'learn' in lower_text or 'education' in lower_text:
        interests.append('education')
    if 'relax' in lower_text:
        interests.append('relaxation')
    if 'adventure' in lower_text or 'exciting' in lower_text:
        interests.append('adventure')
    if interests:
        constraints['interests'] = interests
    
    constraints['confidence'] = 0.7
    return constraints

@app.route('/info', methods=['GET'])
def model_info():
    """Return model information"""
    return jsonify({
        'model_name': MODEL_NAME,
        'device': inference_service.device,
        'max_length': MAX_LENGTH,
        'temperature': TEMPERATURE,
        'gpu_available': torch.cuda.is_available(),
        'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
        'service': 'ORCAST Gemma 3 Inference',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    logger.info(f"Starting ORCAST Gemma 3 service on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False) 