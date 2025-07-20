describe('ORCAST Navigation and Dashboard', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  describe('Dashboard Page', () => {
    it('should display ORCAST dashboard with map cards', () => {
      // Check main heading
      cy.contains('h1', 'ORCAST').should('be.visible')
      cy.contains('Multi-Agent Whale Research Platform').should('be.visible')

      // Check all map cards are present
      cy.get('.map-card').should('have.length', 3)
      
      // Verify each map card
      cy.contains('.map-card', 'Historical Sightings').should('be.visible')
      cy.contains('.map-card', 'Real-time Detection').should('be.visible')
      cy.contains('.map-card', 'ML Predictions').should('be.visible')
    })

    it('should have working launch buttons for each map type', () => {
      // Test Historical Sightings navigation
      cy.contains('.map-card', 'Historical Sightings')
        .find('.launch-btn')
        .should('contain', 'Launch Historical Sightings View')

      // Test Real-time Detection navigation
      cy.contains('.map-card', 'Real-time Detection')
        .find('.launch-btn')
        .should('contain', 'Launch Real-time Detection View')

      // Test ML Predictions navigation
      cy.contains('.map-card', 'ML Predictions')
        .find('.launch-btn')
        .should('contain', 'Launch ML Predictions View')
    })

    it('should display system health information', () => {
      // Wait for health check to complete
      cy.get('.system-status', { timeout: 10000 }).should('be.visible')
      
      // Check health items
      cy.get('.health-item').should('have.length.at.least', 3)
      cy.contains('.health-item', 'Backend API').should('be.visible')
      cy.contains('.health-item', 'Redis Cache').should('be.visible')
      cy.contains('.health-item', 'ML Models').should('be.visible')
    })

    it('should have working footer links', () => {
      cy.get('.footer').should('be.visible')
      cy.get('.footer a').should('have.length.at.least', 2)
    })
  })

  describe('Navigation Between Map Types', () => {
    it('should navigate to Historical Sightings page', () => {
      cy.contains('.map-card', 'Historical Sightings').click()
      cy.url().should('include', '/historical')
      cy.get('orcast-nav-header').should('be.visible')
      cy.contains('📊 Historical Sightings').should('be.visible')
    })

    it('should navigate to Real-time Detection page', () => {
      cy.contains('.map-card', 'Real-time Detection').click()
      cy.url().should('include', '/realtime')
      cy.get('orcast-nav-header').should('be.visible')
      cy.contains('🎧 Live Hydrophones').should('be.visible')
    })

    it('should navigate to ML Predictions page', () => {
      cy.contains('.map-card', 'ML Predictions').click()
      cy.url().should('include', '/ml-predictions')
      cy.get('orcast-nav-header').should('be.visible')
      cy.contains('🧠 ML Prediction Models').should('be.visible')
    })
  })

  describe('Navigation Header', () => {
    beforeEach(() => {
      // Navigate to any map page to test navigation header
      cy.contains('.map-card', 'Historical Sightings').click()
    })

    it('should display navigation header on map pages', () => {
      cy.get('orcast-nav-header').should('be.visible')
      cy.get('.nav-btn').should('have.length', 4)
    })

    it('should navigate between map types using header', () => {
      // Test navigation to each page
      cy.get('.nav-btn').contains('Real-time').click()
      cy.url().should('include', '/realtime')
      
      cy.get('.nav-btn').contains('ML Predictions').click()
      cy.url().should('include', '/ml-predictions')
      
      cy.get('.nav-btn').contains('Historical').click()
      cy.url().should('include', '/historical')
      
      cy.get('.nav-btn').contains('Dashboard').click()
      cy.url().should('match', /\/$/)
    })

    it('should highlight active navigation item', () => {
      cy.url().should('include', '/historical')
      cy.get('.nav-btn').contains('Historical').should('have.class', 'active')
      
      cy.get('.nav-btn').contains('Real-time').click()
      cy.get('.nav-btn').contains('Real-time').should('have.class', 'active')
      cy.get('.nav-btn').contains('Historical').should('not.have.class', 'active')
    })
  })

  describe('Responsive Design', () => {
    it('should work on mobile viewport', () => {
      cy.viewport('iphone-x')
      cy.visit('/')
      
      cy.get('.map-grid').should('be.visible')
      cy.get('.map-card').should('be.visible')
    })

    it('should work on tablet viewport', () => {
      cy.viewport('ipad-2')
      cy.visit('/')
      
      cy.get('.map-grid').should('be.visible')
      cy.get('.map-card').should('have.length', 3)
    })
  })

  describe('Error Handling', () => {
    it('should handle invalid routes gracefully', () => {
      cy.visit('/invalid-route', { failOnStatusCode: false })
      cy.url().should('match', /\/$/) // Should redirect to dashboard
    })
  })
}) 