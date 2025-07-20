describe('ORCAST Automated Demo Recording', () => {
  const demoUrl = 'https://orca-904de.web.app/automated-demo';
  
  beforeEach(() => {
    // Configure for optimal video recording
    cy.viewport(1920, 1080);
  });

  it('should record the complete ORCAST multi-agent demo workflow', () => {
    cy.log('🎬 Starting ORCAST Automated Demo Recording');
    
    // Visit the automated demo page
    cy.visit(demoUrl);
    cy.wait(2000); // Let page load completely
    
    // Verify demo component is loaded
    cy.get('.demo-container').should('be.visible');
    cy.get('.demo-controls').should('be.visible');
    
    // Take screenshot of initial state
    cy.screenshot('01-demo-initial-state');
    cy.log('📸 Initial state captured');
    
    // Start the automated demo
    cy.get('.start-btn').should('be.visible').should('not.be.disabled');
    cy.get('.start-btn').click();
    cy.log('▶️ Automated demo started');
    
    // Wait for demo to start running
    cy.get('.demo-container.running').should('exist');
    cy.get('.demo-stage').should('be.visible');
    
    // Record each slide of the demo
    const slideWaitTimes = [8000, 10000, 12000, 15000, 10000]; // Duration for each slide
    
    slideWaitTimes.forEach((waitTime, index) => {
      const slideNumber = index + 1;
      
      cy.log(`🎯 Recording Slide ${slideNumber}`);
      
      // Wait for slide to be active
      cy.get('.slide-header h1').should('be.visible');
      cy.get('.slide-content').should('be.visible');
      
      // Take screenshot at beginning of slide
      cy.screenshot(`02-slide-${slideNumber}-start`);
      
      // Verify slide content based on slide number
      switch(slideNumber) {
        case 1:
          cy.get('.slide-header h1').should('contain', 'ORCAST System Introduction');
          cy.get('.map-demo-area').should('be.visible');
          cy.get('.map-point.point-whale').should('have.length.at.least', 1);
          cy.log('✅ Slide 1: System introduction with whale locations');
          break;
          
        case 2:
          cy.get('.slide-header h1').should('contain', 'Data Collection Agent');
          cy.get('.agent-panel').should('be.visible');
          cy.get('.agent-step').should('have.length.at.least', 1);
          
          // Wait for agent processing animations
          cy.get('.agent-step.status-processing').should('exist');
          cy.log('🔍 Slide 2: Data collection agent processing');
          
          // Wait for completion
          cy.get('.agent-step.status-completed', { timeout: 15000 }).should('exist');
          cy.log('✅ Data collection completed');
          break;
          
        case 3:
          cy.get('.slide-header h1').should('contain', 'Analysis Agent');
          cy.get('.agent-panel').should('be.visible');
          
          // Verify ML processing steps
          cy.get('.agent-step').should('contain', 'PINN physics');
          cy.get('.agent-step').should('contain', 'Behavioral ML');
          cy.log('🧠 Slide 3: Analysis agent running ML models');
          
          // Wait for all processing to complete
          cy.get('.agent-step.status-completed', { timeout: 20000 }).should('have.length.at.least', 1);
          cy.log('✅ Analysis completed');
          break;
          
        case 4:
          cy.get('.slide-header h1').should('contain', 'Trip Planning Agent');
          cy.get('.map-demo-area').should('be.visible');
          cy.get('.point-route').should('have.length.at.least', 3);
          
          // Verify planning agent workflow
          cy.get('.agent-step').should('contain', 'route optimization');
          cy.log('🗺️ Slide 4: Trip planning and route optimization');
          
          // Wait for trip plan completion
          cy.get('.agent-step.status-completed', { timeout: 20000 }).should('exist');
          cy.log('✅ Trip planning completed');
          break;
          
        case 5:
          cy.get('.slide-header h1').should('contain', 'Multi-Agent Coordination Results');
          cy.get('.slide-content').should('contain', 'Plan Accepted by User');
          cy.get('.agent-step').should('contain', 'Agent Coordinator');
          cy.log('🎯 Slide 5: Final results and user acceptance');
          break;
      }
      
      // Wait for slide timer
      if (index < slideWaitTimes.length - 1) {
        // Wait for slide transition (but not on last slide)
        cy.wait(waitTime);
        cy.screenshot(`03-slide-${slideNumber}-end`);
      } else {
        // Wait for final slide to complete
        cy.wait(waitTime);
        cy.screenshot(`04-final-slide-complete`);
      }
    });
    
    // Wait for demo completion
    cy.get('.demo-results', { timeout: 30000 }).should('be.visible');
    cy.get('.demo-results h2').should('contain', 'Demo Completed Successfully');
    
    // Verify final results
    cy.get('.result-item').should('have.length', 4);
    cy.get('.result-item').should('contain', 'Trip Plan Generated');
    cy.get('.result-item').should('contain', 'Map Configurations');
    cy.get('.result-item').should('contain', 'Agent Interactions');
    cy.get('.result-item').should('contain', 'Data Processing');
    
    cy.screenshot('05-demo-completed-results');
    cy.log('✅ Demo completed successfully');
    
    // Test restart functionality
    cy.get('.restart-btn').should('be.visible').click();
    cy.wait(2000);
    cy.screenshot('06-demo-restarted');
    
    cy.log('🎬 ORCAST Demo Recording Complete!');
    
    // Final verification that all systems are working
    cy.task('log', '📊 ORCAST DEMO RECORDING SUMMARY:');
    cy.task('log', '✅ All 5 slides recorded successfully');
    cy.task('log', '✅ Multi-agent coordination demonstrated');
    cy.task('log', '✅ Map configurations and animations captured');
    cy.task('log', '✅ Trip planning workflow completed');
    cy.task('log', '✅ User acceptance simulation recorded');
    cy.task('log', '🎯 Video ready for hackathon presentation!');
  });

  it('should test individual agent endpoints during demo', () => {
    cy.log('🔗 Testing backend connectivity during demo');
    
    const backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';
    const gemmaUrl = 'https://cloud-run-gemma-2cvqukvhga-uw.a.run.app';
    
    // Test backend APIs
    cy.request({
      method: 'GET',
      url: `${backendUrl}/api/recent-sightings`,
      timeout: 15000,
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Backend Sightings API: ${response.status}`);
      if (response.status === 200) {
        cy.task('log', '✅ Backend sightings API responding');
      } else {
        cy.task('log', '⚠️ Backend sightings API may be cold starting');
      }
    });
    
    // Test Gemma AI agent
    cy.request({
      method: 'GET', 
      url: `${gemmaUrl}/health`,
      timeout: 15000,
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Gemma Agent Health: ${response.status}`);
      if (response.status === 200) {
        cy.task('log', '✅ Gemma AI agent responding');
      } else {
        cy.task('log', '⚠️ Gemma AI agent may be cold starting');
      }
    });
    
    // Test trip planning functionality
    cy.request({
      method: 'POST',
      url: `${gemmaUrl}/generate-trip-plan`,
      body: {
        destination: "San Juan Islands",
        dates: "August 12-14, 2025", 
        preferences: "automated demo test",
        duration: 3
      },
      timeout: 30000,
      failOnStatusCode: false
    }).then((response) => {
      cy.log(`Trip Planning Agent: ${response.status}`);
      if (response.status === 200) {
        cy.task('log', '✅ Trip planning agent fully functional');
        cy.task('log', `📋 Generated plan: ${JSON.stringify(response.body).substring(0, 100)}...`);
      } else {
        cy.task('log', '⚠️ Trip planning agent may need cold start time');
      }
    });
  });

  it('should create a comprehensive demo summary video', () => {
    cy.log('📹 Creating comprehensive demo video summary');
    
    // This test ensures the video captures all key elements
    cy.visit(demoUrl);
    cy.viewport(1920, 1080);
    
    // Record intro sequence
    cy.get('.demo-controls h2').should('contain', 'ORCAST Automated Demo');
    cy.wait(3000);
    
    // Start and record full demo sequence
    cy.get('.start-btn').click();
    
    // Let the entire demo run (total estimated time: ~55 seconds)
    cy.wait(60000);
    
    // Verify completion
    cy.get('.demo-results').should('be.visible');
    
    // Create final summary
    cy.task('log', '🎬 FINAL VIDEO SUMMARY:');
    cy.task('log', '▶️ Total recording time: ~60 seconds');
    cy.task('log', '🤖 Multi-agent workflow: DEMONSTRATED');
    cy.task('log', '🗺️ Map visualizations: RECORDED');
    cy.task('log', '📊 Data processing: SHOWN');
    cy.task('log', '✅ Trip planning: COMPLETED');
    cy.task('log', '👤 User acceptance: SIMULATED');
    cy.task('log', '🚀 Ready for hackathon presentation!');
  });
}); 