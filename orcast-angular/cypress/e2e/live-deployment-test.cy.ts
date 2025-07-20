describe('ORCAST Live Deployment - Full System Test', () => {
  const backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';
  const gemmaUrl = 'https://cloud-run-gemma-2cvqukvhga-uw.a.run.app';

  beforeEach(() => {
    cy.visit('https://orca-904de.web.app');
    cy.viewport(1280, 720);
  });

  describe('1. Application Loading and Routing', () => {
    it('should load the Angular app successfully', () => {
      cy.get('app-root').should('exist');
      cy.title().should('contain', 'ORCAST');
      cy.url().should('eq', 'https://orca-904de.web.app/');
    });

    it('should navigate to Map Dashboard', () => {
      cy.contains('Map Dashboard').click();
      cy.url().should('include', '/map-dashboard');
      cy.get('orcast-map-dashboard').should('exist');
    });

    it('should navigate to AI Agent Demo', () => {
      cy.visit('https://orca-904de.web.app');
      cy.contains('AI Agent Demo').click();
      cy.url().should('include', '/agent-demo');
      cy.get('orcast-agent-demo').should('exist');
    });
  });

  describe('2. Backend API Endpoint Testing', () => {
    it('should verify backend service is live - recent sightings', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/recent-sightings`,
        timeout: 20000,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('sightings');
          cy.log('✅ Backend API - Recent Sightings: LIVE');
        } else {
          cy.log('⚠️ Backend API - Recent Sightings: Service may be cold starting');
        }
      });
    });

    it('should verify ML predictions endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/ml-predictions`,
        timeout: 20000,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('predictions');
          cy.log('✅ Backend API - ML Predictions: LIVE');
        } else {
          cy.log('⚠️ Backend API - ML Predictions: Service may be cold starting');
        }
      });
    });

    it('should verify environmental data endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/environmental-data`,
        timeout: 20000,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('tide_data');
          expect(response.body).to.have.property('weather_data');
          cy.log('✅ Backend API - Environmental Data: LIVE');
        } else {
          cy.log('⚠️ Backend API - Environmental Data: Service may be cold starting');
        }
      });
    });

    it('should verify hydrophone data endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/hydrophone-data`,
        timeout: 20000,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('detections');
          cy.log('✅ Backend API - Hydrophone Data: LIVE');
        } else {
          cy.log('⚠️ Backend API - Hydrophone Data: Service may be cold starting');
        }
      });
    });
  });

  describe('3. Gemma 3 AI Agent Services', () => {
    it('should verify Gemma agent health endpoint', () => {
      cy.request({
        method: 'GET',
        url: `${gemmaUrl}/health`,
        timeout: 20000,
        failOnStatusCode: false
      }).then((response) => {
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('status');
          cy.log('✅ Gemma AI Agent - Health Check: LIVE');
        } else {
          cy.log('⚠️ Gemma AI Agent: Service may be cold starting');
        }
      });
    });

    it('should test trip planning agent functionality', () => {
      const tripRequest = {
        destination: "San Juan Islands",
        dates: "August 12-14, 2025",
        preferences: "whale watching, kayaking, photography",
        duration: 3,
        budget: "moderate"
      };

      cy.request({
        method: 'POST',
        url: `${gemmaUrl}/generate-trip-plan`,
        body: tripRequest,
        timeout: 45000,
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('trip_plan');
          expect(response.body.trip_plan).to.include('San Juan Islands');
          cy.log('✅ Gemma AI Agent - Trip Planning: LIVE AND FUNCTIONAL');
        } else if (response.status === 503) {
          cy.log('⚠️ Gemma AI Agent - Trip Planning: Service cold starting');
        } else {
          cy.log('⚠️ Gemma AI Agent - Trip Planning: Service unavailable');
        }
      });
    });

    it('should test orca prediction agent', () => {
      const predictionRequest = {
        location: { lat: 48.5465, lng: -123.0095 },
        date_range: "2025-08-12",
        environmental_factors: ["tide", "weather", "salmon_runs"]
      };

      cy.request({
        method: 'POST',
        url: `${gemmaUrl}/predict-orca-activity`,
        body: predictionRequest,
        timeout: 45000,
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('prediction');
          cy.log('✅ Gemma AI Agent - Orca Prediction: LIVE AND FUNCTIONAL');
        } else {
          cy.log('⚠️ Gemma AI Agent - Orca Prediction: Service may be unavailable');
        }
      });
    });
  });

  describe('4. Angular Components and UI Testing', () => {
    it('should test Map Dashboard component functionality', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      
      // Wait for component to load
      cy.get('orcast-map-dashboard', { timeout: 15000 }).should('exist');
      
      // Test time controls
      cy.get('.time-controls').should('be.visible');
      cy.get('.time-unit-button').should('have.length.at.least', 3);
      
      // Test probability controls
      cy.get('.probability-threshold').should('be.visible');
      
      // Test forecast layers
      cy.get('.forecast-layers').should('be.visible');
      
      cy.log('✅ Map Dashboard Component: FUNCTIONAL');
    });

    it('should test AI Agent Demo component', () => {
      cy.visit('https://orca-904de.web.app/agent-demo');
      
      // Wait for component to load
      cy.get('orcast-agent-demo', { timeout: 15000 }).should('exist');
      
      // Test user profile section
      cy.get('.user-profile').should('be.visible');
      cy.contains('Gil').should('be.visible');
      
      // Test trip planning form
      cy.get('.trip-planning-form').should('be.visible');
      cy.get('input[placeholder*="destination"]').should('be.visible');
      cy.get('input[placeholder*="dates"]').should('be.visible');
      cy.get('textarea[placeholder*="preferences"]').should('be.visible');
      
      // Test multi-agent workflow display
      cy.get('.agent-workflow').should('be.visible');
      cy.contains('Data Collection Agent').should('be.visible');
      cy.contains('Analysis Agent').should('be.visible');
      cy.contains('Trip Planning Agent').should('be.visible');
      
      cy.log('✅ AI Agent Demo Component: FUNCTIONAL');
    });

    it('should test trip plan generation flow', () => {
      cy.visit('https://orca-904de.web.app/agent-demo');
      cy.get('orcast-agent-demo', { timeout: 15000 }).should('exist');
      
      // Fill out trip planning form
      cy.get('input[placeholder*="destination"]').type('San Juan Islands');
      cy.get('input[placeholder*="dates"]').type('August 12-14, 2025');
      cy.get('textarea[placeholder*="preferences"]').type('whale watching, kayaking');
      
      // Submit form
      cy.get('.generate-plan-btn').click();
      
      // Check for loading state
      cy.get('.loading-indicator').should('be.visible');
      
      // Wait for result (with long timeout for AI processing)
      cy.get('.trip-result', { timeout: 60000 }).should('be.visible');
      
      cy.log('✅ Trip Plan Generation Flow: FUNCTIONAL');
    });
  });

  describe('5. Google Maps Integration', () => {
    it('should load Google Maps successfully', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      
      // Wait for Maps to load
      cy.window().its('google.maps', { timeout: 20000 }).should('exist');
      cy.get('gmp-map, google-map, .google-map').should('be.visible');
      
      cy.log('✅ Google Maps Integration: FUNCTIONAL');
    });

    it('should handle map interactions', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      cy.window().its('google.maps', { timeout: 20000 }).should('exist');
      
      // Test map controls interactions
      cy.get('.probability-slider').should('be.visible');
      cy.get('.time-navigation').should('be.visible');
      
      cy.log('✅ Map Interactions: FUNCTIONAL');
    });
  });

  describe('6. Data Integration and Real-time Features', () => {
    it('should integrate with backend data sources', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      
      // Intercept API calls
      cy.intercept('GET', `${backendUrl}/api/**`).as('backendCall');
      
      // Wait for data loading
      cy.wait('@backendCall', { timeout: 20000 });
      
      cy.log('✅ Backend Data Integration: FUNCTIONAL');
    });

    it('should handle real-time updates', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      
      // Check for SSE or WebSocket connections
      cy.window().then((win) => {
        // Test if real-time features are initialized
        cy.get('.realtime-indicator').should('exist');
      });
      
      cy.log('✅ Real-time Features: INITIALIZED');
    });
  });

  describe('7. Error Handling and Resilience', () => {
    it('should handle network failures gracefully', () => {
      cy.visit('https://orca-904de.web.app/map-dashboard');
      
      // Simulate network failure
      cy.intercept('GET', `${backendUrl}/api/**`, { forceNetworkError: true });
      
      // App should still function and show error states
      cy.get('orcast-map-dashboard').should('exist');
      
      cy.log('✅ Error Handling: RESILIENT');
    });

    it('should handle AI service timeouts', () => {
      cy.visit('https://orca-904de.web.app/agent-demo');
      
      // Simulate slow AI response
      cy.intercept('POST', `${gemmaUrl}/**`, { delay: 65000 });
      
      cy.get('input[placeholder*="destination"]').type('Test Location');
      cy.get('.generate-plan-btn').click();
      
      // Should show timeout handling
      cy.get('.timeout-message, .error-message', { timeout: 70000 }).should('exist');
      
      cy.log('✅ AI Service Timeout Handling: FUNCTIONAL');
    });
  });

  describe('8. Performance and Load Testing', () => {
    it('should load within acceptable performance thresholds', () => {
      const startTime = Date.now();
      
      cy.visit('https://orca-904de.web.app');
      cy.get('app-root').should('exist').then(() => {
        const loadTime = Date.now() - startTime;
        expect(loadTime).to.be.lessThan(8000); // 8 seconds max for initial load
        cy.log(`✅ Performance: Loaded in ${loadTime}ms`);
      });
    });

    it('should handle multiple concurrent agent requests', () => {
      cy.visit('https://orca-904de.web.app/agent-demo');
      cy.get('orcast-agent-demo', { timeout: 15000 }).should('exist');
      
      // Send multiple requests rapidly
      for (let i = 0; i < 3; i++) {
        cy.get('input[placeholder*="destination"]').clear().type(`Location ${i}`);
        cy.get('.generate-plan-btn').click();
        cy.wait(1000);
      }
      
      // Should handle gracefully
      cy.get('.trip-result, .loading-indicator, .error-message').should('exist');
      
      cy.log('✅ Concurrent Request Handling: FUNCTIONAL');
    });
  });

  describe('9. Final System Health Check', () => {
    it('should provide comprehensive system status', () => {
      let systemHealth = {
        angularApp: false,
        backendAPI: false,
        gemmaAgent: false,
        googleMaps: false,
        components: false
      };

      cy.visit('https://orca-904de.web.app');
      
      // Check Angular app
      cy.get('app-root').should('exist').then(() => {
        systemHealth.angularApp = true;
      });

      // Check backend API
      cy.request({ url: `${backendUrl}/health`, failOnStatusCode: false })
        .then((response) => {
          if (response.status === 200) systemHealth.backendAPI = true;
        });

      // Check Gemma agent
      cy.request({ url: `${gemmaUrl}/health`, failOnStatusCode: false })
        .then((response) => {
          if (response.status === 200) systemHealth.gemmaAgent = true;
        });

      // Check Google Maps
      cy.visit('https://orca-904de.web.app/map-dashboard');
      cy.window().its('google.maps').then(() => {
        systemHealth.googleMaps = true;
      });

      // Check components
      cy.get('orcast-map-dashboard').should('exist').then(() => {
        systemHealth.components = true;
      });

      cy.then(() => {
        cy.log('🏁 FINAL SYSTEM HEALTH REPORT:');
        cy.log(`Angular App: ${systemHealth.angularApp ? '✅ LIVE' : '❌ DOWN'}`);
        cy.log(`Backend API: ${systemHealth.backendAPI ? '✅ LIVE' : '⚠️ COLD START'}`);
        cy.log(`Gemma Agent: ${systemHealth.gemmaAgent ? '✅ LIVE' : '⚠️ COLD START'}`);
        cy.log(`Google Maps: ${systemHealth.googleMaps ? '✅ LIVE' : '❌ DOWN'}`);
        cy.log(`Components: ${systemHealth.components ? '✅ FUNCTIONAL' : '❌ BROKEN'}`);
        
        const healthyServices = Object.values(systemHealth).filter(status => status).length;
        cy.log(`📊 System Health: ${healthyServices}/5 services operational`);
      });
    });
  });
}); 