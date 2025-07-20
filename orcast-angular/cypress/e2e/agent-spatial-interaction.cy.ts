describe('ORCAST Agent Spatial Demo - Comprehensive Testing', () => {
  const backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';

  beforeEach(() => {
    cy.visit('/agent-spatial-demo');
    cy.viewport(1400, 900);
  });

  describe('1. Page Loading & Interface Elements', () => {
    it('should load the agent spatial demo page successfully', () => {
      cy.get('orcast-agent-spatial-demo').should('exist');
      cy.contains('ORCAST Agent-Driven Spatial Planning').should('be.visible');
      cy.contains('Multi-Agent Orchestration for Whale Research & Trip Planning').should('be.visible');
    });

    it('should display all demo control buttons', () => {
      cy.get('.demo-controls').should('be.visible');
      cy.contains('🤖 Start Agent Orchestration').should('be.visible');
      cy.contains('🗺️ Generate Map Configuration').should('be.visible');  
      cy.contains('🧹 Clear Logs').should('be.visible');
    });

    it('should display all three main panels', () => {
      cy.get('.agent-panel').should('be.visible');
      cy.get('.map-config-panel').should('be.visible');
      cy.get('.forecast-panel').should('be.visible');
    });
  });

  describe('2. Agent Chat Interface', () => {
    beforeEach(() => {
      // Open the agent chat interface
      cy.contains('🔼 Show Agent Chat').click();
      cy.get('.agent-chat-interface').should('be.visible');
    });

    it('should display all 5 specialized agents', () => {
      const expectedAgents = [
        { name: 'Primary Planning Agent', icon: '🎯' },
        { name: 'Analytics Agent', icon: '📊' },
        { name: 'Spatial Forecast Agent', icon: '🗺️' },
        { name: 'Whale Research Agent', icon: '🐋' },
        { name: 'Environmental Agent', icon: '🌊' }
      ];

      expectedAgents.forEach(agent => {
        cy.get('.agent-tabs').contains(agent.icon).should('be.visible');
        cy.get('.agent-tabs').contains(agent.name).should('be.visible');
      });
    });

    it('should allow selection of different agents', () => {
      // Test selecting Analytics Agent
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      cy.get('.agent-tab.active').should('contain', 'Analytics Agent');
      
      // Verify agent details update
      cy.get('.current-agent-info').should('contain', 'Analytics Agent');
      cy.get('.agent-description').should('contain', 'whale sighting statistics');
      
      // Test selecting Spatial Forecast Agent
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.agent-tab.active').should('contain', 'Spatial Forecast Agent');
      cy.get('.current-agent-info').should('contain', 'Spatial Forecast Agent');
    });

    it('should display agent capabilities correctly', () => {
      // Select Primary Planning Agent
      cy.get('.agent-tab').contains('🎯 Primary Planning Agent').click();
      
      // Check capabilities
      cy.get('.capability-tag').should('contain', 'Trip Planning');
      cy.get('.capability-tag').should('contain', 'Coordination');
      cy.get('.capability-tag').should('contain', 'Route Optimization');
    });

    it('should show appropriate quick prompts for each agent', () => {
      // Test Analytics Agent quick prompts
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      cy.get('.quick-prompt-btn').should('contain', 'Historical Data');
      cy.get('.quick-prompt-btn').should('contain', 'Success Rates');
      cy.get('.quick-prompt-btn').should('contain', 'Seasonal Patterns');

      // Test Spatial Forecast Agent quick prompts
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.quick-prompt-btn').should('contain', 'Generate Forecasts');
      cy.get('.quick-prompt-btn').should('contain', 'Behavior Prediction');
      cy.get('.quick-prompt-btn').should('contain', 'Probability Maps');
    });

    it('should allow sending prompts to agents', () => {
      // Select Spatial Forecast Agent
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      
      // Type a custom prompt
      const testPrompt = 'Generate spatial forecasts for the next 24 hours in the San Juan Islands';
      cy.get('.prompt-textarea').type(testPrompt);
      
      // Verify character count updates
      cy.get('.char-count').should('contain', testPrompt.length.toString());
      
      // Send the prompt
      cy.get('.send-prompt-btn').click();
      
      // Verify the prompt appears in agent messages
      cy.get('.agent-messages').should('contain', testPrompt);
      cy.get('.agent-messages').should('contain', '👤 User');
      
      // Verify agent response appears
      cy.get('.agent-messages', { timeout: 10000 }).should('contain', '🗺️ Spatial Forecast Agent');
    });

    it('should populate prompt from quick prompt buttons', () => {
      // Select Analytics Agent
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      
      // Click a quick prompt
      cy.get('.quick-prompt-btn').contains('Historical Data').click();
      
      // Verify prompt textarea is populated
      cy.get('.prompt-textarea').should('contain.value', 'whale sighting statistics');
    });

    it('should support keyboard shortcuts', () => {
      // Type a prompt
      cy.get('.prompt-textarea').type('Test keyboard shortcut');
      
      // Use Ctrl+Enter to send
      cy.get('.prompt-textarea').type('{ctrl}{enter}');
      
      // Verify prompt was sent
      cy.get('.agent-messages').should('contain', 'Test keyboard shortcut');
    });
  });

  describe('3. Agent Orchestration & Map Generation', () => {
    it('should start agent demo and show agent activity', () => {
      // Start the demo
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      
      // Verify demo is running
      cy.get('.agent-status').should('contain', 'Agents Active');
      
      // Verify agent messages start appearing
      cy.get('.agent-messages .message', { timeout: 10000 }).should('have.length.greaterThan', 0);
      
      // Check for specific agent types
      cy.get('.agent-messages').should('contain', 'Spatial Forecast Agent');
    });

    it('should generate map configuration with real data', () => {
      // Generate map config
      cy.get('button').contains('🗺️ Generate Map Configuration').click();
      
      // Verify map config panel updates
      cy.get('.config-status').should('contain', 'Generated by: ORCAST Spatial Planning Agent');
      
      // Verify forecast overlay appears
      cy.get('.config-overlay').should('be.visible');
      cy.get('.config-overlay').should('contain', 'Forecast Overview');
      cy.get('.config-overlay').should('contain', 'whale behavior probability');
    });

    it('should display spatial forecasts with real API data', () => {
      // Trigger spatial forecast generation
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.quick-prompt-btn').contains('Generate Forecasts').click();
      cy.get('.send-prompt-btn').click();
      
      // Wait for forecasts to appear
      cy.get('.forecast-list .forecast-item', { timeout: 15000 }).should('have.length.greaterThan', 0);
      
      // Verify forecast contains expected data
      cy.get('.forecast-item').first().within(() => {
        cy.get('.behavior').should('be.visible');
        cy.get('.probability').should('contain', '%');
        cy.get('.location').should('contain', '📍');
        cy.get('.model-info').should('contain', 'Model:');
      });
    });

    it('should show data source verification', () => {
      // Generate some data
      cy.get('button').contains('🗺️ Generate Map Configuration').click();
      
      // Check data source verification panel
      cy.get('.data-source-verification').should('be.visible');
      cy.get('.data-source-verification').should('contain', 'Data Source Verification');
      cy.get('.source-item').should('have.length.greaterThan', 0);
      
      // Verify verification status indicators
      cy.get('.verified').should('be.visible');
    });
  });

  describe('4. Map Interaction & Heat Layers', () => {
    it('should toggle forecast overlay visibility', () => {
      // Generate map config first
      cy.get('button').contains('🗺️ Generate Map Configuration').click();
      
      // Verify overlay is visible initially
      cy.get('.config-overlay').should('be.visible');
      
      // Toggle overlay off
      cy.get('.toggle-overlay-btn').click();
      
      // Verify overlay is hidden
      cy.get('.config-overlay').should('not.exist');
      
      // Toggle overlay back on
      cy.get('.toggle-overlay-btn').click();
      cy.get('.config-overlay').should('be.visible');
    });

    it('should display heatmap canvas for probability visualization', () => {
      // Start demo to generate some forecasts
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      
      // Verify heatmap canvas exists
      cy.get('.heatmap-overlay').should('exist');
      cy.get('canvas[width="800"][height="600"]').should('exist');
    });

    it('should allow layer control interactions', () => {
      // Generate map config
      cy.get('button').contains('🗺️ Generate Map Configuration').click();
      
      // Check if layer controls exist
      cy.get('.layer-controls').should('be.visible');
      
      // Test layer toggles if available
      cy.get('.layer-control input[type="checkbox"]').then($checkboxes => {
        if ($checkboxes.length > 0) {
          cy.wrap($checkboxes.first()).click();
        }
      });
    });
  });

  describe('5. Real Backend API Integration', () => {
    it('should call real ML prediction API', () => {
      // Intercept the backend API call
      cy.intercept('POST', `${backendUrl}/forecast/quick`).as('mlPrediction');
      
      // Trigger API call through spatial agent
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.quick-prompt-btn').contains('Generate Forecasts').click();
      cy.get('.send-prompt-btn').click();
      
      // Verify API call was made
      cy.wait('@mlPrediction', { timeout: 20000 }).then((interception) => {
        expect(interception.request.body).to.have.property('lat');
        expect(interception.request.body).to.have.property('lng');
        expect(interception.request.body).to.have.property('model');
      });
    });

    it('should handle API errors gracefully', () => {
      // Mock API failure
      cy.intercept('POST', `${backendUrl}/forecast/quick`, { 
        statusCode: 500, 
        body: { error: 'API Error' }
      }).as('mlPredictionError');
      
      // Trigger API call
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.quick-prompt-btn').contains('Generate Forecasts').click();
      cy.get('.send-prompt-btn').click();
      
      // Verify fallback behavior
      cy.get('.agent-messages').should('contain', 'API call failed');
      cy.get('.agent-messages').should('contain', 'falling back to demo data');
    });
  });

  describe('6. Performance & Accessibility', () => {
    it('should load within reasonable time', () => {
      const startTime = Date.now();
      
      cy.get('orcast-agent-spatial-demo').should('be.visible').then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(5000); // 5 seconds max
      });
    });

    it('should be keyboard accessible', () => {
      // Test tab navigation through agent tabs
      cy.get('.agent-tab').first().focus();
      cy.focused().should('have.class', 'agent-tab');
      
      // Test Enter key on agent selection
      cy.focused().type('{enter}');
      cy.get('.agent-tab.active').should('exist');
    });

    it('should handle rapid interactions without errors', () => {
      // Rapidly click between agents
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.agent-tab').contains('🐋 Whale Research Agent').click();
      cy.get('.agent-tab').contains('🌊 Environmental Agent').click();
      
      // Verify no JavaScript errors
      cy.window().then((win) => {
        expect(win.console.error).to.not.have.been.called;
      });
    });
  });

  describe('7. Agent Message Logging & Communication', () => {
    it('should log agent messages with proper formatting', () => {
      // Start demo
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      
      // Wait for messages to appear
      cy.get('.message', { timeout: 10000 }).should('have.length.greaterThan', 0);
      
      // Verify message structure
      cy.get('.message').first().within(() => {
        cy.get('.message-header').should('be.visible');
        cy.get('.agent-name').should('be.visible');
        cy.get('.timestamp').should('be.visible');
        cy.get('.message-content').should('be.visible');
      });
    });

    it('should clear logs when requested', () => {
      // Generate some messages first
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      cy.get('.message', { timeout: 5000 }).should('have.length.greaterThan', 0);
      
      // Clear logs
      cy.get('button').contains('🧹 Clear Logs').click();
      
      // Verify logs are cleared
      cy.get('.message').should('have.length', 0);
    });

    it('should auto-scroll to latest messages', () => {
      // Start demo to generate messages
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      
      // Wait for multiple messages
      cy.get('.message', { timeout: 10000 }).should('have.length.greaterThan', 3);
      
      // Verify scroll behavior (last message should be visible)
      cy.get('.message').last().should('be.visible');
    });
  });
}); 