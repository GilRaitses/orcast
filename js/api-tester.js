// ORCAST API Tester
// Handles backend API endpoint testing for the inspection panel

class APITester {
    constructor() {
        this.endpoints = {
            predictions: '/api/predictions',
            behavioral: '/api/behavioral-analysis',
            realtime: '/api/real-time-data',
            feeding: '/api/feeding-zones',
            dtag: '/api/dtag-data'
        };
    }

    async testEndpoint(endpoint, responseId) {
        const responseArea = document.getElementById(responseId);
        responseArea.innerHTML = '<span style="color: #ffff80;">Testing...</span>';
        responseArea.className = 'response-area';
        
        try {
            const response = await fetch(endpoint);
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