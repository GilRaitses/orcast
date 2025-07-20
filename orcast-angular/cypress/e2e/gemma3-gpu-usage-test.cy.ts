describe('ORCAST Gemma 3 GPU Container Usage Test', () => {
  const gemma3GpuUrl = 'https://orcast-gemma3-gpu-2cvqukvhga.europe-west4.run.app';
  const testStartTime = new Date().toISOString();
  let requestCount = 0;
  let successfulRequests = 0;
  let failedRequests = 0;
  let totalResponseTime = 0;

  before(() => {
    cy.log('🚀 Starting Gemma 3 GPU Container Usage Test');
    cy.log(`Service URL: ${gemma3GpuUrl}`);
    cy.log(`Test Start Time: ${testStartTime}`);
    cy.log('This test will generate load on the Gemma 3 GPU container and track usage metrics');
  });

  beforeEach(() => {
    requestCount++;
    cy.log(`🔄 Request #${requestCount} starting...`);
  });

  afterEach(() => {
    cy.log(`📊 Total Requests So Far: ${requestCount} | Successful: ${successfulRequests} | Failed: ${failedRequests}`);
    if (successfulRequests > 0) {
      const avgResponseTime = totalResponseTime / successfulRequests;
      cy.log(`⏱️ Average Response Time: ${avgResponseTime.toFixed(2)}ms`);
    }
  });

  describe('🔍 Service Discovery & Health Checks', () => {
    it('should discover available endpoints on Gemma 3 GPU service', () => {
      const startTime = Date.now();
      
      cy.log('🕵️ Testing root endpoint...');
      cy.request({
        method: 'GET',
        url: gemma3GpuUrl,
        failOnStatusCode: false,
        timeout: 30000
      }).then((response) => {
        const responseTime = Date.now() - startTime;
        totalResponseTime += responseTime;
        
        cy.log(`📈 Root Endpoint Response Time: ${responseTime}ms`);
        cy.log(`📊 Status Code: ${response.status}`);
        cy.log(`📝 Headers: ${JSON.stringify(response.headers)}`);
        
        if (response.status === 200) {
          successfulRequests++;
          cy.log('✅ Root endpoint accessible');
        } else {
          failedRequests++;
          cy.log(`⚠️ Root endpoint returned ${response.status}`);
        }
      });
    });

    it('should test common AI service endpoints', () => {
      const endpoints = [
        '/health',
        '/status', 
        '/info',
        '/docs',
        '/openapi.json',
        '/v1/models',
        '/models'
      ];

      endpoints.forEach((endpoint, index) => {
        const startTime = Date.now();
        
        cy.log(`🔍 Testing endpoint: ${endpoint}`);
        cy.request({
          method: 'GET',
          url: `${gemma3GpuUrl}${endpoint}`,
          failOnStatusCode: false,
          timeout: 15000
        }).then((response) => {
          const responseTime = Date.now() - startTime;
          totalResponseTime += responseTime;
          
          cy.log(`📊 ${endpoint} - Status: ${response.status} | Response Time: ${responseTime}ms`);
          
          if (response.status === 200) {
            successfulRequests++;
            cy.log(`✅ ${endpoint} endpoint found and accessible`);
            if (response.body) {
              cy.log(`📝 Response body size: ${JSON.stringify(response.body).length} characters`);
            }
          } else {
            failedRequests++;
            cy.log(`❌ ${endpoint} endpoint not accessible (${response.status})`);
          }
        });
      });
    });
  });

  describe('🤖 AI Service Load Testing', () => {
    it('should test OpenAI-compatible chat completions endpoint', () => {
      const testPrompts = [
        'Hello, can you help with whale behavior analysis?',
        'What are the feeding patterns of orcas in the San Juan Islands?',
        'Analyze whale migration routes in the Pacific Northwest',
        'Generate a summary of orca pod dynamics',
        'Predict whale sighting probabilities'
      ];

      testPrompts.forEach((prompt, index) => {
        const startTime = Date.now();
        
        cy.log(`🧠 Testing AI prompt ${index + 1}: "${prompt.substring(0, 30)}..."`);
        
        cy.request({
          method: 'POST',
          url: `${gemma3GpuUrl}/v1/chat/completions`,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            model: 'gemma',
            messages: [
              {
                role: 'user',
                content: prompt
              }
            ],
            max_tokens: 150,
            temperature: 0.7
          },
          failOnStatusCode: false,
          timeout: 45000
        }).then((response) => {
          const responseTime = Date.now() - startTime;
          totalResponseTime += responseTime;
          
          cy.log(`🚀 AI Request ${index + 1} - Status: ${response.status} | Response Time: ${responseTime}ms`);
          
          if (response.status === 200) {
            successfulRequests++;
            cy.log(`✅ AI generation successful for prompt ${index + 1}`);
            if (response.body && response.body.choices) {
              const responseText = response.body.choices[0]?.message?.content || 'No content';
              cy.log(`📝 AI Response: "${responseText.substring(0, 100)}..."`);
              cy.log(`📊 Response length: ${responseText.length} characters`);
            }
          } else {
            failedRequests++;
            cy.log(`❌ AI generation failed for prompt ${index + 1} (${response.status})`);
          }
        });
      });
    });

    it('should test alternative AI endpoints', () => {
      const aiEndpoints = [
        { endpoint: '/generate', method: 'POST', body: { prompt: 'Test whale analysis', max_tokens: 100 } },
        { endpoint: '/chat', method: 'POST', body: { message: 'Hello AI', max_length: 100 } },
        { endpoint: '/completion', method: 'POST', body: { text: 'Complete this whale behavior analysis', max_tokens: 100 } },
        { endpoint: '/predict', method: 'POST', body: { input: 'Orca behavior prediction', model: 'gemma' } }
      ];

      aiEndpoints.forEach((config, index) => {
        const startTime = Date.now();
        
        cy.log(`🔬 Testing AI endpoint: ${config.endpoint}`);
        
        cy.request({
          method: config.method,
          url: `${gemma3GpuUrl}${config.endpoint}`,
          headers: {
            'Content-Type': 'application/json'
          },
          body: config.body,
          failOnStatusCode: false,
          timeout: 30000
        }).then((response) => {
          const responseTime = Date.now() - startTime;
          totalResponseTime += responseTime;
          
          cy.log(`⚡ ${config.endpoint} - Status: ${response.status} | Response Time: ${responseTime}ms`);
          
          if (response.status === 200) {
            successfulRequests++;
            cy.log(`✅ ${config.endpoint} endpoint working`);
          } else {
            failedRequests++;
            cy.log(`❌ ${config.endpoint} endpoint not available (${response.status})`);
          }
        });
      });
    });
  });

  describe('🏋️ Performance & Load Testing', () => {
    it('should test rapid sequential requests to measure GPU utilization', () => {
      const rapidRequests = 5;
      
      cy.log(`🔥 Starting ${rapidRequests} rapid sequential requests to test GPU load...`);
      
      for (let i = 0; i < rapidRequests; i++) {
        const startTime = Date.now();
        
        cy.request({
          method: 'POST',
          url: `${gemma3GpuUrl}/v1/chat/completions`,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            model: 'gemma',
            messages: [
              {
                role: 'user',
                content: `Rapid request ${i + 1}: Analyze orca behavior patterns in the Pacific Northwest.`
              }
            ],
            max_tokens: 100
          },
          failOnStatusCode: false,
          timeout: 60000
        }).then((response) => {
          const responseTime = Date.now() - startTime;
          totalResponseTime += responseTime;
          
          cy.log(`🚀 Rapid Request ${i + 1} - Status: ${response.status} | Response Time: ${responseTime}ms`);
          
          if (response.status === 200) {
            successfulRequests++;
            cy.log(`✅ Rapid request ${i + 1} successful`);
          } else {
            failedRequests++;
            cy.log(`❌ Rapid request ${i + 1} failed (${response.status})`);
          }
        });
        
        // Minimal delay for rapid testing
        cy.wait(200);
      }
      
      cy.log(`🎯 All ${rapidRequests} rapid requests completed`);
    });

    it('should test sustained load over time', () => {
      const loadTestDuration = 10; // Number of sequential requests
      
      cy.log(`⏰ Starting sustained load test with ${loadTestDuration} sequential requests...`);
      
      for (let i = 0; i < loadTestDuration; i++) {
        const startTime = Date.now();
        
        cy.request({
          method: 'POST',
          url: `${gemma3GpuUrl}/v1/chat/completions`,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            model: 'gemma',
            messages: [
              {
                role: 'user',
                content: `Load test request ${i + 1}: Generate whale behavioral insights for research purposes.`
              }
            ],
            max_tokens: 80
          },
          failOnStatusCode: false,
          timeout: 45000
        }).then((response) => {
          const responseTime = Date.now() - startTime;
          totalResponseTime += responseTime;
          
          cy.log(`🔄 Load Test ${i + 1}/${loadTestDuration} - Status: ${response.status} | Response Time: ${responseTime}ms`);
          
          if (response.status === 200) {
            successfulRequests++;
          } else {
            failedRequests++;
          }
        });
        
        // Add small delay between requests
        cy.wait(1000);
      }
    });
  });

  describe('🔍 Frontend Integration Testing', () => {
    it('should test the live Angular app using Gemma 3 GPU service', () => {
      cy.log('🌐 Testing frontend integration with Gemma 3 GPU service...');
      
      cy.visit('https://orca-904de.web.app');
      cy.get('app-root').should('exist');
      
      cy.log('✅ Angular app loaded successfully');
      
      // Start the demo to trigger backend calls
      cy.get('[data-cy="start-demo-btn"]', { timeout: 10000 }).should('be.visible').click();
      
      cy.log('🚀 Started live demo - this should trigger calls to Gemma 3 GPU service');
      
      // Wait for backend calls to complete
      cy.wait(5000);
      
      // Check for agent messages indicating Gemma 3 GPU service usage
      cy.get('.agent-transcript', { timeout: 15000 }).should('be.visible');
      
      cy.get('.agent-transcript').should('contain.text', 'Gemma 3 GPU');
      cy.get('.agent-transcript').should('contain.text', 'europe-west4');
      
      cy.log('✅ Frontend successfully integrated with Gemma 3 GPU service');
    });

    it('should test agent prompts through the UI', () => {
      cy.visit('https://orca-904de.web.app');
      
      // Test different agent prompts to generate backend load
      const testPrompts = [
        'Load current month sightings',
        'Show recent activity',
        'Analyze feeding behavior',
        'Generate predictions'
      ];
      
      testPrompts.forEach((prompt, index) => {
        cy.log(`🤖 Testing agent prompt: "${prompt}"`);
        
        // Use the agent prompt interface
        cy.get('[data-cy="agent-prompt-input"]', { timeout: 10000 }).should('be.visible').clear().type(prompt);
        cy.get('[data-cy="send-prompt-btn"]').click();
        
        cy.log(`📤 Sent prompt ${index + 1}: "${prompt}"`);
        
        // Wait for response
        cy.wait(3000);
        
        // Check that the transcript shows activity
        cy.get('.agent-transcript').should('contain.text', 'Gemma 3 GPU');
        
        cy.log(`✅ Prompt ${index + 1} processed by Gemma 3 GPU service`);
      });
    });
  });

  after(() => {
    const testEndTime = new Date().toISOString();
    const avgResponseTime = successfulRequests > 0 ? totalResponseTime / successfulRequests : 0;
    
    cy.log('📊 === GEMMA 3 GPU CONTAINER USAGE TEST SUMMARY ===');
    cy.log(`🕐 Test Duration: ${testStartTime} to ${testEndTime}`);
    cy.log(`📈 Total Requests: ${requestCount}`);
    cy.log(`✅ Successful Requests: ${successfulRequests}`);
    cy.log(`❌ Failed Requests: ${failedRequests}`);
    cy.log(`📊 Success Rate: ${((successfulRequests / requestCount) * 100).toFixed(2)}%`);
    cy.log(`⏱️ Average Response Time: ${avgResponseTime.toFixed(2)}ms`);
    cy.log(`🎯 Service URL: ${gemma3GpuUrl}`);
    cy.log(`🌍 Region: europe-west4`);
    cy.log(`💻 Container: orcast-gemma3-gpu`);
    cy.log('==============================================');
    
    // Log final metrics for monitoring
    cy.task('log', `GEMMA3_GPU_USAGE_SUMMARY: ${successfulRequests}/${requestCount} requests successful, ${avgResponseTime.toFixed(2)}ms avg response time`);
  });
}); 