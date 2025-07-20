describe('ORCAST Simple Demo Recording for Hackathon', () => {
  it('should record the complete automated demo workflow', () => {
    // Optimal video recording settings
    cy.viewport(1920, 1080);
    
    // Visit the automated demo page
    cy.visit('https://orca-904de.web.app/automated-demo');
    cy.wait(3000); // Let page load
    
    // Take initial screenshot
    cy.screenshot('demo-ready');
    
    // Start the demo
    cy.get('.start-btn').should('be.visible').click();
    cy.wait(2000);
    
    // Let the entire demo run (estimated 55-60 seconds)
    // This will capture all slides automatically
    cy.wait(65000);
    
    // Take final screenshot
    cy.screenshot('demo-completed');
    
    // The video will show:
    // - System introduction with whale locations
    // - Data collection agent processing
    // - Analysis agent running ML models
    // - Trip planning and route optimization
    // - Final results and user acceptance
    
    cy.log('✅ ORCAST Demo Video Recorded Successfully!');
  });

  it('should capture the slideshow presentation', () => {
    // This test ensures we get the QMD slideshow content
    cy.viewport(1920, 1080);
    
    // Test the main components that would be in slides
    cy.visit('https://orca-904de.web.app');
    cy.screenshot('main-interface');
    
    cy.visit('https://orca-904de.web.app/agent-demo');
    cy.screenshot('agent-demo-interface');
    
    cy.visit('https://orca-904de.web.app/automated-demo');
    cy.screenshot('automated-demo-interface');
    
    cy.log('✅ All key interfaces captured for slideshow');
  });
}); 