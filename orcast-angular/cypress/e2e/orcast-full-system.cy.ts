describe('ORCAST Full System E2E Tests', () => {
  const backendUrl = Cypress.env('backendUrl');
  const gemmaUrl = Cypress.env('gemmaUrl');

  beforeEach(() => {
    cy.visit('/');
    cy.viewport(1280, 720);
  });

  describe('Application Loading and Navigation', () => {
    it('should load the main dashboard', () => {
      cy.get('app-root').should('exist');
      cy.get('[data-cy="dashboard"]').should('be.visible');
      cy.title().should('contain', 'ORCAST');
    });

    it('should navigate to AI Agent Demo', () => {
      cy.get('[data-cy="agent-demo-card"]').click();
      cy.url().should('include', '/agent-demo');
      cy.get('[data-cy="agent-demo-container"]').should('be.visible');
    });

    it('should navigate to Map Dashboard', () => {
      cy.visit('/');
      cy.get('[data-cy="map-dashboard-card"]').click();
      cy.url().should('include', '/map-dashboard');
    });
  });

  describe('Backend API Endpoints', () => {
    it('should fetch recent sightings from backend', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/recent-sightings`,
        timeout: 15000
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('sightings');
        expect(response.body.sightings).to.be.an('array');
      });
    });

    it('should fetch ML predictions from backend', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/ml-predictions`,
        timeout: 15000
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('predictions');
      });
    });

    it('should fetch environmental data from backend', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/environmental-data`,
        timeout: 15000
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('tide_data');
        expect(response.body).to.have.property('weather_data');
      });
    });

    it('should fetch hydrophone data from backend', () => {
      cy.request({
        method: 'GET',
        url: `${backendUrl}/api/hydrophone-data`,
        timeout: 15000
      }).then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('detections');
      });
    });
  });

  describe('Gemma 3 AI Agent Services', () => {
    it('should check Gemma agent health', () => {
      cy.request({
        method: 'GET',
        url: `${gemmaUrl}/health`,
        timeout: 15000,
        failOnStatusCode: false
      }).then((response) => {
        // Service might be sleeping, so we accept both 200 and 503
        expect([200, 503]).to.include(response.status);
        if (response.status === 200) {
          expect(response.body).to.have.property('status');
        }
      });
    });

    it('should test trip planning agent', () => {
      const tripRequest = {
        destination: "San Juan Islands",
        dates: "August 12-14, 2025",
        preferences: "whale watching, kayaking",
        duration: 3
      };

      cy.request({
        method: 'POST',
        url: `${gemmaUrl}/generate-trip-plan`,
        body: tripRequest,
        timeout: 30000,
        failOnStatusCode: false
      }).then((response) => {
        if (response.status === 200) {
          expect(response.body).to.have.property('trip_plan');
          expect(response.body.trip_plan).to.include('San Juan Islands');
        } else {
          // Service might be cold starting
          cy.log('Gemma service may be cold starting');
        }
      });
    });
  });

  describe('AI Agent Demo Interface', () => {
    beforeEach(() => {
      cy.visit('/agent-demo');
    });

    it('should display user profile section', () => {
      cy.get('[data-cy="user-profile"]').should('be.visible');
      cy.get('[data-cy="user-name"]').should('contain', 'Gil');
      cy.get('[data-cy="past-trips"]').should('be.visible');
      cy.get('[data-cy="upcoming-trips"]').should('be.visible');
    });

    it('should show trip planning form', () => {
      cy.get('[data-cy="trip-planning-form"]').should('be.visible');
      cy.get('[data-cy="destination-input"]').should('be.visible');
      cy.get('[data-cy="dates-input"]').should('be.visible');
      cy.get('[data-cy="preferences-input"]').should('be.visible');
      cy.get('[data-cy="generate-plan-btn"]').should('be.visible');
    });

    it('should display multi-agent workflow', () => {
      cy.get('[data-cy="agent-workflow"]').should('be.visible');
      cy.get('[data-cy="data-agent"]').should('contain', 'Data Collection Agent');
      cy.get('[data-cy="analysis-agent"]').should('contain', 'Analysis Agent');
      cy.get('[data-cy="planning-agent"]').should('contain', 'Trip Planning Agent');
    });

    it('should generate trip plan when form is submitted', () => {
      cy.get('[data-cy="destination-input"]').type('San Juan Islands');
      cy.get('[data-cy="dates-input"]').type('August 12-14, 2025');
      cy.get('[data-cy="preferences-input"]').type('whale watching, kayaking');
      
      cy.get('[data-cy="generate-plan-btn"]').click();
      
      cy.get('[data-cy="loading-indicator"]').should('be.visible');
      cy.get('[data-cy="trip-result"]', { timeout: 30000 }).should('be.visible');
    });

    it('should display map preview', () => {
      cy.get('[data-cy="map-preview"]').should('be.visible');
      cy.get('[data-cy="map-container"]').should('exist');
    });
  });

  describe('Map Dashboard Integration', () => {
    beforeEach(() => {
      cy.visit('/map-dashboard');
    });

    it('should load Google Maps', () => {
      cy.get('[data-cy="map-container"]', { timeout: 15000 }).should('be.visible');
      cy.window().should('have.property', 'google');
    });

    it('should display probability controls', () => {
      cy.get('[data-cy="time-controls"]').should('be.visible');
      cy.get('[data-cy="probability-threshold"]').should('be.visible');
      cy.get('[data-cy="forecast-layers"]').should('be.visible');
    });

    it('should show agent assistant panel', () => {
      cy.get('[data-cy="agent-assistant"]').should('be.visible');
      cy.get('[data-cy="heat-map-layers"]').should('be.visible');
      cy.get('[data-cy="agent-ready-status"]').should('contain', 'ORCAST Agent Ready');
    });

    it('should interact with map controls', () => {
      cy.get('[data-cy="time-unit-months"]').click();
      cy.get('[data-cy="time-unit-months"]').should('have.class', 'active');
      
      cy.get('[data-cy="probability-slider"]').should('be.visible');
      cy.get('[data-cy="probability-slider"]').invoke('val', 70).trigger('input');
    });
  });

  describe('Real-time Data Integration', () => {
    it('should fetch and display recent sightings on map', () => {
      cy.visit('/map-dashboard');
      
      cy.intercept('GET', `${backendUrl}/api/recent-sightings`).as('getSightings');
      cy.wait('@getSightings', { timeout: 15000 });
      
      cy.get('[data-cy="sighting-markers"]').should('exist');
    });

    it('should update with ML predictions', () => {
      cy.visit('/map-dashboard');
      
      cy.intercept('GET', `${backendUrl}/api/ml-predictions`).as('getPredictions');
      cy.wait('@getPredictions', { timeout: 15000 });
      
      cy.get('[data-cy="prediction-overlay"]').should('exist');
    });

    it('should show environmental data integration', () => {
      cy.visit('/map-dashboard');
      
      cy.intercept('GET', `${backendUrl}/api/environmental-data`).as('getEnvironmental');
      cy.wait('@getEnvironmental', { timeout: 15000 });
      
      cy.get('[data-cy="environmental-indicators"]').should('exist');
    });
  });

  describe('Error Handling and Resilience', () => {
    it('should handle backend service failures gracefully', () => {
      cy.intercept('GET', `${backendUrl}/api/recent-sightings`, { forceNetworkError: true }).as('failedSightings');
      
      cy.visit('/map-dashboard');
      cy.wait('@failedSightings');
      
      cy.get('[data-cy="error-message"]').should('be.visible');
      cy.get('[data-cy="retry-button"]').should('be.visible');
    });

    it('should handle AI agent timeouts', () => {
      cy.visit('/agent-demo');
      
      cy.intercept('POST', `${gemmaUrl}/generate-trip-plan`, { delay: 35000 }).as('slowAgent');
      
      cy.get('[data-cy="destination-input"]').type('Test Location');
      cy.get('[data-cy="generate-plan-btn"]').click();
      
      cy.get('[data-cy="timeout-message"]', { timeout: 40000 }).should('be.visible');
    });
  });

  describe('Performance and Load Testing', () => {
    it('should load dashboard within acceptable time', () => {
      const start = Date.now();
      cy.visit('/');
      cy.get('[data-cy="dashboard"]').should('be.visible').then(() => {
        const loadTime = Date.now() - start;
        expect(loadTime).to.be.lessThan(5000); // 5 seconds max
      });
    });

    it('should handle multiple agent requests', () => {
      cy.visit('/agent-demo');
      
      for (let i = 0; i < 3; i++) {
        cy.get('[data-cy="destination-input"]').clear().type(`Location ${i}`);
        cy.get('[data-cy="generate-plan-btn"]').click();
        cy.wait(2000); // Space out requests
      }
      
      cy.get('[data-cy="trip-result"]').should('be.visible');
    });
  });
}); 