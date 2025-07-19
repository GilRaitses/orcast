/**
 * ORCAST Gemini API Integration
 * Natural language processing for agentic trip planning
 */

class GeminiIntegration {
    constructor(config = {}) {
        this.apiKey = config.apiKey || window.ORCA_CONFIG?.gemini?.apiKey || window.ORCA_CONFIG?.apiKeys?.GEMINI;
        this.projectId = config.projectId || window.ORCA_CONFIG?.gemini?.projectId || 'orca-466204';
        this.model = config.model || window.ORCA_CONFIG?.gemini?.model || 'gemini-pro';
        this.baseUrl = 'https://generativelanguage.googleapis.com/v1beta';
        
        if (!this.apiKey) {
            console.warn('Gemini API key not found. Using fallback rule-based processing.');
        }
        
        this.initializePrompts();
    }

    /**
     * Initialize prompt templates for different planning tasks
     */
    initializePrompts() {
        this.prompts = {
            constraintExtraction: `
Extract trip planning constraints from the following user input and return as JSON.

User input: "{input}"

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
{
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
}
            `,
            
            planOptimization: `
Optimize the following orca watching trip plan based on constraints and probability data.

Constraints: {constraints}
Available locations: {locations}
Probability data: {probabilityData}
Weather forecast: {weather}

Please provide optimization suggestions in JSON format:
{
  "recommendedChanges": [
    {
      "type": "location_change" | "time_adjustment" | "activity_addition",
      "description": "string",
      "reason": "string",
      "probabilityImprovement": number
    }
  ],
  "alternativeOptions": [
    {
      "description": "string",
      "probabilityScore": number,
      "pros": ["array of strings"],
      "cons": ["array of strings"]
    }
  ],
  "confidence": number between 0 and 1
}
            `,
            
            planGeneration: `
Generate a detailed orca watching trip plan based on these constraints:

{constraints}

Available viewing locations with probability scores:
{locations}

Create a comprehensive plan including:
1. Day-by-day schedule with optimal viewing times
2. Location recommendations with probability justification
3. Accommodation suggestions if specified
4. Equipment and preparation recommendations
5. Weather contingency plans

Return as JSON:
{
  "timeline": [
    {
      "day": number,
      "date": "ISO date string",
      "schedule": [
        {
          "time": "time range string",
          "activity": "string",
          "location": "string", 
          "probabilityScore": number,
          "details": "string",
          "alternatives": ["array of strings"]
        }
      ]
    }
  ],
  "logistics": {
    "accommodation": ["array of recommendations"],
    "transportation": ["array of options"],
    "equipment": ["array of items"],
    "tips": ["array of helpful tips"]
  },
  "contingencyPlans": [
    {
      "condition": "string (e.g., bad weather)",
      "alternatives": ["array of alternative activities"]
    }
  ],
  "overallProbabilityScore": number,
  "confidence": number between 0 and 1
}
            `
        };
    }

    /**
     * Extract planning constraints from natural language input
     */
    async extractConstraints(userInput) {
        if (!this.apiKey) {
            console.log('Using fallback constraint extraction');
            return this.fallbackConstraintExtraction(userInput);
        }

        try {
            const prompt = this.prompts.constraintExtraction.replace('{input}', userInput);
            const response = await this.callGeminiAPI(prompt);
            
            // Parse JSON response
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            } else {
                throw new Error('No valid JSON found in response');
            }
            
        } catch (error) {
            console.error('Gemini constraint extraction failed:', error);
            return this.fallbackConstraintExtraction(userInput);
        }
    }

    /**
     * Optimize existing trip plan with AI suggestions
     */
    async optimizePlan(plan, constraints, additionalData = {}) {
        if (!this.apiKey) {
            return { recommendedChanges: [], alternativeOptions: [], confidence: 0.7 };
        }

        try {
            const prompt = this.prompts.planOptimization
                .replace('{constraints}', JSON.stringify(constraints))
                .replace('{locations}', JSON.stringify(plan.locations))
                .replace('{probabilityData}', JSON.stringify(additionalData.probabilityData || {}))
                .replace('{weather}', JSON.stringify(additionalData.weather || {}));

            const response = await this.callGeminiAPI(prompt);
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
            
            return { recommendedChanges: [], alternativeOptions: [], confidence: 0.5 };
            
        } catch (error) {
            console.error('Gemini plan optimization failed:', error);
            return { recommendedChanges: [], alternativeOptions: [], confidence: 0.3 };
        }
    }

    /**
     * Generate complete trip plan using AI
     */
    async generatePlan(constraints, locations, additionalData = {}) {
        if (!this.apiKey) {
            return null; // Fall back to rule-based generation
        }

        try {
            const prompt = this.prompts.planGeneration
                .replace('{constraints}', JSON.stringify(constraints))
                .replace('{locations}', JSON.stringify(locations));

            const response = await this.callGeminiAPI(prompt);
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            
            if (jsonMatch) {
                const plan = JSON.parse(jsonMatch[0]);
                plan.id = Date.now();
                plan.created = new Date().toISOString();
                plan.constraints = constraints;
                return plan;
            }
            
            return null;
            
        } catch (error) {
            console.error('Gemini plan generation failed:', error);
            return null;
        }
    }

    /**
     * Make API call to Gemini
     */
    async callGeminiAPI(prompt, options = {}) {
        const url = `${this.baseUrl}/models/${this.model}:generateContent?key=${this.apiKey}`;
        
        const requestBody = {
            contents: [{
                parts: [{
                    text: prompt
                }]
            }],
            generationConfig: {
                temperature: options.temperature || 0.3,
                topK: options.topK || 1,
                topP: options.topP || 0.8,
                maxOutputTokens: options.maxOutputTokens || 2048,
            },
            safetySettings: [
                {
                    category: "HARM_CATEGORY_HARASSMENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_HATE_SPEECH", 
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Gemini API error: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        
        if (data.candidates && data.candidates[0] && data.candidates[0].content) {
            return data.candidates[0].content.parts[0].text;
        } else {
            throw new Error('Unexpected Gemini API response format');
        }
    }

    /**
     * Fallback constraint extraction using rule-based approach
     */
    fallbackConstraintExtraction(text) {
        const constraints = {};
        const lowerText = text.toLowerCase();
        
        // Time constraints
        if (lowerText.includes('weekend')) constraints.timeframe = 'weekend';
        if (lowerText.includes('weekday')) constraints.timeframe = 'weekday';
        if (lowerText.includes('morning')) constraints.preferredTime = 'morning';
        if (lowerText.includes('afternoon')) constraints.preferredTime = 'afternoon';
        if (lowerText.includes('evening')) constraints.preferredTime = 'evening';
        
        // Duration
        const durationMatch = lowerText.match(/(\d+)\s?(day|days)/);
        if (durationMatch) constraints.duration = parseInt(durationMatch[1]);
        
        // Viewing preferences
        if (lowerText.includes('land') || lowerText.includes('shore')) {
            constraints.viewingType = 'land';
        }
        if (lowerText.includes('boat') || lowerText.includes('ferry')) {
            constraints.viewingType = 'boat';
        }
        if (lowerText.includes('balcony')) {
            constraints.accommodation = 'balcony';
        }
        
        // Location preferences
        if (lowerText.includes('san juan')) constraints.region = 'san_juan_islands';
        if (lowerText.includes('seattle')) constraints.region = 'puget_sound';
        
        // Group size
        const groupMatch = lowerText.match(/(\d+)\s?(people|person|adults?|guests?)/);
        if (groupMatch) constraints.groupSize = parseInt(groupMatch[1]);
        
        // Interests
        const interests = [];
        if (lowerText.includes('photo')) interests.push('photography');
        if (lowerText.includes('learn') || lowerText.includes('education')) interests.push('education');
        if (lowerText.includes('relax')) interests.push('relaxation');
        if (lowerText.includes('adventure') || lowerText.includes('exciting')) interests.push('adventure');
        if (interests.length > 0) constraints.interests = interests;
        
        constraints.confidence = 0.7; // Medium confidence for rule-based extraction
        
        return constraints;
    }

    /**
     * Test the API connection
     */
    async testConnection() {
        try {
            const response = await this.callGeminiAPI('Respond with just "OK" if you can hear me.');
            return response.trim().toLowerCase().includes('ok');
        } catch (error) {
            console.error('Gemini API connection test failed:', error);
            return false;
        }
    }
}

// Export for use in other modules
window.GeminiIntegration = GeminiIntegration; 