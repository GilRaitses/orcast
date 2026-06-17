// ORCAST API Tester
// Handles backend API endpoint testing for the inspection panel

class APITester {
    constructor() {
        this.endpoints = {
            health: '/health',
            sightings: '/api/sightings',
            verified: '/api/verified-sightings',
            report: '/api/reports/probability',
            spatial: '/forecast/spatial',
            status: '/api/status'
        };
    }

    async testEndpoint(endpoint, responseId) {
        const responseArea = document.getElementById(responseId);
        responseArea.innerHTML = '<span style="color: #ffff80;">Testing...</span>';
        responseArea.className = 'response-area';
        
        try {
            const options = endpoint.includes('/api/reports/probability') || endpoint.includes('/forecast/spatial')
                ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ min_confidence: 0 }) }
                : {};
            const response = await fetch(endpoint, options);
            const contentType = response.headers.get('content-type');
            
            let data;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
                data = JSON.stringify(data, null, 2); // Pretty format JSON
            } else {
                data = await response.text();
            }
            
            if (response.ok) {
                // Limit response size to prevent browser hang
                const displayData = data.length > 2000 ? data.substring(0, 2000) + '\n\n... (truncated)' : data;
                responseArea.innerHTML = `<span style="color: #4fc3f7;">✓ Status: ${response.status} OK</span>\n\n<pre style="white-space: pre-wrap; font-size: 0.8rem; max-height: 300px; overflow-y: auto;">${displayData}</pre>`;
            } else {
                responseArea.innerHTML = `<span style="color: #ff6b6b;">✗ Status: ${response.status}</span>\n\n${data}`;
            }
        } catch (error) {
            responseArea.innerHTML = `<span style="color: #ff6b6b;">✗ Network Error:</span>\n${error.message}`;
        }
    }

    setupAPIButtons() {
        // Set up click handlers for all API test buttons
        document.querySelectorAll('.test-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const endpoint = e.target.getAttribute('data-endpoint');
                const responseId = e.target.getAttribute('data-response-id');
                if (endpoint && responseId) {
                    this.testEndpoint(endpoint, responseId);
                }
            });
        });
    }
}

// Export for use
window.apiTester = new APITester();
