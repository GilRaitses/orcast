describe('orcast navigation', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  describe('Landing page', () => {
    it('shows the orcast hero and primary CTA to the report page', () => {
      cy.contains('h1', 'orcast').should('be.visible')
      cy.contains('.btn', "See this week's map")
        .should('have.attr', 'href')
        .and('include', '/reports')
    })

    it('shows the field pilot banner', () => {
      cy.get('.pilot-banner').should('contain', 'Field pilot')
    })

    it('presents the live guided steps', () => {
      cy.get('.steps .step-card').should('have.length', 3)
      cy.contains('.step-card', 'Probability report').should('be.visible')
      cy.contains('.step-card', 'Historical sightings').should('be.visible')
      cy.contains('.step-card', 'Probability map').should('be.visible')
      cy.get('.badge--live').should('exist')
      cy.get('.badge--historical').should('exist')
    })

    it('links to the partners page', () => {
      cy.contains('.btn', 'Partner with us')
        .should('have.attr', 'href')
        .and('include', '/partners')
    })
  })

  describe('Top navigation bar', () => {
    it('exposes the five expected nav links', () => {
      cy.get('orcast-nav-header').should('be.visible')
      cy.get('.nav-btn').should('have.length', 5)
      cy.contains('.nav-btn', 'Home').should('be.visible')
      cy.contains('.nav-btn', 'Reports').should('be.visible')
      cy.contains('.nav-btn', 'Historical').should('be.visible')
      cy.contains('.nav-btn', 'Recent').should('be.visible')
      cy.contains('.nav-btn', 'Score grid').should('be.visible')
    })

    it('routes to Historical and marks it active', () => {
      cy.contains('.nav-btn', 'Historical').click()
      cy.url().should('include', '/historical')
      cy.contains('h3', 'Historical sightings').should('be.visible')
      cy.contains('.nav-btn', 'Historical').should('have.class', 'active')
    })

    it('routes to Recent and marks it active', () => {
      cy.contains('.nav-btn', 'Recent').click()
      cy.url().should('include', '/realtime')
      cy.contains('h3', 'Recent sightings').should('be.visible')
      cy.contains('.nav-btn', 'Recent').should('have.class', 'active')
    })

    it('routes to the Score grid (probability map) and marks it active', () => {
      cy.contains('.nav-btn', 'Score grid').click()
      cy.url().should('include', '/ml-predictions')
      cy.contains('h3', 'Probability map').should('be.visible')
      cy.contains('.nav-btn', 'Score grid').should('have.class', 'active')
    })
  })

  describe('Responsive design', () => {
    it('renders the hero on a mobile viewport', () => {
      cy.viewport('iphone-x')
      cy.visit('/')
      cy.contains('h1', 'orcast').should('be.visible')
      cy.get('.steps .step-card').should('have.length', 3)
    })

    it('renders the hero on a tablet viewport', () => {
      cy.viewport('ipad-2')
      cy.visit('/')
      cy.contains('h1', 'orcast').should('be.visible')
      cy.get('.nav-btn').should('have.length', 5)
    })
  })

  describe('Error handling', () => {
    it('redirects unknown routes to the landing page', () => {
      cy.visit('/invalid-route', { failOnStatusCode: false })
      cy.url().should('match', /\/$/)
      cy.contains('h1', 'orcast').should('be.visible')
    })
  })
})
