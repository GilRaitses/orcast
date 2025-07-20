describe('ORCAST Live AI Demo Recording', () => {
  const demoUrl = 'https://orca-904de.web.app';
  
  beforeEach(() => {
    // Optimal video recording settings
    cy.viewport(1920, 1080);
  });

  it('should record the live AI spatial analysis demo', () => {
    cy.log('🎬 Recording Live ORCAST AI Demo');
    
    // Visit the live demo
    cy.visit(demoUrl);
    cy.wait(3000); // Let page load
    
    // Verify the live demo interface is loaded
    cy.get('.live-demo-container').should('be.visible');
    cy.get('.header-bar h1').should('contain', 'ORCAST');
    cy.get('.subtitle').should('contain', 'Live AI Spatial Analysis Demo');
    
    // Take initial screenshot
    cy.screenshot('01-live-demo-ready');
    
    // Verify map centerpiece is visible
    cy.get('.map-centerpiece').should('be.visible');
    cy.get('#live-map').should('be.visible');
    cy.get('.agent-sidebar').should('be.visible');
    cy.get('.analysis-panel').should('be.visible');
    
    cy.screenshot('02-interface-layout');
    
    // Start the live demo
    cy.get('.start-btn').should('be.visible').should('contain', 'Start Live AI Demo');
    cy.get('.start-btn').click();
    
    // Wait for demo to start
    cy.get('.status.running').should('be.visible');
    cy.get('.status.running').should('contain', 'AI Agents Active');
    
    cy.screenshot('03-demo-started');
    
    // Let agents run and generate messages
    cy.wait(5000);
    cy.screenshot('04-agent-messages-appearing');
    
    // Verify agent messages are appearing
    cy.get('.message').should('have.length.at.least', 3);
    cy.get('.agent-transcript').should('be.visible');
    
    // Check different map modes
    cy.get('.map-mode-btn').contains('ML Predictions').click();
    cy.wait(2000);
    cy.screenshot('05-ml-predictions-mode');
    
    cy.get('.map-mode-btn').contains('Probability Heatmap').click();
    cy.wait(2000);
    cy.screenshot('06-heatmap-mode');
    
    cy.get('.map-mode-btn').contains('Live Detections').click();
    cy.wait(2000);
    cy.screenshot('07-detections-mode');
    
    // Let the demo run for full coordination
    cy.wait(15000);
    
    // Verify ML predictions are appearing
    cy.get('.prediction-card').should('be.visible');
    cy.get('.prediction-card .probability').should('be.visible');
    
    cy.screenshot('08-ml-predictions-active');
    
    // Verify pattern recognition
    cy.get('.pattern-item').should('have.length.at.least', 2);
    cy.get('.pattern-strength').should('be.visible');
    
    // Verify environmental data
    cy.get('.env-factors .factor').should('have.length', 4);
    
    // Verify model performance metrics
    cy.get('.performance-metrics .metric').should('have.length.at.least', 3);
    
    cy.screenshot('09-full-analysis-active');
    
    // Let it run for longer to show coordination
    cy.wait(20000);
    
    // Final screenshot with all systems active
    cy.screenshot('10-live-demo-complete');
    
    // Stop the demo
    cy.get('.stop-btn').click();
    cy.get('.status').should('not.have.class', 'running');
    
    cy.screenshot('11-demo-stopped');
    
    cy.log('✅ Live AI Demo Recording Complete!');
    cy.log('📊 Captured: Map-centered interface, Agent coordination, ML predictions, Real-time analysis');
  });

  it('should verify all key components are functional', () => {
    cy.visit(demoUrl);
    cy.viewport(1920, 1080);
    
    // Verify layout matches original design intent
    cy.get('.main-interface').should('have.css', 'display', 'grid');
    cy.get('.main-interface').should('have.css', 'grid-template-columns');
    
    // Verify map is centerpiece
    cy.get('.map-centerpiece').should('be.visible');
    cy.get('#live-map').should('be.visible');
    
    // Verify agent sidebar for transcripts
    cy.get('.agent-sidebar').should('be.visible');
    cy.get('.agent-transcript').should('be.visible');
    
    // Verify analysis panel
    cy.get('.analysis-panel').should('be.visible');
    cy.get('.analysis-sections').should('be.visible');
    
    // Start demo and verify functionality
    cy.get('.start-btn').click();
    cy.wait(8000);
    
    // Verify agents are generating messages
    cy.get('.message').should('have.length.at.least', 5);
    
    // Verify map modes work
    cy.get('.map-mode-btn').should('have.length', 4);
    cy.get('.map-mode-btn').each(($btn) => {
      cy.wrap($btn).click();
      cy.wait(1000);
    });
    
    // Verify ML models are active
    cy.get('.ml-model').should('have.length', 3);
    cy.get('.model-status.status-active').should('have.length', 3);
    
    cy.log('✅ All components verified functional');
  });
}); 