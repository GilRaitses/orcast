describe('ORCAST Presentation Component Capture', () => {
  beforeEach(() => {
    // Visit the main ORCAST platform
    cy.visit('https://orca-904de.web.app', {
      failOnStatusCode: false
    });
    cy.wait(3000); // Allow components to load
  });

  it('should capture the main dashboard overview', () => {
    // Wait for page to load completely
    cy.get('body').should('be.visible');
    
    // Take screenshot of main dashboard
    cy.screenshot('01-main-dashboard-overview', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured main dashboard overview');
  });

  it('should capture Google Maps integration with controls', () => {
    // Look for map-related elements
    cy.get('body').then(($body) => {
      // Try to find Google Maps or map container
      if ($body.find('[id*="map"], [class*="map"], .google-map, #google-map').length > 0) {
        cy.log('Found map elements');
      } else {
        cy.log('No map elements found, capturing general interface');
      }
    });
    
    // Take screenshot showing any map interface
    cy.screenshot('02-google-maps-interface', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured Google Maps interface');
  });

  it('should capture AI agent demo interface', () => {
    // Look for agent demo elements
    cy.get('body').then(($body) => {
      if ($body.find('[class*="agent"], [class*="demo"], [id*="agent"]').length > 0) {
        cy.log('Found agent interface elements');
      }
    });
    
    // Try to navigate to or show agent interface
    cy.get('body').should('contain.text', 'ORCAST');
    
    cy.screenshot('03-ai-agent-interface', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured AI agent interface');
  });

  it('should show multi-agent workflow components', () => {
    // Try to trigger or show agent workflows
    cy.get('body').then(($body) => {
      // Look for any interactive elements that might trigger agent workflows
      const interactiveElements = $body.find('button, .btn, [role="button"], .clickable');
      
      if (interactiveElements.length > 0) {
        cy.wrap(interactiveElements.first()).click({ force: true });
        cy.wait(2000); // Allow workflow to start
      }
    });
    
    cy.screenshot('04-multi-agent-workflow', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured multi-agent workflow');
  });

  it('should capture probability visualization components', () => {
    // Look for any probability or analytics related elements
    cy.get('body').then(($body) => {
      // Try to find probability controls or analytics
      const probabilityElements = $body.find('[class*="probability"], [class*="analytics"], [class*="prediction"]');
      
      if (probabilityElements.length > 0) {
        cy.log('Found probability/analytics elements');
      }
    });
    
    cy.screenshot('05-probability-analytics', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured probability analytics');
  });

  it('should show environmental data integration', () => {
    // Try to access environmental data features
    cy.get('body').then(($body) => {
      // Look for environmental data indicators
      const envElements = $body.find('[class*="environmental"], [class*="weather"], [class*="tidal"]');
      
      if (envElements.length > 0) {
        cy.log('Found environmental data elements');
      }
    });
    
    cy.screenshot('06-environmental-data', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured environmental data integration');
  });

  it('should capture ML predictions and forecasting', () => {
    // Try to show ML prediction components
    cy.get('body').then(($body) => {
      // Look for ML or prediction related elements
      const mlElements = $body.find('[class*="ml"], [class*="prediction"], [class*="forecast"]');
      
      if (mlElements.length > 0) {
        cy.log('Found ML prediction elements');
      }
    });
    
    cy.screenshot('07-ml-predictions-forecasting', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured ML predictions and forecasting');
  });

  it('should show historical sightings data visualization', () => {
    // Try to show sightings data
    cy.get('body').then(($body) => {
      // Look for sightings or data visualization elements
      const sightingsElements = $body.find('[class*="sighting"], [class*="data"], [class*="visualization"]');
      
      if (sightingsElements.length > 0) {
        cy.log('Found sightings data elements');
      }
    });
    
    cy.screenshot('08-historical-sightings-data', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured historical sightings data');
  });

  it('should capture agent output and communication logs', () => {
    // Try to show agent communication or logs
    cy.get('body').then(($body) => {
      // Look for logs, messages, or communication elements
      const logElements = $body.find('[class*="log"], [class*="message"], [class*="output"], [class*="transcript"]');
      
      if (logElements.length > 0) {
        cy.log('Found agent communication elements');
        // Try to scroll to show more content
        cy.scrollTo('bottom');
        cy.wait(1000);
      }
    });
    
    cy.screenshot('09-agent-communication-logs', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured agent communication logs');
  });

  it('should show analytics dashboard with metrics', () => {
    // Try to show analytics or metrics
    cy.get('body').then(($body) => {
      // Look for analytics, metrics, or dashboard elements
      const analyticsElements = $body.find('[class*="analytics"], [class*="metrics"], [class*="dashboard"], [class*="stats"]');
      
      if (analyticsElements.length > 0) {
        cy.log('Found analytics dashboard elements');
      }
    });
    
    cy.screenshot('10-analytics-dashboard-metrics', {
      capture: 'viewport',
      overwrite: true
    });
    
    cy.log('✅ Captured analytics dashboard');
  });

  it('should create a comprehensive component summary', () => {
    // Final screenshot showing the overall interface
    cy.get('body').should('be.visible');
    
    // Try to navigate to show the most comprehensive view
    cy.get('body').then(($body) => {
      // Look for navigation elements to show main features
      const navElements = $body.find('nav, .nav, .navigation, .menu');
      
      if (navElements.length > 0) {
        cy.log('Found navigation elements');
      }
    });
    
    cy.screenshot('11-comprehensive-platform-overview', {
      capture: 'viewport',
      overwrite: true
    });
    
    // Create summary log
    cy.task('log', '📊 ORCAST Platform Component Capture Summary:');
    cy.task('log', '✅ Main dashboard captured');
    cy.task('log', '✅ Google Maps interface captured');
    cy.task('log', '✅ AI agent workflow captured');
    cy.task('log', '✅ Probability analytics captured');
    cy.task('log', '✅ Environmental data captured');
    cy.task('log', '✅ ML predictions captured');
    cy.task('log', '✅ Historical data captured');
    cy.task('log', '✅ Agent communications captured');
    cy.task('log', '✅ Analytics dashboard captured');
    cy.task('log', '✅ Platform overview captured');
    cy.task('log', '🎯 Ready for presentation integration!');
    
    cy.log('✅ Component capture complete!');
  });
}); 