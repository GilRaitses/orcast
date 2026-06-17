describe('🚀 GEMMA 3 GPU LOAD GENERATOR', () => {
  const gemma3GpuUrl = 'https://orcast-gemma3-gpu-2cvqukvhga.europe-west4.run.app';
  let totalRequests = 0;
  let responses: any[] = [];
  
  before(() => {
    cy.log('🔥 STARTING HEAVY LOAD TEST ON GEMMA 3 GPU CONTAINER');
    cy.log(`🎯 Target: ${gemma3GpuUrl}`);
    cy.log('🚀 This will generate significant traffic on your container');
  });

  it('🔥 Heavy Load Test - 20 Rapid Requests', () => {
    cy.log('💥 GENERATING HEAVY LOAD ON GEMMA 3 GPU CONTAINER');
    
    for (let i = 1; i <= 20; i++) {
      const startTime = Date.now();
      totalRequests++;
      
      cy.request({
        method: 'GET',
        url: gemma3GpuUrl,
        failOnStatusCode: false,
        timeout: 10000
      }).then((response) => {
        const responseTime = Date.now() - startTime;
        
        responses.push({
          requestNumber: i,
          statusCode: response.status,
          responseTime: responseTime,
          timestamp: new Date().toISOString()
        });
        
        cy.log(`🚀 Request ${i}/20 - Status: ${response.status} | Time: ${responseTime}ms`);
        
        // Log every 5th request for tracking
        if (i % 5 === 0) {
          cy.log(`📊 PROGRESS: ${i}/20 requests completed`);
        }
      });
      
      // Rapid fire - minimal delay
      if (i < 20) {
        cy.wait(100);
      }
    }
  });

  it('🔬 POST Endpoint Discovery Load Test', () => {
    const testEndpoints = [
      '/v1/chat/completions',
      '/chat/completions', 
      '/generate',
      '/chat',
      '/completion',
      '/predict',
      '/inference',
      '/api/generate'
    ];
    
    testEndpoints.forEach((endpoint, index) => {
      const startTime = Date.now();
      totalRequests++;
      
      cy.log(`🔍 Testing POST ${endpoint}...`);
      
      cy.request({
        method: 'POST',
        url: `${gemma3GpuUrl}${endpoint}`,
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          prompt: `Load test ${index + 1}`,
          message: `Load test ${index + 1}`,
          model: 'gemma',
          max_tokens: 50
        },
        failOnStatusCode: false,
        timeout: 15000
      }).then((response) => {
        const responseTime = Date.now() - startTime;
        
        responses.push({
          requestNumber: totalRequests,
          endpoint: endpoint,
          method: 'POST',
          statusCode: response.status,
          responseTime: responseTime,
          timestamp: new Date().toISOString()
        });
        
        cy.log(`⚡ POST ${endpoint} - Status: ${response.status} | Time: ${responseTime}ms`);
        
        if (response.status === 200) {
          cy.log(`✅ FOUND WORKING ENDPOINT: ${endpoint}`);
        }
      });
      
      cy.wait(200);
    });
  });

  it('🏃 Sprint Test - 10 Ultra-Fast Requests', () => {
    cy.log('🏃‍♂️ SPRINT TEST - Maximum request rate!');
    
    for (let i = 1; i <= 10; i++) {
      const startTime = Date.now();
      totalRequests++;
      
      cy.request({
        method: 'GET',
        url: `${gemma3GpuUrl}/health`,
        failOnStatusCode: false,
        timeout: 5000
      }).then((response) => {
        const responseTime = Date.now() - startTime;
        
        responses.push({
          requestNumber: totalRequests,
          testType: 'sprint',
          statusCode: response.status,
          responseTime: responseTime,
          timestamp: new Date().toISOString()
        });
        
        cy.log(`💨 Sprint ${i}/10 - Status: ${response.status} | Time: ${responseTime}ms`);
      });
      
      // Ultra-minimal delay for maximum rate
      if (i < 10) {
        cy.wait(50);
      }
    }
  });

  it('🎯 Frontend Integration Load Test', () => {
    cy.log('🌐 Testing frontend integration with Gemma 3 GPU...');
    
    cy.visit('https://orca-904de.web.app');
    cy.get('app-root').should('exist');
    
    cy.log('✅ Frontend loaded, triggering backend calls...');
    
    // Try to find and click the start demo button
    cy.get('button').contains('Start').first().click();
    
    cy.log('🚀 Triggered demo start - this hits Gemma 3 GPU service');
    
    cy.wait(3000);
    
    // Look for any indication that the service was called
    cy.get('body').should('contain.text', 'Gemma');
    
    cy.log('✅ Frontend successfully integrated with Gemma 3 GPU service');
  });

  after(() => {
    // Calculate final metrics
    const successfulRequests = responses.filter(r => r.statusCode === 200).length;
    const averageResponseTime = responses.length > 0 ? 
      responses.reduce((sum, r) => sum + r.responseTime, 0) / responses.length : 0;
    
    cy.log('🏁 === GEMMA 3 GPU LOAD TEST COMPLETE ===');
    cy.log(`📊 TOTAL REQUESTS SENT: ${totalRequests}`);
    cy.log(`✅ SUCCESSFUL RESPONSES (200): ${successfulRequests}`);
    cy.log(`❌ NON-200 RESPONSES: ${totalRequests - successfulRequests}`);
    cy.log(`⏱️ AVERAGE RESPONSE TIME: ${averageResponseTime.toFixed(2)}ms`);
    cy.log(`🎯 TARGET CONTAINER: orcast-gemma3-gpu`);
    cy.log(`🌍 REGION: europe-west4`);
    cy.log(`💻 SERVICE URL: ${gemma3GpuUrl}`);
    
    // Log individual response breakdown
    const statusCodes = {};
    responses.forEach(r => {
      statusCodes[r.statusCode] = (statusCodes[r.statusCode] || 0) + 1;
    });
    
    cy.log('📈 RESPONSE STATUS BREAKDOWN:');
    Object.keys(statusCodes).forEach(status => {
      cy.log(`   ${status}: ${statusCodes[status]} requests`);
    });
    
    cy.log('=== CONTAINER SHOULD SHOW SIGNIFICANT ACTIVITY ===');
    
    // Final summary for monitoring
    cy.task('log', `🔥 GEMMA3_GPU_LOAD_TEST_COMPLETE: ${totalRequests} requests sent, ${successfulRequests} successful, ${averageResponseTime.toFixed(2)}ms avg response time`);
  });
}); 